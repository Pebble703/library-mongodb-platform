"""Borrow and return operations over the time-series ``borrow_logs`` collection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection


def borrow_logs_collection(db) -> Collection:
    return db["borrow_logs"]


def list_borrows(db, query: dict[str, Any] | None = None, limit: int = 0):
    cursor = borrow_logs_collection(db).find(query or {}).sort("borrow_date", -1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def borrow_book(
    db,
    reader_card: str,
    book_isbn: str,
    *,
    borrow_date: datetime | None = None,
):
    """Register a borrow and decrement stock when the book is available."""

    reader = db["readers"].find_one({"card_no": reader_card})
    if reader is None:
        raise ValueError(f"reader not found: {reader_card}")
    book = db["books"].find_one_and_update(
        {"isbn": book_isbn, "stock": {"$gt": 0}},
        {"$inc": {"stock": -1, "borrow_count": 1}},
    )
    if book is None:
        raise ValueError(f"book not found or stock is zero: {book_isbn}")
    doc = {
        "borrow_date": borrow_date or datetime.now(timezone.utc),
        "reader_card": reader_card,
        "book_isbn": book_isbn,
        "status": "借出",
    }
    result = borrow_logs_collection(db).insert_one(doc)
    return result, doc


def return_book(
    db,
    reader_card: str,
    book_isbn: str,
    *,
    return_date: datetime | None = None,
):
    """Close the newest active loan and restore one copy to stock."""

    active = borrow_logs_collection(db).find_one_and_update(
        {
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": {"$in": ["借出", "逾期"]},
        },
        {"$set": {"status": "已归还", "return_date": return_date or datetime.now(timezone.utc)}},
        sort=[("borrow_date", -1)],
    )
    if active is None:
        return None
    db["books"].update_one({"isbn": book_isbn}, {"$inc": {"stock": 1}})
    return active


def overdue_loans(db) -> list[dict[str, Any]]:
    return list_borrows(db, {"status": "逾期"})


def mark_overdue(db, before: datetime):
    return borrow_logs_collection(db).update_many(
        {"status": "借出", "borrow_date": {"$lt": before}},
        {"$set": {"status": "逾期"}},
    )


def delete_one_returned(db):
    return borrow_logs_collection(db).delete_one({"status": {"$eq": "已归还"}})


def delete_overdue(db):
    return borrow_logs_collection(db).delete_many({"status": "逾期"})


def count_borrows(db, query: dict[str, Any] | None = None) -> int:
    return borrow_logs_collection(db).count_documents(query or {})

