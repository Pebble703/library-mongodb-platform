"""读者模块：读者信息查询与学院、等级的分布统计。"""


def list_readers(db, query=None, limit=0):
    """查看读者列表，可按条件过滤。"""
    cursor = db.readers.find(query or {}, {"_id": 0}).sort("card_no", 1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def get_reader(db, card_no):
    """按借阅证号查一位读者。"""
    return db.readers.find_one({"card_no": card_no})


def count_readers(db, query=None):
    """统计读者数量。"""
    return db.readers.count_documents(query or {})


def college_statistics(db):
    """按学院统计读者人数。"""
    pipeline = [
        {"$group": {"_id": "$college", "reader_count": {"$sum": 1}}},
        {"$sort": {"reader_count": -1, "_id": 1}},
    ]
    return list(db.readers.aggregate(pipeline))


def level_statistics(db):
    """按借阅等级统计读者人数。"""
    pipeline = [
        {"$group": {"_id": "$level", "reader_count": {"$sum": 1}}},
        {"$sort": {"reader_count": -1, "_id": 1}},
    ]
    return list(db.readers.aggregate(pipeline))


def distinct_colleges(db):
    """取出所有学院名称。"""
    return sorted(db.readers.distinct("college"))
