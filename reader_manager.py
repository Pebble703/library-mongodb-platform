"""读者模块：读者查询与学院、等级分布统计。"""


def list_readers(db, query=None, limit=0):
    cursor = db.readers.find(query or {}, {"_id": 0}).sort("card_no", 1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def get_reader(db, card_no):
    return db.readers.find_one({"card_no": card_no}, {"_id": 0})


def count_readers(db, query=None):
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
    return sorted(db.readers.distinct("college"))

def insert_reader(db, reader):
    """新增读者，证号重复会被唯一索引拦住。"""
    return db.readers.insert_one(reader)


def update_reader(db, card_no, fields):
    """修改读者信息，证号不允许改。"""
    allowed = {"name", "college", "level", "email", "fav_categories", "register_date"}
    data = {k: v for k, v in fields.items() if k in allowed}
    if not data:
        raise ValueError("没有可更新的字段")
    return db.readers.update_one({"card_no": card_no}, {"$set": data})


def delete_reader(db, card_no):
    """删除读者：还有未归还借阅时拒绝删除，避免流水指向不存在的读者。"""
    active = db.borrow_logs.count_documents(
        {"reader_card": card_no, "status": {"$in": ["借出", "逾期"]}})
    if active:
        raise ValueError("该读者还有 %d 条未归还借阅，不能删除" % active)
    return db.readers.delete_one({"card_no": card_no})


def list_page(db, query=None, page=1, size=10, sort=None):
    """分页浏览读者。"""
    query = query or {}
    size = max(1, size)
    total = db.readers.count_documents(query)
    pages = max(1, (total + size - 1) // size)
    page = min(max(1, page), pages)
    cursor = (db.readers.find(query, {"_id": 0, "card_no": 1, "name": 1, "college": 1, "level": 1})
              .sort(sort or [("card_no", 1)])
              .skip((page - 1) * size)
              .limit(size))
    return {"total": total, "pages": pages, "page": page, "size": size, "rows": list(cursor)}
