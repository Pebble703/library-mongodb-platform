print("清理前: " + db.borrow_logs.countDocuments());
const r = db.adminCommand({ cleanupOrphaned: "smartlib.borrow_logs" });
print("cleanupOrphaned 结果: " + JSON.stringify(r).substring(0, 200));
sleep(3000);
print("清理后: " + db.borrow_logs.countDocuments());
