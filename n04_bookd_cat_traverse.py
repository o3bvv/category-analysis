#!/usr/bin/env python3

import csv

from typing import Collection

import scrapy


ROOT_CATEGORIES_FILE_NAME    = "n03_bookd_cat_root_all.csv"
ROOT_CATEGORIES_IDS_EXCLUDED = {
  "3389/Audio-Books",
  "2455/Childrens-Books",
  "2633/Graphic-Novels-Anime-Manga",
}

SITE_ROOT_URL           = "https://www.bookdepository.com"

CATEGORY_ROOT_PATH      = "/category/"
CATEGORY_ROOT_PATH_LEN  = len(CATEGORY_ROOT_PATH)

CATEGORY_URL_PREFIX     = f"{SITE_ROOT_URL}{CATEGORY_ROOT_PATH}"
CATEGORY_URL_PREFIX_LEN = len(CATEGORY_URL_PREFIX)

CATEGORY_URL_SUFFIX     = "/browse/viewmode/all"
CATEGORY_URL_SUFFIX_LEN = len(CATEGORY_URL_SUFFIX)

CATEGORY_URL_TEMPLATE   = f"{CATEGORY_URL_PREFIX}{{category_id}}{CATEGORY_URL_SUFFIX}"

TITLE_XPATH    = "//span[contains(@class, 'current-page')][1]/text()"
COUNT_XPATH    = "//span[@class='search-count'][1]/text()"
CHILDREN_XPATH = "/".join([
  "//ul[contains(@class, 'category-list')]",
  "li[not(contains(@class, 'parent-item'))]",
  "a[contains(@class, 'sub-category') and not(contains(@href, 'browse/viewmode'))]",
  "@href"
])


def format_url(category_id: str) -> str:
  return CATEGORY_URL_TEMPLATE.format(category_id = category_id)


def parse_cid(url: str) -> str:
  return url[CATEGORY_URL_PREFIX_LEN:-CATEGORY_URL_SUFFIX_LEN]


def parse_child_cid(path: str) -> str:
  return path[CATEGORY_ROOT_PATH_LEN:]


def parse_title(selector) -> str:
  return selector.xpath(TITLE_XPATH).get().strip()


def parse_count_maybe(selector) -> int | None:
  value = selector.xpath(COUNT_XPATH).get()
  if value:
    return int(value.replace(",", ""))


def parse_children_ids(selector) -> list[str]:
  items = selector.xpath(CHILDREN_XPATH).getall()
  return [
    parse_child_cid(x) for x in items
  ]


def load_root_ids(file_path: str, excluded_ids: Collection) -> list[str]:
  with open(file_path, newline='') as f:
    result = [
      c['cid']
      for c in csv.DictReader(f)
      if c['cid'] not in excluded_ids
    ]

  return list(sorted(result))


def make_start_urls(category_ids: list[str]) -> list[str]:
  return [format_url(cid) for cid in category_ids]


class BookDepositoryCategoriesSpider(scrapy.Spider):
  name       = "bookd_categories"
  start_urls = make_start_urls(
    category_ids = load_root_ids(
      file_path    = ROOT_CATEGORIES_FILE_NAME,
      excluded_ids = ROOT_CATEGORIES_IDS_EXCLUDED,
    ),
  )

  def parse(self, response):
    cid      = parse_cid(response.url)
    title    = parse_title(response.selector)
    count    = parse_count_maybe(response.selector)
    children = parse_children_ids(response.selector)

    yield dict(
      title    = title,
      cid      = cid,
      count    = count,
      children = children or None,
    )

    for child_id in children:
      next_page = format_url(child_id)
      yield scrapy.Request(next_page, callback=self.parse)


def main():
  print(BookDepositoryCategoriesSpider.start_urls)


if __name__ == "__main__":
  main()
