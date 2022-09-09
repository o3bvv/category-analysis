#!/usr/bin/env python3

import csv
import datetime
import json
import re

from pathlib import Path

import scrapy

from astropy.time import Time

from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging


__here__ = Path(__file__).parent.absolute()


I_FILE_NAME = __here__ / "n12_greads_library_export.csv"
O_FILE_NAME = __here__ / "n14_greads_library.jsonl"

SITE_ROOT_URL     = "https://www.goodreads.com"
BOOK_URL_TEMPLATE = f"{SITE_ROOT_URL}/book/show/{{book_id}}"

DATA_XPATH = "//script[@id='__NEXT_DATA__']/text()"

BOOK_ID_REGEX = re.compile(r"^(\d+)")

HEADERS = {
  b"Accept": b"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  b"Accept-Language": b"en",
  b"User-Agent": b"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:103.0) Gecko/20100101 Firefox/103.0",
  b"Accept-Encoding": b"gzip, deflate",
}

COOKIES = {
  b"locale": b"en",
  b"start_expanded_book_details": b"true",
  b"mobvious.device_type": b"mobile",
  b"srb_8":	b"1_wl",
}


SCRAPY_SETTINGS = {
  "LOG_FORMAT":     "%(asctime)s [%(levelname).1s] [%(process)s %(threadName)s] %(message)s",
  "LOG_DATEFORMAT": "%Y-%m-%d %H:%M:%S.%f %z",

  "DOWNLOAD_DELAY":           0.25,
  "AUTOTHROTTLE_ENABLED":     1,
  "AUTOTHROTTLE_START_DELAY": 1,
  "AUTOTHROTTLE_MAX_DELAY":   5,

  "FEED_FORMAT": "jsonlines",
  "FEED_URI":    str(O_FILE_NAME),
}


def parse_book_id(s: str) -> str:
  return BOOK_ID_REGEX.match(s).group()


def parse_genre_slug(url: str) -> str:
  return url.rstrip().rsplit("/", maxsplit=1)[1]


def parse_author_id(url: str) -> str:
  return url.rsplit("/", maxsplit=1)[1].split(".", maxsplit=1)[0]

def parse_series_id(url: str) -> str:
  return url.rsplit("/", maxsplit=1)[1].split("-", maxsplit=1)[0]


def get_book_contributor(info: dict, entities: dict) -> dict:
  role   = info['role']
  ref    = info['node']['__ref']
  entity = entities[ref]
  e_id   = parse_author_id(entity['webUrl'])
  name   = entity['name']
  return {
    'id':   e_id,
    'name': name,
    'role': role,
  }


def get_book_primary_contributor(book: dict, entities: dict) -> dict:
  info = book['primaryContributorEdge']
  return get_book_contributor(info, entities)


def get_book_secondary_contributors(book: dict, entities: dict) -> dict:
  return [
    get_book_contributor(info, entities)
    for info in book['secondaryContributorEdges']
  ]


def get_book_genres(book: dict) -> list[dict]:
  genres = book['bookGenres'] or []
  return [
    {
      'name': x['genre']['name'],
      'slug': parse_genre_slug(x['genre']['webUrl']),
    }
    for x in genres
  ]


def get_book_work(book: dict, entities: dict) -> dict:
  work_ref = book['work']['__ref']
  return entities[work_ref]


def get_book_stats(work: dict) -> dict:
  stats = work['stats']
  return {
    'rating_avg':        stats['averageRating'],
    'rating_count':      stats['ratingsCount'],
    'rating_count_dist': stats['ratingsCountDist'],
    'reviews_count':     stats['textReviewsCount'],
  }


def get_book_series(book: dict, entities: dict) -> list[dict]:

  def get_one(info: dict) -> dict:
    position = info['userPosition']
    ref      = info['series']['__ref']
    entity   = entities[ref]
    return {
      'title':    entity['title'],
      'id':       parse_series_id(entity['webUrl']),
      'position': position,
    }

  return [get_one(info) for info in book['bookSeries']]


def get_book_links(book: dict) -> list[dict]:

  def get_one(info: dict) -> dict:
    return {
      'name': info['name'],
      'url':  info['url'],
    }

  result = [
    get_one(info)
    for info in book['links({})']['secondaryAffiliateLinks']
  ]
  result.insert(0, get_one(book['links({})']['primaryAffiliateLink']))


def get_book_description_maybe(book: dict) -> str | None:
  result = book['description({"stripped":true})']

  if result is not None:
    result = result.replace(u'\xa0', u' ')

  return result


def parse_time_maybe(value: int | None) -> str | None:

  if value is not None:
    value = Time(value / 1000, format='unix').isot

  return value


def process_item_data(data: dict) -> dict:
  book_id  = parse_book_id(data['query']['book_id'])

  entities = data['props']['pageProps']['apolloState']
  book_ref = entities['ROOT_QUERY'][f'getBookByLegacyId({{"legacyId":"{book_id}"}})']['__ref']
  book     = entities[book_ref]

  book_web_url     = book['webUrl']
  book_title       = book['title']
  book_title_full  = book['titleComplete']
  book_description = get_book_description_maybe(book)
  book_genres      = get_book_genres(book)
  book_pages_n     = book['details']['numPages']
  book_publisher   = book['details']['publisher']
  book_pub_time    = parse_time_maybe(book['details']['publicationTime'])
  book_isbn        = book['details']['isbn']
  book_isbn13      = book['details']['isbn13']
  book_language    = book['details']['language']['name']

  book_primary_contributor    = get_book_primary_contributor(book, entities)
  book_secondary_contributors = get_book_secondary_contributors(book, entities)

  work = get_book_work(book, entities)
  work_original_title = work['details']['originalTitle']
  work_pub_time       = parse_time_maybe(work['details']['publicationTime'])

  book_stats  = get_book_stats(work)
  book_series = get_book_series(book, entities)
  book_links  = get_book_links(book)

  return {
    'book_id':                book_id,
    'title':                  book_title,
    'title_full':             book_title_full,
    'title_original':         work_original_title,
    'description':            book_description,
    'genres':                 book_genres,
    'web_url':                book_web_url,
    'pages_n':                book_pages_n,
    'pub_time':               book_pub_time,
    'pub_first':              work_pub_time,
    'book_publisher':         book_publisher,
    'book_isbn':              book_isbn,
    'book_isbn13':            book_isbn13,
    'book_language':          book_language,
    'primary_contributor':    book_primary_contributor,
    'secondary_contributors': book_secondary_contributors,
    'stats':                  book_stats,
    'series':                 book_series,
    'links':                  book_links,
  }


class GoodReadsBooksSpider(scrapy.Spider):
  name = 'greads_books'

  def __init__(self, catalog_file_path: Path | str, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.catalog_file_path = Path(catalog_file_path)

  def start_requests(self):
    with self.catalog_file_path.open('rt') as f:
      for book in csv.DictReader(f):
        url = BOOK_URL_TEMPLATE.format(book_id = book['Book Id'])
        yield scrapy.Request(
          url      = url,
          callback = self.parse,
          headers  = HEADERS,
          cookies  = COOKIES,
        )

  def parse(self, response):
    data = json.loads(response.selector.xpath(DATA_XPATH).get())
    yield process_item_data(data)


def main() -> None:
  configure_logging(
    settings = SCRAPY_SETTINGS,
  )
  process = CrawlerProcess(
    settings = SCRAPY_SETTINGS,
  )
  process.crawl(GoodReadsBooksSpider, catalog_file_path=I_FILE_NAME)
  process.start()


if __name__ == "__main__":
  main()
