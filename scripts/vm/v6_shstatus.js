const r = db.adminCommand({ listShards: 1 });
print("分片数: " + r.shards.length);
r.shards.forEach(s => print("  " + s._id + "   " + s.host));

const dbs = db.getSiblingDB("config").databases.find({ name: "smartlib" }).toArray();
dbs.forEach(d => print("smartlib: 主分片=" + d.primary + "  已分区=" + (d.partitioned ? "是" : "否")));

const cols = db.getSiblingDB("config").collections.find({ _id: /smartlib/ }).toArray();
cols.forEach(c => print("已分片集合: " + c._id + "  分片键=" + JSON.stringify(c.key)));
