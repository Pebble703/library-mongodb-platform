"""建库脚本：创建集合、建立索引，并把 data 目录下的三个数据集导入。

用法：
    python setup_library.py
"""

from pathlib import Path

from bson import json_util

from mongodb_connect import DATABASE_NAME, get_client
from stat_manager import collection_counts, save_category_statistics

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"


def load(name):
    """读取 Extended JSON 文件，$date 会还原成 Date 类型。"""
    return json_util.loads((DATA / name).read_text(encoding="utf-8-sig"))


def create_collections(db):
    """按任务二的要求建立六个对象，已存在则跳过。"""
    existing = db.list_collection_names()
    if "book_logs" not in existing:
        db.create_collection("book_logs", capped=True, size=1048576, max=1000)
    if "borrow_logs" not in existing:
        db.create_collection(
            "borrow_logs",
            timeseries={"timeField": "borrow_date", "granularity": "hours"},
            expireAfterSeconds=63072000,
        )
    for name in ("books", "readers", "category_stats"):
        if name not in existing:
            db.create_collection(name)
    if "book_in_stock" not in existing:
        db.create_collection(
            "book_in_stock",
            viewOn="books",
            pipeline=[{"$match": {"stock": {"$gt": 0}}}],
        )


def create_indexes(db):
    """建立任务四要求的五个索引，另加读者的证号唯一索引。"""
    db.books.create_index([("isbn", 1)], unique=True, name="uniq_isbn")
    db.books.create_index([("title", 1)], name="idx_title")
    db.books.create_index([("category", 1)], name="idx_category")
    db.books.create_index([("tags", 1)], name="idx_tags_multikey")
    db.books.create_index([("category", 1), ("price", 1)], name="idx_category_price")
    db.readers.create_index([("card_no", 1)], unique=True, name="uniq_card_no")


def import_data(db):
    """集合为空时才导入，避免重复插入。"""
    mapping = {
        "books.txt": "books",
        "readers.txt": "readers",
        "borrow_logs.txt": "borrow_logs",
    }
    for file_name, collection_name in mapping.items():
        if db[collection_name].count_documents({}) == 0:
            docs = load(file_name)
            db[collection_name].insert_many(docs)
            print("%s 导入 %d 条" % (collection_name, len(docs)))
        else:
            print("%s 已有数据，跳过导入" % collection_name)


def main():
    client = get_client()
    try:
        db = client[DATABASE_NAME]
        create_collections(db)
        create_indexes(db)
        import_data(db)
        save_category_statistics(db)
        print("各集合文档数：", collection_counts(db))
    finally:
        client.close()


if __name__ == "__main__":
    main()
