db.fs.files.drop();
db.fs.chunks.drop();
db.category_stats.drop();
print("gridfs=" + db.fs.files.countDocuments({}) + "  category_stats=" + db.category_stats.countDocuments({}));
