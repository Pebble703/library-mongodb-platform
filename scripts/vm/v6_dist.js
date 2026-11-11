const lib = db.getSiblingDB("smartlib");
print("borrow_logs 总数: " + lib.borrow_logs.countDocuments());
lib.borrow_logs.getShardDistribution();
