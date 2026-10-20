"""Reader management and reader-oriented statistics."""

from __future__ import annotations

from typing import Any, Iterable

from pymongo.collection import Collection


def readers_collection(db) -> Collection:
    return db["readers"]


def add_reader(db, reader: dict[str, Any]):
    return readers_collection(db).insert_one(reader)


def add_readers(db, readers: Iterable[dict[str, Any]]):
    return readers_collection(db).insert_many(list(readers), ordered=False)


def get_reader(db, card_no: str) -> dict[str, Any] | None:
    return readers_collection(db).find_one({"card_no": card_no})


def list_readers(db, query: dict[str, Any] | None = None, limit: int = 0):
    cursor = readers_collection(db).find(query or {}, {"_id": 0}).sort("card_no", 1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def replace_reader(db, card_no: str, replacement: dict[str, Any]):
    """Replace a reader document while retaining the existing ``_id``."""

    replacement = dict(replacement)
    replacement.pop("_id", None)
    return readers_collection(db).replace_one({"card_no": card_no}, replacement)


def delete_reader(db, card_no: str):
    return readers_collection(db).delete_one({"card_no": card_no})


def college_statistics(db) -> list[dict[str, Any]]:
    return list(
        readers_collection(db).aggregate(
            [
                {"$group": {"_id": "$college", "reader_count": {"$sum": 1}}},
                {"$sort": {"reader_count": -1, "_id": 1}},
            ]
        )
    )


def level_statistics(db) -> list[dict[str, Any]]:
    return list(
        readers_collection(db).aggregate(
            [
                {"$group": {"_id": "$level", "reader_count": {"$sum": 1}}},
                {"$sort": {"reader_count": -1, "_id": 1}},
            ]
        )
    )


def count_readers(db, query: dict[str, Any] | None = None) -> int:
    return readers_collection(db).count_documents(query or {})


def distinct_colleges(db) -> list[str]:
    return sorted(readers_collection(db).distinct("college"))

