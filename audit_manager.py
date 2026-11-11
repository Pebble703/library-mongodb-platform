"""操作日志模块：新增、删除、导出等关键操作写入 audit_logs。

audit_logs 使用固定集合（capped），只追加不修改，超过容量后旧记录自动淘汰，
正好满足「按时间倒序查询最近 100 条操作」的需求。
"""

from datetime import datetime, timezone


def log(db, action, collection, doc_id=None, detail=None, operator="app_rw"):
    """写一条操作日志。

    action：操作类型，如 insert / delete / export / upload；
    collection：涉及的对象，如 books；
    doc_id：受影响文档的主键；detail：补充信息（字典）。
    """
    record = {
        "ts": datetime.now(timezone.utc),
        "action": action,
        "collection": collection,
        "doc_id": str(doc_id) if doc_id is not None else None,
        "operator": operator,
        "detail": detail or {},
    }
    return db.audit_logs.insert_one(record)


def recent(db, limit=100):
    """按时间倒序取最近若干条日志。"""
    cursor = db.audit_logs.find({}, {"_id": 0}).sort("ts", -1).limit(limit)
    return list(cursor)


def count(db):
    return db.audit_logs.count_documents({})


def stats_by_action(db):
    """按操作类型统计条数，用于演示日志分布。"""
    pipeline = [
        {"$group": {"_id": "$action", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]
    return list(db.audit_logs.aggregate(pipeline))
