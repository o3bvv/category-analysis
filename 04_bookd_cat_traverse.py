#!/usr/bin/env python3

import csv

import scrapy

from urllib.parse import urljoin


DOWNLOAD_DELAY = 1

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 3


BASE_URL = "https://www.bookdepository.com/category/"
ROOT_CATEGORIES_FILE_PATH = "03_bookd_cat_root.csv"


TITLE_XPATH    = "//span[contains(@class, 'current-page')][1]/text()"
COUNT_XPATH    = "//span[@class='search-count'][1]/text()"
CHILDREN_XPATH = "/".join([
  "//ul[contains(@class, 'category-list')]",
  "li[not(contains(@class, 'parent-item'))]",
  "a[contains(@class, 'sub-category') and not(contains(@href, 'browse/viewmode'))]",
  "@href"
])


def make_start_urls(base_url, root_categories_file_path):
  with open(root_categories_file_path, newline='') as f:
    return [
      urljoin(base_url, c['subpath'])
      for c in csv.DictReader(f)
    ]


def extract_subpath(url):
   return url.rstrip("/").rsplit("/category/")[1]


def parse_title(selector) -> str:
  return selector.xpath(TITLE_XPATH).get().strip()


def parse_count_maybe(selector) -> int | None:
  value = selector.xpath(COUNT_XPATH).get()
  if value:
    return int(value.replace(",", ""))


def extract_children(selector) -> list[str]:
  items = selector.xpath(CHILDREN_XPATH).getall()
  return [
    extract_subpath(x) for x in items
  ]


class BookDepositoryCategoriesSpider(scrapy.Spider):
  name       = "bookd_cat"
  start_urls = make_start_urls(BASE_URL, ROOT_CATEGORIES_FILE_PATH)

  def parse(self, response):
    title    = parse_title(response.selector)
    subpath  = extract_subpath(response.url)
    count    = parse_count_maybe(response.selector)
    children = extract_children(response.selector)

    yield dict(
      title    = title,
      subpath  = subpath,
      count    = count,
      children = children or None,
    )

    for child in children:
      next_page = urljoin(BASE_URL, child)
      yield scrapy.Request(next_page, callback=self.parse)


def main():
  ...


if __name__ == "__main__":
  main()
