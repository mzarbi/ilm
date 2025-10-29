from typing import Tuple
from flask import request


def parse_pagination(default_size: int = 50, max_size: int = 500) -> Tuple[int, int]:
    page = max(int(request.args.get("page", 1)), 1)
    size = min(max(int(request.args.get("page_size", default_size)), 1), max_size)
    return page, size


def parse_sort(default: str = "id:asc"):
    """
    ?sort=field:asc,other:desc
    Returns list of (field, dir)
    """
    raw = request.args.get("sort", default) or ""
    items = []
    for token in raw.split(","):
        if ":" in token:
            f, d = token.split(":", 1)
            d = d.lower()
            items.append((f.strip(), d if d in ("asc", "desc") else "asc"))
        elif token.strip():
            items.append((token.strip(), "asc"))
    return items


def parse_bool_param(name: str, default: bool = False) -> bool:
    v = (request.args.get(name) or "").lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "y", "on")
