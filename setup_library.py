"""Create the assignment schema and import the supplied Extended JSON data.

Examples::

    python setup_library.py --reset
    python setup_library.py                 # idempotent import

Use ``MONGO_URI`` and ``MONGO_DB`` to target a Linux or remote instance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bson import json_util
from pymongo import ASCENDING, DESCENDING, ReplaceOne
from pymongo.errors import CollectionInvalid, OperationFailure

from mongodb_connect import DATABASE_NAME, get_client
from stat_manager import collection_counts, save_category_statistics


BASE_DIR = Path(__file__).resolve().parent


def load_extended_json(path: Path) -> list[dict[str, Any]]:
    data = json_util.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON array in {path.name}")
    return data


def ensure_view(db) -> str:
    existing = db.list_collection_names(filter={"name": "book_in_stock"})
    if existing:
        info = db.command("listCollections", filter={"name": "book_in_stock"})["cursor"]["firstBatch"][0]
        if info.get("type") == "view":
            return "existing"
        return "skipped: book_in_stock is an ordinary collection"
    db.create_collection(
        "book_in_stock",
        viewOn="books",
        pipeline=[{"$match": {"stock": {"$gt": 0}}}],
    )
    return "created"


def ensure_collections(db) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ("books", "readers", "category_stats"):
        if name in db.list_collection_names():
            result[name] = "existing"
        else:
            db.create_collection(name)
            result[name] = "created"

    if "book_logs" not in db.list_collection_names():
        db.create_collection("book_logs", capped=True, size=1_048_576, max=1000)
        result["book_logs"] = "created capped (1MB/1000 docs)"
    else:
        result["book_logs"] = "existing"

    if "borrow_logs" not in db.list_collection_names():
        db.create_collection(
            "borrow_logs",
            timeseries={"timeField": "borrow_date", "granularity": "hours"},
            expireAfterSeconds=63_072_000,
        )
        result["borrow_logs"] = "created time-series (hours/2 years)"
    else:
        result["borrow_logs"] = "existing"

    result["book_in_stock"] = ensure_view(db)
    return result


def import_data(db, data_dir: Path) -> dict[str, Any]:
    books = load_extended_json(data_dir / "books.txt")
    readers = load_extended_json(data_dir / "readers.txt")
    borrows = load_extended_json(data_dir / "borrow_logs.txt")
    operations: dict[str, Any] = {}

    def upsert_documents(collection, docs: list[dict[str, Any]], key: str) -> dict[str, int]:
        if not docs:
            return {"inserted": 0, "upserted": 0, "modified": 0}
        if collection.count_documents({}) == 0:
            first = collection.insert_one(docs[0])
            result = collection.insert_many(docs[1:], ordered=True) if len(docs) > 1 else None
            return {
                "inserted": 1 + (len(result.inserted_ids) if result else 0),
                "insertOne": 1,
                "insertMany": len(result.inserted_ids) if result else 0,
            }
        requests = [ReplaceOne({key: doc[key]}, doc, upsert=True) for doc in docs]
        result = collection.bulk_write(requests, ordered=False)
        return {
            "inserted": result.upserted_count,
            "upserted": result.upserted_count,
            "modified": result.modified_count,
        }

    operations["books"] = upsert_documents(db.books, books, "isbn")
    operations["readers"] = upsert_documents(db.readers, readers, "card_no")
    if db.borrow_logs.count_documents({}) == 0:
        result = db.borrow_logs.insert_many(borrows, ordered=True)
        operations["borrow_logs"] = {"insertMany": len(result.inserted_ids)}
    else:
        operations["borrow_logs"] = {"skipped": db.borrow_logs.count_documents({}), "reason": "already populated"}
    return operations


def ensure_indexes(db) -> dict[str, str]:
    indexes = {
        "books": [
            ([('isbn', ASCENDING)], {"unique": True, "name": "uniq_isbn"}),
            ([('title', ASCENDING)], {"name": "idx_title"}),
            ([('category', ASCENDING)], {"name": "idx_category"}),
            ([('tags', ASCENDING)], {"name": "idx_tags_multikey"}),
            ([('category', ASCENDING), ('price', ASCENDING)], {"name": "idx_category_price"}),
        ],
        "readers": [
            ([('card_no', ASCENDING)], {"unique": True, "name": "uniq_card_no"}),
        ],
        "borrow_logs": [
            ([('reader_card', ASCENDING), ('status', ASCENDING)], {"name": "idx_reader_status"}),
            ([('book_isbn', ASCENDING), ('status', ASCENDING)], {"name": "idx_book_status"}),
        ],
    }
    created: dict[str, str] = {}
    for collection_name, definitions in indexes.items():
        for keys, options in definitions:
            try:
                created[options["name"]] = db[collection_name].create_index(keys, **{k: v for k, v in options.items() if k != "name"}, name=options["name"])
            except OperationFailure as exc:
                created[options["name"]] = f"existing/error: {exc.details.get('codeName', str(exc))}"
    return created


def collection_options(db) -> list[dict[str, Any]]:
    infos = db.command("listCollections", nameOnly=False)["cursor"]["firstBatch"]
    wanted = {"books", "readers", "borrow_logs", "category_stats", "book_logs", "book_in_stock"}
    return [
        {"name": info["name"], "type": info.get("type"), "options": info.get("options", {})}
        for info in infos
        if info["name"] in wanted
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop only the configured library database first")
    parser.add_argument("--data-dir", type=Path, default=BASE_DIR)
    args = parser.parse_args()
    client = get_client()
    try:
        client.admin.command("ping")
        if args.reset:
            client.drop_database(DATABASE_NAME)
        db = client[DATABASE_NAME]
        schema = ensure_collections(db)
        operations = import_data(db, args.data_dir)
        indexes = ensure_indexes(db)
        category_stats = save_category_statistics(db)
        result = {
            "database": DATABASE_NAME,
            "schema": schema,
            "operations": operations,
            "indexes": indexes,
            "counts": collection_counts(db),
            "collection_options": collection_options(db),
            "category_stats_count": len(category_stats),
        }
        artifacts = BASE_DIR / "artifacts"
        artifacts.mkdir(exist_ok=True)
        (artifacts / "setup_result.json").write_text(
            json_util.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json_util.dumps(result, ensure_ascii=False, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

