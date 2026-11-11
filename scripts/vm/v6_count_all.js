print("mongos 汇总 borrow_logs = " + db.getSiblingDB("smartlib").borrow_logs.countDocuments());
print("分片数 = " + db.adminCommand({ listShards: 1 }).shards.length);
