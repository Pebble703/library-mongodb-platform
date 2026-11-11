const cfg = db.getSiblingDB("config");
const d = cfg.databases.findOne({ _id: "smartlib" });
const c = cfg.collections.findOne({ _id: "smartlib.borrow_logs" });
const chunks = cfg.chunks.countDocuments({ uuid: c.uuid });

print("数据库: smartlib    主分片: " + d.primary);
print("集合: borrow_logs");
print("分片键: " + JSON.stringify(c.key));
print("已分片: " + (c.key !== undefined) + "    chunk 数: " + chunks);
print("分片总数: " + db.adminCommand({ listShards: 1 }).shards.length);
