sh.enableSharding("smartlib");
const d = db.getSiblingDB("config").databases.findOne({ _id: "smartlib" });
print("partitioned = " + d.partitioned + "  主分片 = " + d.primary);
const c = db.getSiblingDB("config").collections.findOne({ _id: "smartlib.borrow_logs" });
print("集合分片键 = " + JSON.stringify(c.key));
print("chunk 数 = " + db.getSiblingDB("config").chunks.countDocuments({ uuid: c.uuid }));
