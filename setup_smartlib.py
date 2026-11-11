"""智慧图书馆数字资源平台：建库、建索引、导入数据、上传 GridFS。

用法：
    python setup_smartlib.py            # 增量导入，已存在则跳过
    python setup_smartlib.py --reset    # 先删除 smartlib 数据库再重建

数据文件放在 data/ 下，电子书与封面在 data/gridfs_files/ 下。
导入时把 JSON 中的 ISO 日期字符串转换成 BSON Date 类型。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from mongodb_connect import DATABASE_NAME, get_client

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
FILES = DATA / "gridfs_files"

# 导入后必须对上的基线，任何一项不符就报错退出
EXPECTED = {
    "books": 50,
    "readers": 30,
    "borrow_logs": 3000,
    "books_without_tags": 4,
    "books_with_ebook": 3,
    "readers_without_fav": 2,
    "readers_email_null": 5,
    "logs_returned": 2142,
    "logs_borrowed": 429,
    "logs_overdue": 429,
    "gridfs_files": 6,
}


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def to_date(value):
    """ISO 字符串转 datetime，已经是 Date 的原样返回。"""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def create_collections(db):
    existing = set(db.list_collection_names())
    created = {}

    for name in ("books", "readers", "borrow_logs", "category_stats"):
        if name not in existing:
            db.create_collection(name)
            created[name] = "created"
        else:
            created[name] = "existing"

    # 操作日志用固定集合：只追加、自动淘汰旧记录
    if "audit_logs" not in existing:
        db.create_collection("audit_logs", capped=True, size=16 * 1024 * 1024, max=100000)
        created["audit_logs"] = "created capped 16MB/100000"
    else:
        created["audit_logs"] = "existing"

    return created


def create_indexes(db):
    result = {}
    result["books.isbn"] = db.books.create_index([("isbn", 1)], unique=True, name="uniq_isbn")
    result["books.category_price"] = db.books.create_index(
        [("category", 1), ("price", 1)], name="idx_category_price"
    )
    result["books.tags"] = db.books.create_index([("tags", 1)], name="idx_tags")
    result["books.rating"] = db.books.create_index([("rating", -1)], name="idx_rating")
    result["books.publish_date"] = db.books.create_index([("publish_date", 1)], name="idx_publish_date")

    result["readers.card_no"] = db.readers.create_index([("card_no", 1)], unique=True, name="uniq_card_no")
    result["readers.college"] = db.readers.create_index([("college", 1)], name="idx_college")

    result["borrow_logs.reader_date"] = db.borrow_logs.create_index(
        [("reader_card", 1), ("borrow_date", 1)], name="idx_reader_date"
    )
    result["borrow_logs.book_date"] = db.borrow_logs.create_index(
        [("book_isbn", 1), ("borrow_date", -1)], name="idx_book_date"
    )
    result["borrow_logs.date"] = db.borrow_logs.create_index([("borrow_date", 1)], name="idx_borrow_date")

    result["audit_logs.ts"] = db.audit_logs.create_index([("ts", -1)], name="idx_ts")
    return result


def import_books(db):
    docs = load_json("books.txt")
    for doc in docs:
        doc["publish_date"] = to_date(doc["publish_date"])
    if db.books.count_documents({}) == 0:
        db.books.insert_many(docs)
    return len(docs)


def import_readers(db):
    docs = load_json("readers.txt")
    for doc in docs:
        doc["register_date"] = to_date(doc["register_date"])
    if db.readers.count_documents({}) == 0:
        db.readers.insert_many(docs)
    return len(docs)


def import_borrow_logs(db):
    docs = load_json("borrow_logs.txt")
    for doc in docs:
        doc["borrow_date"] = to_date(doc["borrow_date"])
        if "return_date" in doc:
            doc["return_date"] = to_date(doc["return_date"])
    if db.borrow_logs.count_documents({}) == 0:
        # 三千条分批写入，避免单次请求过大
        for i in range(0, len(docs), 500):
            db.borrow_logs.insert_many(docs[i:i + 500])
    return len(docs)


def upload_gridfs(db):
    import gridfs_manager

    if db.fs.files.count_documents({}) > 0:
        return db.fs.files.count_documents({})
    uploaded = gridfs_manager.upload_manifest(db, FILES)
    return len(uploaded)


def verify(db):
    checks = {
        "books": db.books.count_documents({}),
        "readers": db.readers.count_documents({}),
        "borrow_logs": db.borrow_logs.count_documents({}),
        "books_without_tags": db.books.count_documents({"tags": {"$exists": False}}),
        "books_with_ebook": db.books.count_documents({"ebook_name": {"$exists": True}}),
        "readers_without_fav": db.readers.count_documents({"fav_categories": {"$exists": False}}),
        "readers_email_null": db.readers.count_documents({"email": None}),
        "logs_returned": db.borrow_logs.count_documents({"status": "已归还"}),
        "logs_borrowed": db.borrow_logs.count_documents({"status": "借出"}),
        "logs_overdue": db.borrow_logs.count_documents({"status": "逾期"}),
        "gridfs_files": db.fs.files.count_documents({}),
    }
    bad = {k: (checks[k], EXPECTED[k]) for k in EXPECTED if checks[k] != EXPECTED[k]}
    return checks, bad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="先删除 smartlib 数据库")
    args = parser.parse_args()

    client = get_client()
    try:
        if args.reset:
            client.drop_database(DATABASE_NAME)
            print("已删除数据库", DATABASE_NAME)

        db = client[DATABASE_NAME]
        print("集合：", create_collections(db))
        print("索引：", create_indexes(db))
        print("导入 books：", import_books(db))
        print("导入 readers：", import_readers(db))
        print("导入 borrow_logs：", import_borrow_logs(db))
        print("上传 GridFS：", upload_gridfs(db))

        checks, bad = verify(db)
        print("\n核对结果：")
        for key, value in checks.items():
            flag = "OK" if value == EXPECTED.get(key, value) else "期望 %s" % EXPECTED[key]
            print("  %-22s %-6s %s" % (key, value, flag))

        if bad:
            raise SystemExit("数据与基线不一致，请检查：%s" % bad)
        print("\n全部核对通过。")
    finally:
        client.close()


if __name__ == "__main__":
    main()
