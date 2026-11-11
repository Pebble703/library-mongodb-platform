const cfg = db.getSiblingDB("config");
const lib = db.getSiblingDB("smartlib");

print("mongos 视角 borrow_logs 总数: " + lib.borrow_logs.countDocuments());

const col = cfg.collections.findOne({ _id: "smartlib.borrow_logs" });
print("集合元数据: " + (col ? ("分片键=" + JSON.stringify(col.key) + " uuid=" + col.uuid) : "不存在"));

const total = cfg.chunks.countDocuments({ ns: "smartlib.borrow_logs" });
print("chunk 总数(按 ns): " + total);

const list = cfg.chunks.find({ ns: "smartlib.borrow_logs" }, { shard: 1, min: 1, max: 1 }).limit(8).toArray();
list.forEach(c => print("  " + c.shard + "   " + JSON.stringify(c.min) + "  ->  " + JSON.stringify(c.max)));
