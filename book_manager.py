"""图书模块：馆藏检索、评分排行与库存维护。

对应任务三的检索需求：类别与价格区间组合、标签多选、书名模糊、
出版年份范围、缺少 tags 的数据质量核查、评分 Top10。
"""


def insert_book(db, book):
    return db.books.insert_one(book)


def search_category_price(db, category, price_min=None, price_max=None, limit=50):
    """按类别与价格区间组合筛选。"""
    query = {"category": category}
    if price_min is not None or price_max is not None:
        query["price"] = {}
        if price_min is not None:
            query["price"]["$gte"] = price_min
        if price_max is not None:
            query["price"]["$lte"] = price_max
    return list(db.books.find(query, {"_id": 0}).sort("price", 1).limit(limit))


def search_tags(db, tags, limit=50):
    """标签多选：同时包含指定的所有标签。"""
    return list(db.books.find({"tags": {"$all": tags}}, {"_id": 0}).limit(limit))


def search_title(db, keyword, limit=50):
    """书名模糊检索。"""
    return list(
        db.books.find({"title": {"$regex": keyword, "$options": "i"}}, {"_id": 0}).limit(limit)
    )


def search_year_range(db, year_from, year_to, limit=50):
    """出版年份范围检索，年份边界自动转成日期。"""
    from datetime import datetime

    start = datetime(year_from, 1, 1)
    end = datetime(year_to + 1, 1, 1)
    query = {"publish_date": {"$gte": start, "$lt": end}}
    return list(db.books.find(query, {"_id": 0}).sort("publish_date", 1).limit(limit))


def missing_tags(db):
    """缺少 tags 字段的图书，用于数据质量核查。"""
    return list(db.books.find({"tags": {"$exists": False}}, {"_id": 0}))


def top_rated(db, limit=10):
    """评分最高的若干本，只返回书名、作者、评分。"""
    projection = {"_id": 0, "isbn": 1, "title": 1, "author": 1, "rating": 1}
    cursor = db.books.find({}, projection).sort([("rating", -1), ("borrow_count", -1)])
    return list(cursor.limit(limit))


def get_book(db, isbn):
    return db.books.find_one({"isbn": isbn}, {"_id": 0})


def update_stock(db, isbn, delta):
    return db.books.update_one({"isbn": isbn}, {"$inc": {"stock": delta}})


def delete_book(db, isbn):
    return db.books.delete_one({"isbn": isbn})


def count_books(db, query=None):
    return db.books.count_documents(query or {})


def categories(db):
    return sorted(db.books.distinct("category"))

def update_book(db, isbn, fields):
    """通用更新：只允许修改业务字段，ISBN 作为主键不允许改。"""
    allowed = {"title", "author", "publisher", "category", "price", "stock",
               "rating", "tags", "publish_date", "location", "ebook_name", "borrow_count"}
    data = {k: v for k, v in fields.items() if k in allowed}
    if not data:
        raise ValueError("没有可更新的字段")
    return db.books.update_one({"isbn": isbn}, {"$set": data})


def list_page(db, query=None, page=1, size=10, sort=None):
    """分页浏览图书：返回总条数、总页数与当前页数据。"""
    query = query or {}
    size = max(1, size)
    total = db.books.count_documents(query)
    pages = max(1, (total + size - 1) // size)
    page = min(max(1, page), pages)
    cursor = (db.books.find(query, {"_id": 0, "isbn": 1, "title": 1, "author": 1, "category": 1, "price": 1, "stock": 1})
              .sort(sort or [("isbn", 1)])
              .skip((page - 1) * size)
              .limit(size))
    return {"total": total, "pages": pages, "page": page, "size": size, "rows": list(cursor)}
