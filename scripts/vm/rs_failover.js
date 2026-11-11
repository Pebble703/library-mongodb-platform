function roles(){ return rs.status().members.map(m => m.name + "=" + m.stateStr).join("  "); }
print("== 操作前 ==");
print("时间: " + new Date().toISOString());
print("角色: " + roles());
print("主节点: " + db.hello().primary);
print("");
print("== 执行 rs.stepDown(60) ==");
try { rs.stepDown(60); } catch (e) { print("stepDown 返回: " + e.message); }
sleep(15000);
print("");
print("== 15 秒后 ==");
print("时间: " + new Date().toISOString());
const s = rs.status();
print("角色: " + s.members.map(m => m.name + "=" + m.stateStr).join("  "));
s.members.forEach(m => { if (m.stateStr === "PRIMARY") print("新主节点: " + m.name + "   选举时间: " + m.electionDate); });
