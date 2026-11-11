const r = db.borrow_logs.deleteMany({ borrow_date: { $gt: ISODate("2026-01-01") } });
print("删除测试流水: " + r.deletedCount);
print("borrow_logs = " + db.borrow_logs.countDocuments({}));
print("gridfs = " + db.fs.files.countDocuments({}));
