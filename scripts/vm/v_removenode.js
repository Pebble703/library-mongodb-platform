try { rs.remove("192.168.78.128:27023"); print("已移除 27023"); }
catch (e) { print("无该节点"); }
print("成员数 " + rs.status().members.length);
