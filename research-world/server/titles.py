from __future__ import annotations

import re

TITLE_TOKEN_LIMIT = 12

_TOKEN_PATTERN = re.compile(
    r"[\u3400-\u9fff\uf900-\ufaff]"
    r"|[A-Za-z0-9]+"
    r"|[^\sA-Za-z0-9\u3400-\u9fff\uf900-\ufaff]"
)


def validate_title(value) -> str:
    if not isinstance(value, str):
        raise TypeError("node title must be a string")
    title = value.strip()
    if not title:
        raise ValueError("node title must be non-empty text")
    if len(_TOKEN_PATTERN.findall(title)) > TITLE_TOKEN_LIMIT:
        raise ValueError("node title exceeds the 12-token limit")
    return title
