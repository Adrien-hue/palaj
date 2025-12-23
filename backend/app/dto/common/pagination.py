from __future__ import annotations

import math
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Params de pagination réutilisables via Depends().
    """
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> PaginationParams:
    """
    Dependency FastAPI (plus flexible que Depends(PaginationParams) avec Query).
    """
    return PaginationParams(page=page, page_size=page_size)


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta


def build_page(items: List[T], total: int, p: PaginationParams) -> Page[T]:
    pages = math.ceil(total / p.page_size) if total else 0
    return Page[T](
        items=items,
        meta=PageMeta(
            page=p.page,
            page_size=p.page_size,
            total=total,
            pages=pages,
        ),
    )
