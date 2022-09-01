#!/usr/bin/env python3

from __future__ import annotations

import csv
import dataclasses
import json

from typing import Any
from typing import Collection


I_ROOT_IDS_FILE_NAME = "03_bookd_cat_root.csv"
I_ROOT_IDS_EXCLUDE   = {
  "3389/Audio-Books",
  "2455/Childrens-Books",
  "2633/Graphic-Novels-Anime-Manga",
  "",
}

I_CATALOG_FILE_NAME  = "06_bookd_cat_flat.jl"

O_CATALOG_FILE_NAME  = "08_bookd_cat_tree.json"
O_CATALOG_INDENT     = 2


@dataclasses.dataclass
class TreeNode:
  id:       str
  data:     Any
  children: list[TreeNode] | None


def build_tree(node_id: str, catalog: dict) -> TreeNode:
  item = catalog.get(node_id)
  if not item:
    return

  children = item.get('children') or None
  if children:
    children = [
      build_tree(child_id, catalog)
      for child_id in children
    ]
    children = list(filter(bool, children))

  count = item['count']
  if count is None and children:
    count = sum(
      child.data.get('count') or 0
      for child in children
    )

  data  = dict(
    title = item['title'],
    count = count,
  )

  return TreeNode(
    id       = node_id,
    data     = data,
    children = children,
  )


def transform_catalog(catalog: dict, root_ids: list[str]) -> list[TreeNode]:
  trees = [build_tree(node_id, catalog) for node_id in root_ids]
  return list(filter(bool, trees))


def load_root_ids(file_path: str, excluded_ids: Collection) -> list[str]:
  with open(file_path, newline='') as f:
    return [
      c['subpath']
      for c in csv.DictReader(f)
      if c['subpath'] not in excluded_ids
    ]


def load_catalog(file_path: str) -> dict[dict]:
  result = dict()

  with open(file_path) as f:
    for s in f:
      item = json.loads(s)
      result[item['subpath']] = item

  return result


def save_catalog(catalog: list[TreeNode], file_path: str, indent: int | None) -> None:
  catalog = [
    dataclasses.asdict(category_tree)
    for category_tree in catalog
  ]
  with open(file_path, 'wt') as f:
    json.dump(catalog, f, indent = indent)
    f.write("\n")


def main() -> None:
  root_ids = load_root_ids(I_ROOT_IDS_FILE_NAME, I_ROOT_IDS_EXCLUDE)
  catalog  = load_catalog(I_CATALOG_FILE_NAME)
  catalog  = transform_catalog(catalog, root_ids)
  save_catalog(catalog, O_CATALOG_FILE_NAME, O_CATALOG_INDENT)


if __name__ == "__main__":
  main()
