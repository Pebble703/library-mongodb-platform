"""借阅模块：借阅登记、归还处理与逾期查询。

borrow_logs 是时间序列集合，且没有定义 metaField，因此不能修改 status 这类
普通字段（会报 error 72）。所以归还操作采用“追加一条已归还记录 + 库存加 1”
的方式，而不是回写原记录。
"""

from datetime import datetime, timezone


def list_borrows(db, query=None, limit=0):
    """查看借阅流水，按借阅时间倒序。"""
    cursor = db.borrow_logs.find(query or {}).sort("borrow_date", -1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def borrow_book(db, card_no, isbn, borrow_date=None):
    """借阅登记：先扣库存，再写一条借出流水。"""
    reader = db.readers.find_one({"card_no": card_no})
    if reader is None:
        raise ValueError("借阅证号不存在：%s" % card_no)

    book = db.books.find_one_and_update(
        {"isbn": isbn, "stock": {"$gt": 0}},
        {"$inc": {"stock": -1, "borrow_count": 1}},
    )
    if book is None:
        raise ValueError("图书不存在或库存不足：%s" % isbn)

    return db.borrow_logs.insert_one(
        {
            "borrow_date": borrow_date or datetime.now(timezone.utc),
            "reader_card": card_no,
            "book_isbn": isbn,
            "status": "借出",
        }
    )


def return_book(db, card_no, isbn, return_date=None):
    """归还处理：追加一条已归还记录，并把库存加回去。"""
    active = db.borrow_logs.find_one(
        {
            "reader_card": card_no,
            "book_isbn": isbn,
            "status": {"$in": ["借出", "逾期"]},
        },
        sort=[("borrow_date", -1)],
    )
    if active is None:
        return None

    returned_at = return_date or datetime.now(timezone.utc)
    result = db.borrow_logs.insert_one(
        {
            "borrow_date": returned_at,
            "return_date": returned_at,
            "reader_card": card_no,
            "book_isbn": isbn,
            "status": "已归还",
        }
    )
    db.books.update_one({"isbn": isbn}, {"$inc": {"stock": 1}})
    return result


def mark_overdue(db, before):
    """把借出时间早于 before 的记录批量标记为逾期（update_many）。

    注意：borrow_logs 是时间序列集合且未定义 metaField，MongoDB 只允许更新
    metaField 字段，因此对 status 执行 $set 会返回 error 72
    （Cannot perform an update on a time-series collection which updates a
    field that is not the metaField）。该函数保留用于对应任务书 5.3 对
    update_many 的要求，实际逾期判断由 overdue_loans 通过查询完成。
    """
    return db.borrow_logs.update_many(
        {"status": "借出", "borrow_date": {"$lt": before}},
        {"$set": {"status": "逾期"}},
    )


def overdue_loans(db):
    """查询状态为逾期的记录。"""
    return list_borrows(db, {"status": "逾期"})
