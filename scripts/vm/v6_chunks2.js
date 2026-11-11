const cfg = db.getSiblingDB("config");
const col = cfg.collections.findOne({ _id: "smartlib.borrow_logs" });
const chunks = cfg.chunks.find({ uuid: col.uuid }).sort({ min: 1 }).toArray();
print("分片键: " + JSON.stringify(col.key));
print("chunk 数: " + chunks.length);
chunks.forEach(c => print("  " + c.shard + "   " + JSON.stringify(c.min) + "  ->  " + JSON.stringify(c.max)));
