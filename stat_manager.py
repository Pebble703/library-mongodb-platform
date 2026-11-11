"""统计模块：分类统计、学院借阅排行、年月趋势与借阅排行。

全部通过聚合管道实现，统计结果用 $merge 写入 category_stats 供后续查询。
"""


def category_statistics(db):
    """按类别统计藏书量、平均价格、平均评分。"""
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "book_count": {"$sum": 1},
                "total_stock": {"$sum": "$stock"},
                "avg_price": {"$avg": "$price"},
                "avg_rating": {"$avg": "$rating"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "book_count": 1,
                "total_stock": 1,
                "avg_price": {"$round": ["$avg_price", 2]},
                "avg_rating": {"$round": ["$avg_rating", 2]},
            }
        },
        {"$sort": {"book_count": -1, "_id": 1}},
    ]
    return list(db.books.aggregate(pipeline))


def college_borrow_top5(db):
    """各学院借阅总量前五：借阅流水关联读者后按学院分组。"""
    pipeline = [
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
        {"$limit": 5},
    ]
    return list(db.borrow_logs.aggregate(pipeline))


def monthly_trend(db):
    """按年月统计借阅趋势，输出 2024-03 形式的标签。"""
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$borrow_date", "timezone": "+08:00"}},
                "borrow_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(db.borrow_logs.aggregate(pipeline))


def top_books(db, limit=10):
    """借阅次数最多的图书，关联出书名与馆藏位置。"""
    pipeline = [
        {"$group": {"_id": "$book_isbn", "borrow_count": {"$sum": 1}}},
        {"$sort": {"borrow_count": -1, "_id": 1}},
        {"$limit": limit},
        {"$lookup": {"from": "books", "localField": "_id", "foreignField": "isbn", "as": "book"}},
        {"$unwind": {"path": "$book", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "isbn": "$_id",
                "title": "$book.title",
                "location": "$book.location",
                "borrow_count": 1,
            }
        },
    ]
    return list(db.borrow_logs.aggregate(pipeline))


def year_trend(db):
    """按年份统计借阅量，供文档与答辩对比使用。"""
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y年", "date": "$borrow_date", "timezone": "+08:00"}},
                "borrow_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(db.borrow_logs.aggregate(pipeline))


def save_category_stats(db):
    """把分类统计结果写入 category_stats 集合（$merge 幂等覆盖）。"""
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "book_count": {"$sum": 1},
                "total_stock": {"$sum": "$stock"},
                "avg_price": {"$avg": "$price"},
                "avg_rating": {"$avg": "$rating"},
            }
        },
        {
            "$set": {
                "avg_price": {"$round": ["$avg_price", 2]},
                "avg_rating": {"$round": ["$avg_rating", 2]},
                "generated_at": "$$NOW",
            }
        },
        {"$merge": {"into": "category_stats", "on": "_id", "whenMatched": "replace", "whenNotMatched": "insert"}},
    ]
    list(db.books.aggregate(pipeline))
    return list(db.category_stats.find().sort("_id", 1))


def collection_counts(db):
    names = ["books", "readers", "borrow_logs", "audit_logs", "category_stats"]
    return {name: db[name].count_documents({}) for name in names if name in db.list_collection_names()}
