"""图书模块：图书的增删改查、条件检索与评分排行。"""


def insert_book(db, book):
    """插入一本图书。"""
    return db.books.insert_one(book)


def insert_books(db, books):
    """批量插入图书。"""
    return db.books.insert_many(list(books))


def get_book(db, isbn):
    """按 ISBN 查一本图书。"""
    return db.books.find_one({"isbn": isbn})


def search_books(db, keyword=None, category=None, price_min=None, price_max=None, limit=20):
    """组合条件检索：关键词同时匹配书名或作者，其余条件按需拼接。"""
    query = {}

    # 关键词在书名和作者之间是“或”的关系，不能写成两个字段并列
    if keyword:
        query["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"author": {"$regex": keyword, "$options": "i"}},
        ]

    if category:
        query["category"] = category

    if price_min is not None or price_max is not None:
        query["price"] = {}
        if price_min is not None:
            query["price"]["$gte"] = price_min
        if price_max is not None:
            query["price"]["$lte"] = price_max

    return list(db.books.find(query, {"_id": 0}).sort("rating", -1).limit(limit))


def top_rated(db, limit=5):
    """评分排行，分数相同时按借阅次数排。"""
    cursor = db.books.find({}, {"_id": 0, "isbn": 1, "title": 1, "rating": 1, "borrow_count": 1})
    return list(cursor.sort([("rating", -1), ("borrow_count", -1)]).limit(limit))


def update_stock(db, isbn, delta):
    """调整库存，正数入库、负数出库。"""
    return db.books.update_one({"isbn": isbn}, {"$inc": {"stock": delta}})


def delete_book(db, isbn):
    """删除一本图书。"""
    return db.books.delete_one({"isbn": isbn})


def delete_books(db, query=None):
    """按条件批量删除。空条件直接拒绝，避免误删整个集合。"""
    if not query:
        raise ValueError("批量删除必须给条件，不能传空查询")
    return db.books.delete_many(query).deleted_count


def count_books(db, query=None):
    """统计图书数量。"""
    return db.books.count_documents(query or {})
