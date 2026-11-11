// 三节点副本集初始化（在 nosql1 上执行）
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "192.168.78.128:27018", priority: 2 },
    { _id: 1, host: "192.168.78.129:27018", priority: 1 },
    { _id: 2, host: "192.168.78.130:27018", priority: 1 }
  ]
});

sleep(9000);

const s = rs.status();
print("set=" + s.set);
s.members.forEach(m => print("  " + m.name + "   " + m.stateStr + "   health=" + m.health));
const h = db.hello();
print("primary=" + h.primary);
