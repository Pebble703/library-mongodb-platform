const cfg = db.getSiblingDB("config");
print("collections 文档:");
cfg.collections.find().forEach(c => print("  " + c._id + "  key=" + JSON.stringify(c.key) + "  dropped=" + c.dropped + "  uuid=" + c.uuid));
print("chunks 总数: " + cfg.chunks.countDocuments({}));
print("shards: " + cfg.shards.countDocuments({}));
print("mongos: " + cfg.mongos.countDocuments({}));
