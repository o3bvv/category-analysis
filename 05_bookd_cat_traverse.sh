#!/usr/bin/env bash

set -e

SPIDER_FILE_NAME="04_bookd_cat_traverse.py"
O_FILE_NAME="06_bookd_cat_flat.jl"

scrapy runspider \
  -s DOWNLOAD_DELAY=0.25 \
  -s AUTOTHROTTLE_ENABLED=1 \
  -s AUTOTHROTTLE_START_DELAY=1 \
  -s AUTOTHROTTLE_MAX_DELAY=5 \
  -o "$O_FILE_NAME" \
  "$SPIDER_FILE_NAME"
