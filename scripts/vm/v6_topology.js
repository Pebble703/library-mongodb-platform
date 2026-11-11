const cfg = db.getSiblingDB("config");
print("=== 集群拓扑 ===");
cfg.shards.find().forEach(s => print("  分片: " + s._id + "  " + s.host));
cfg.mongos.find().forEach(m => print("  mongos: " + m._id));
const cs = db.adminCommand({ listShards: 1 });
print("分片总数: " + cs.shards.length);
const col = cfg.collections.findOne({ _id: "smartlib.borrow_logs" });
print("borrow_logs 已分片: 分片键=" + JSON.stringify(col.key));
