from math import ceil


def parse_pagination_args(args, default_page_size: int = 20, max_page_size: int = 100) -> dict:
    def _to_int(name: str, default: int) -> int:
        raw = args.get(name, default)
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc
        return value

    page = max(_to_int("page", 1), 1)
    page_size = _to_int("page_size", default_page_size)
    page_size = min(max(page_size, 1), max_page_size)
    return {
        "page": page,
        "page_size": page_size,
        "q": (args.get("q") or "").strip(),
        "status": (args.get("status") or "").strip(),
        "sort": (args.get("sort") or "-created_at").strip(),
        "level": (args.get("level") or "").strip(),
    }


def build_paginated_payload(items: list, total: int, page: int, page_size: int) -> dict:
    total_pages = ceil(total / page_size) if total else 0
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }
