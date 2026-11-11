// 在 mongos 上建管理员并加入两个分片
const admin = db.getSiblingDB("admin");
try {
  admin.createUser({ user: "root", pwd: "Root2026", roles: ["root"] });
  print("root created");
} catch (e) {
  print("root: " + e.message);
}
admin.auth("root", "Root2026");

sh.addShard("shard1/192.168.78.129:27020");
sh.addShard("shard2/192.168.78.130:27021");
print("分片加入完成");
