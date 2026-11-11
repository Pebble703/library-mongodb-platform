"""借阅模块：借阅登记、归还处理与逾期查询。

borrow_logs 按任务二的设计使用普通集合（便于按 status 更新、便于后续分片），
因此归还可以直接回写状态，不需要像时间序列集合那样只能追加。
"""

from datetime import datetime, timedelta, timezone


def borrow_book(db, card_no, isbn, borrow_date=None, duration_days=30):
    """借阅登记：校验读者与库存，扣减库存后写一条借出流水。"""
    reader = db.readers.find_one({"card_no": card_no})
    if reader is None:
        raise ValueError("借阅证号不存在：%s" % card_no)

    book = db.books.find_one_and_update(
        {"isbn": isbn, "stock": {"$gt": 0}},
        {"$inc": {"stock": -1, "borrow_count": 1}},
    )
    if book is None:
        raise ValueError("图书不存在或库存为 0：%s" % isbn)

    borrowed_at = borrow_date or datetime.now(timezone.utc)
    return db.borrow_logs.insert_one(
        {
            "borrow_date": borrowed_at,
            "reader_card": card_no,
            "book_isbn": isbn,
            "status": "借出",
            "duration_days": duration_days,
        }
    )


def return_book(db, card_no, isbn, return_date=None):
    """归还：找到最近一条未归还记录，回写状态与归还时间，并恢复库存。"""
    loan = db.borrow_logs.find_one(
        {"reader_card": card_no, "book_isbn": isbn, "status": {"$in": ["借出", "逾期"]}},
        sort=[("borrow_date", -1)],
    )
    if loan is None:
        return None

    returned_at = return_date or datetime.now(timezone.utc)
    duration = (returned_at - loan["borrow_date"].replace(tzinfo=timezone.utc)).days
    result = db.borrow_logs.update_one(
        {"_id": loan["_id"]},
        {"$set": {"status": "已归还", "return_date": returned_at, "duration_days": max(duration, 0)}},
    )
    db.books.update_one({"isbn": isbn}, {"$inc": {"stock": 1}})
    return result


def mark_overdue(db, days=30):
    """把超过借期仍未归还的记录标记为逾期。"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return db.borrow_logs.update_many(
        {"status": "借出", "borrow_date": {"$lt": cutoff}},
        {"$set": {"status": "逾期"}},
    )


def overdue_loans(db, limit=0):
    """查询逾期记录。"""
    cursor = db.borrow_logs.find({"status": "逾期"}).sort("borrow_date", -1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def list_borrows(db, query=None, limit=20):
    cursor = db.borrow_logs.find(query or {}).sort("borrow_date", -1).limit(limit)
    return list(cursor)
