"""Aggregation pipelines used by the library reporting screens."""

from __future__ import annotations

from typing import Any


def category_statistics(db) -> list[dict[str, Any]]:
    return list(
        db.books.aggregate(
            [
                {
                    "$group": {
                        "_id": "$category",
                        "book_count": {"$sum": 1},
                        "average_rating": {"$avg": "$rating"},
                        "max_stock": {"$max": "$stock"},
                        "min_stock": {"$min": "$stock"},
                        "total_stock": {"$sum": "$stock"},
                        "average_price": {"$avg": "$price"},
                    }
                },
                {"$sort": {"total_stock": -1, "_id": 1}},
                {
                    "$project": {
                        "_id": 1,
                        "book_count": 1,
                        "average_rating": {"$round": ["$average_rating", 2]},
                        "max_stock": 1,
                        "min_stock": 1,
                        "total_stock": 1,
                        "average_price": {"$round": ["$average_price", 2]},
                    }
                },
            ]
        )
    )


def publisher_top5(db) -> list[dict[str, Any]]:
    return list(
        db.books.aggregate(
            [
                {"$group": {"_id": "$publisher", "book_count": {"$sum": 1}}},
                {"$sort": {"book_count": -1, "_id": 1}},
                {"$limit": 5},
            ]
        )
    )


def most_common_category(db) -> list[dict[str, Any]]:
    return list(db.books.aggregate([{"$sortByCount": "$category"}, {"$limit": 1}]))


def top_rated_books(db, limit: int = 3) -> list[dict[str, Any]]:
    return list(
        db.books.aggregate(
            [
                {"$sort": {"rating": -1, "borrow_count": -1}},
                {"$limit": limit},
                {"$project": {"_id": 0, "title": 1, "rating": 1, "borrow_count": 1}},
            ]
        )
    )


def book_sales(db) -> list[dict[str, Any]]:
    return list(
        db.books.aggregate(
            [
                {
                    "$set": {
                        "sales": {
                            "$round": [{"$multiply": ["$price", "$borrow_count"]}, 2]
                        }
                    }
                },
                {"$sort": {"sales": -1}},
                {"$project": {"_id": 0, "isbn": 1, "title": 1, "sales": 1}},
            ]
        )
    )


def borrow_trend(db) -> list[dict[str, Any]]:
    return list(
        db.borrow_logs.aggregate(
            [
                {
                    "$group": {
                        "_id": {"$dateToString": {"format": "%Y年", "date": "$borrow_date"}},
                        "borrow_count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
    )


def reader_top5(db) -> list[dict[str, Any]]:
    return list(
        db.borrow_logs.aggregate(
            [
                {"$group": {"_id": "$reader_card", "borrow_count": {"$sum": 1}}},
                {"$sort": {"borrow_count": -1, "_id": 1}},
                {"$limit": 5},
                {
                    "$lookup": {
                        "from": "readers",
                        "localField": "_id",
                        "foreignField": "card_no",
                        "as": "reader",
                    }
                },
                {"$unwind": {"path": "$reader", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": 0,
                        "card_no": "$_id",
                        "name": "$reader.name",
                        "college": "$reader.college",
                        "borrow_count": 1,
                    }
                },
            ]
        )
    )


def college_borrow_ranking(db) -> list[dict[str, Any]]:
    return list(
        db.borrow_logs.aggregate(
            [
                {
                    "$lookup": {
                        "from": "readers",
                        "localField": "reader_card",
                        "foreignField": "card_no",
                        "as": "reader",
                    }
                },
                {"$unwind": "$reader"},
                {"$group": {"_id": "$reader.college", "borrow_count": {"$sum": 1}}},
                {"$sort": {"borrow_count": -1, "_id": 1}},
            ]
        )
    )


def save_category_statistics(db) -> list[dict[str, Any]]:
    """Run A1 and persist the same result in ``category_stats`` (A9)."""

    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "book_count": {"$sum": 1},
                "average_rating": {"$avg": "$rating"},
                "max_stock": {"$max": "$stock"},
                "min_stock": {"$min": "$stock"},
                "total_stock": {"$sum": "$stock"},
            }
        },
        {"$set": {"generated_at": "$$NOW"}},
        {
            "$merge": {
                "into": "category_stats",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert",
            }
        },
    ]
    list(db.books.aggregate(pipeline))
    return list(db.category_stats.find({}, {"_id": 1, "book_count": 1, "average_rating": 1, "max_stock": 1, "min_stock": 1, "total_stock": 1}).sort("_id", 1))


def collection_counts(db) -> dict[str, int]:
    names = ["books", "readers", "borrow_logs", "category_stats", "book_logs"]
    return {name: db[name].count_documents({}) for name in names if name in db.list_collection_names()}


def run_all_reports(db) -> dict[str, list[dict[str, Any]]]:
    return {
        "A1_category_statistics": category_statistics(db),
        "A2_publisher_top5": publisher_top5(db),
        "A3_most_common_category": most_common_category(db),
        "A4_top_rated_books": top_rated_books(db),
        "A5_book_sales": book_sales(db),
        "A6_borrow_trend": borrow_trend(db),
        "A7_reader_top5": reader_top5(db),
        "A8_college_borrow_ranking": college_borrow_ranking(db),
    }

