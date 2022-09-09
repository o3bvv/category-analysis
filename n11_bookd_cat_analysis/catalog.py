import json

from collections.abc import Iterable
from collections.abc import Mapping

from pathlib import Path


__here__ = Path(__file__).parent.absolute()


CATALOG_FILE_PATH_DEFAULT = __here__.parent / "n08_bookd_cat_tree.json"
EXCLUDED_TITLES_DEFAULT   = set()


def load_catalog(
  file_path: Path | None = None,
) -> Iterable[Mapping]:
  if file_path is None:
    file_path = CATALOG_FILE_PATH_DEFAULT

  with file_path.open("rt") as f:
    return json.load(f)
