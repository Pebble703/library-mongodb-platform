"""统计模块：用聚合管道完成分类统计、借阅趋势与排行榜。"""


def category_statistics(db):
    """按类别统计图书数量、库存与评分。"""
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "book_count": {"$sum": 1},
                "total_stock": {"$sum": "$stock"},
                "max_stock": {"$max": "$stock"},
                "min_stock": {"$min": "$stock"},
                "average_rating": {"$avg": "$rating"},
                "average_price": {"$avg": "$price"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "book_count": 1,
                "total_stock": 1,
                "max_stock": 1,
                "min_stock": 1,
                "average_rating": {"$round": ["$average_rating", 2]},
                "average_price": {"$round": ["$average_price", 2]},
            }
        },
        {"$sort": {"total_stock": -1, "_id": 1}},
    ]
    return list(db.books.aggregate(pipeline))


def publisher_top5(db):
    """出版社藏书量前五。"""
    pipeline = [
        {"$group": {"_id": "$publisher", "book_count": {"$sum": 1}}},
        {"$sort": {"book_count": -1, "_id": 1}},
        {"$limit": 5},
    ]
    return list(db.books.aggregate(pipeline))


def most_common_category(db):
    """藏书最多的类别。"""
    return list(db.books.aggregate([{"$sortByCount": "$category"}, {"$limit": 1}]))


def top_rated_books(db, limit=3):
    """评分最高的若干本图书。"""
    pipeline = [
        {"$sort": {"rating": -1, "borrow_count": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "title": 1, "rating": 1, "borrow_count": 1}},
    ]
    return list(db.books.aggregate(pipeline))


def best_sellers(db, limit=5):
    """畅销榜：按借阅次数取前几名。"""
    pipeline = [
        {"$sort": {"borrow_count": -1, "isbn": 1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "isbn": 1, "title": 1, "borrow_count": 1}},
    ]
    return list(db.books.aggregate(pipeline))


def book_sales(db):
    """销售额 = 单价 × 借阅次数，保留两位小数。"""
    pipeline = [
        {"$set": {"sales": {"$round": [{"$multiply": ["$price", "$borrow_count"]}, 2]}}},
        {"$sort": {"sales": -1}},
        {"$project": {"_id": 0, "isbn": 1, "title": 1, "sales": 1}},
    ]
    return list(db.books.aggregate(pipeline))


def borrow_trend(db):
    """按年份统计借阅量，输出成 2024年 这样的字符串。"""
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


def reader_top5(db):
    """借阅次数最多的五位读者，关联出姓名和学院。"""
    pipeline = [
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
    return list(db.borrow_logs.aggregate(pipeline))


def college_borrow_ranking(db):
    """学院借阅量排行榜。"""
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
    ]
    return list(db.borrow_logs.aggregate(pipeline))


def save_category_statistics(db):
    """把分类统计结果用 $merge 写入 category_stats 集合。"""
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "book_count": {"$sum": 1},
                "total_stock": {"$sum": "$stock"},
                "max_stock": {"$max": "$stock"},
                "min_stock": {"$min": "$stock"},
                "average_rating": {"$avg": "$rating"},
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
    return list(db.category_stats.find().sort("_id", 1))


def collection_counts(db):
    """统计各集合的文档数。"""
    names = ["books", "readers", "borrow_logs", "category_stats", "book_logs"]
    counts = {}
    for name in names:
        if name in db.list_collection_names():
            counts[name] = db[name].count_documents({})
    return counts


def run_all_reports(db):
    """一次跑完全部统计，写验证脚本时用。"""
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
