db.borrow_logs.deleteMany({ borrow_date: { $gt: ISODate("2026-01-01") } });
db.fs.files.drop(); db.fs.chunks.drop(); db.category_stats.drop();
print("logs=" + db.borrow_logs.countDocuments({}));
