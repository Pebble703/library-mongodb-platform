"""Execute the required Q1-Q16 and A1-A9 checks and save JSON evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util

import book_manager
import borrow_manager
import reader_manager
import stat_manager
from mongodb_connect import get_client


def rows(cursor) -> list[dict]:
    return list(cursor)


def run_queries(db) -> dict:
    books = db.books
    readers = db.readers
    first_book = books.find_one({}, {"_id": 0}) or {}
    first_isbn = first_book.get("isbn", "9787115428028")
    first_publisher = first_book.get("publisher", "不存在的出版社")
    query_specs = {
        "Q1_price_gt_80": {"price": {"$gt": 80}},
        "Q2_stock_lt_10": {"stock": {"$lt": 10}},
        "Q3_isbn_eq": {"isbn": {"$eq": first_isbn}},
        "Q5_publisher_ne": {"publisher": {"$ne": first_publisher}},
        "Q6_category_in": {"category": {"$in": ["计算机", "经济管理"]}},
        "Q7_rating_and_category": {"$and": [{"rating": {"$gte": 4.0}}, {"category": "计算机"}]},
        "Q8_low_rating_or_empty_stock": {"$or": [{"rating": {"$lt": 3.5}}, {"stock": 0}]},
        "Q9_title_regex_python": {"title": {"$regex": "Python", "$options": "i"}},
        "Q10_tags_all": {"tags": {"$all": ["编程", "入门"]}},
        "Q11_tags_size_3": {"tags": {"$size": 3}},
        "Q12_tags_exists": {"tags": {"$exists": True}},
        "Q13_id_string_type": {"_id": {"$type": "string"}},
    }
    query_results = {
        name: {"query": query, "count": books.count_documents(query), "sample": rows(books.find(query).limit(3))}
        for name, query in query_specs.items()
    }
    reader_email_query = {"email": {"$eq": None}}
    query_results["Q4_reader_email_null"] = {
        "query": reader_email_query,
        "collection": "readers",
        "count": readers.count_documents(reader_email_query),
        "sample": rows(readers.find(reader_email_query, {"_id": 0}).limit(3)),
    }
    top5_cursor = books.find({}, {"_id": 0, "title": 1, "rating": 1}).sort("rating", -1).limit(5)
    query_results["Q14_rating_sort_limit"] = {"count": len(rows(top5_cursor)), "sample": rows(books.find({}, {"_id": 0, "title": 1, "rating": 1}).sort("rating", -1).limit(5))}
    projection = {"_id": 0, "title": 1, "price": 1, "rating": 1}
    projection_rows = rows(books.find({}, projection).limit(5))
    query_results["Q15_projection"] = {"projection": projection, "count": len(projection_rows), "sample": projection_rows}
    query_results["Q16_distinct_categories"] = {"values": sorted(books.distinct("category"))}
    return query_results


def run_mutations(db) -> dict:
    book = db.books.find_one({}, {"_id": 1, "isbn": 1, "category": 1})
    reader = db.readers.find_one({})
    if not book or not reader:
        return {"skipped": "books or readers is empty"}
    isbn = book["isbn"]
    category = book.get("category")
    before_overdue = list(db.borrow_logs.find({"status": "逾期"}).limit(10))
    u1 = db.books.update_one({"isbn": isbn}, {"$inc": {"stock": -5}})
    u2 = db.books.update_many({"category": category}, {"$mul": {"price": 0.9}})
    u3 = db.books.update_one({"isbn": isbn}, {"$currentDate": {"last_checked": True}})
    u4 = db.books.update_one({"isbn": isbn}, {"$unset": {"tags": ""}})
    d1 = db.borrow_logs.delete_one({"status": {"$eq": "已归还"}})
    d2 = db.borrow_logs.delete_many({"status": "逾期"})
    replacement = dict(reader)
    replacement["_id"] = reader["_id"]
    replacement["note"] = "replaceOne 验证记录"
    d3 = db.readers.replace_one({"card_no": reader["card_no"]}, replacement)
    return {
        "preview_D2_overdue_count": len(before_overdue),
        "U1_updateOne_inc": {"matched": u1.matched_count, "modified": u1.modified_count},
        "U2_updateMany_mul": {"matched": u2.matched_count, "modified": u2.modified_count},
        "U3_currentDate": {"matched": u3.matched_count, "modified": u3.modified_count},
        "U4_unset_tags": {"matched": u4.matched_count, "modified": u4.modified_count},
        "D1_deleteOne_eq": {"deleted": d1.deleted_count},
        "D2_deleteMany_overdue": {"deleted": d2.deleted_count},
        "D3_replaceOne": {"matched": d3.matched_count, "modified": d3.modified_count},
    }


def index_evidence(db) -> dict:
    result = {"books_indexes": list(db.books.list_indexes()), "explain": {}}
    try:
        filter_query = {"category": "计算机", "price": {"$gte": 80}}
        indexed = db.command("explain", {"find": "books", "filter": filter_query}, verbosity="executionStats")
        natural = db.command("explain", {"find": "books", "filter": filter_query, "hint": {"$natural": 1}}, verbosity="executionStats")
        result["explain"] = {
            "indexed": {
                "executionTimeMillis": indexed.get("executionStats", {}).get("executionTimeMillis"),
                "nReturned": indexed.get("executionStats", {}).get("nReturned"),
            },
            "natural": {
                "executionTimeMillis": natural.get("executionStats", {}).get("executionTimeMillis"),
                "nReturned": natural.get("executionStats", {}).get("nReturned"),
            },
        }
    except Exception as exc:
        result["explain_error"] = str(exc)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mutate", action="store_true", help="execute U1-U4 and D1-D3 after recording the preview")
    args = parser.parse_args()
    client = get_client()
    try:
        db = client.get_database("library")
        result = {
            "generated_at": datetime.now(timezone.utc),
            "counts_before": stat_manager.collection_counts(db),
            "queries": run_queries(db),
            "mutations": run_mutations(db) if args.mutate else {"skipped": "use --mutate to execute U/D operations"},
            "reports": stat_manager.run_all_reports(db),
            "A9_category_stats": stat_manager.save_category_statistics(db),
            "indexes": index_evidence(db),
            "counts_after": stat_manager.collection_counts(db),
        }
        out_dir = Path(__file__).resolve().parent / "artifacts"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "validation_results.json").write_text(json_util.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json_util.dumps(result, ensure_ascii=False, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

