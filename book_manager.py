"""CRUD and query operations for the ``books`` collection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from pymongo.collection import Collection


def books_collection(db) -> Collection:
    return db["books"]


def insert_book(db, book: dict[str, Any]):
    """Insert one book and return the PyMongo result."""

    return books_collection(db).insert_one(book)


def insert_books(db, books: Iterable[dict[str, Any]]):
    """Insert many books and return the PyMongo result."""

    return books_collection(db).insert_many(list(books), ordered=False)


def get_book(db, isbn: str) -> dict[str, Any] | None:
    return books_collection(db).find_one({"isbn": isbn})


def list_books(
    db,
    filter_query: dict[str, Any] | None = None,
    *,
    sort: list[tuple[str, int]] | None = None,
    limit: int = 0,
    skip: int = 0,
    projection: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    cursor = books_collection(db).find(filter_query or {}, projection)
    if sort:
        cursor = cursor.sort(sort)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def search_books(
    db,
    *,
    keyword: str | None = None,
    title: str | None = None,
    author: str | None = None,
    isbn: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    stock_min: int | None = None,
    stock_max: int | None = None,
    publisher_exclude: list[str] | None = None,
    require_email: bool | None = None,
    page: int = 1,
    page_size: int = 10,
) -> list[dict[str, Any]]:
    """Build a safe combination query for the platform search screen."""

    query: dict[str, Any] = {}
    if isbn:
        query["isbn"] = {"$eq": isbn}
    if keyword:
        query["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"author": {"$regex": keyword, "$options": "i"}},
        ]
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if author:
        query["author"] = {"$regex": author, "$options": "i"}
    if category:
        query["category"] = {"$eq": category}
    if tags:
        query["tags"] = {"$all": tags}
    for field, low, high in (
        ("price", price_min, price_max),
        ("rating", rating_min, rating_max),
        ("stock", stock_min, stock_max),
    ):
        bounds: dict[str, Any] = {}
        if low is not None:
            bounds["$gte"] = low
        if high is not None:
            bounds["$lte"] = high
        if bounds:
            query[field] = bounds
    if publisher_exclude:
        query["publisher"] = {"$nin": publisher_exclude}
    if require_email is not None:
        query["email"] = {"$exists": require_email}
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    return list_books(
        db,
        query,
        sort=[("title", 1)],
        skip=(page - 1) * page_size,
        limit=page_size,
    )


def top_rated(db, limit: int = 5) -> list[dict[str, Any]]:
    return list_books(
        db,
        sort=[("rating", -1), ("borrow_count", -1), ("isbn", 1)],
        limit=limit,
        projection={"_id": 0, "isbn": 1, "title": 1, "rating": 1, "borrow_count": 1},
    )


def update_stock(db, isbn: str, delta: int):
    return books_collection(db).update_one({"isbn": isbn}, {"$inc": {"stock": delta}})


def discount_category(db, category: str, factor: float = 0.9):
    if not 0 < factor <= 1:
        raise ValueError("factor must be between 0 and 1")
    return books_collection(db).update_many(
        {"category": category}, {"$mul": {"price": factor}}
    )


def touch_book(db, isbn: str):
    return books_collection(db).update_one(
        {"isbn": isbn}, {"$currentDate": {"last_checked": True}}
    )


def remove_tags(db, isbn: str):
    return books_collection(db).update_one({"isbn": isbn}, {"$unset": {"tags": ""}})


def delete_book(db, isbn: str):
    return books_collection(db).delete_one({"isbn": isbn})


def count_books(db, query: dict[str, Any] | None = None) -> int:
    return books_collection(db).count_documents(query or {})


def all_categories(db) -> list[str]:
    return sorted(books_collection(db).distinct("category"))


def insert_audit_event(db, action: str, isbn: str, details: dict[str, Any] | None = None):
    """Write an operation event to the capped collection."""

    event = {
        "action": action,
        "isbn": isbn,
        "at": datetime.now(timezone.utc),
        "details": details or {},
    }
    return db["book_logs"].insert_one(event)

