from dataclasses import dataclass

__all__ = ["LocalMapQuery"]


@dataclass(frozen=True, slots=True)
class LocalMapQuery:
    text: str | None = None
    record_id: str | None = None
    limit: int = 20
