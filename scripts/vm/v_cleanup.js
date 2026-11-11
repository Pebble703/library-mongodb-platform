db.books.deleteOne({ isbn: "RS-VM-001" });
print("books 恢复为 " + db.books.countDocuments());
try { rs.remove("192.168.78.128:27019"); } catch (e) { print("remove: " + e.message); }
sleep(4000);
print("成员数: " + rs.status().members.length);
rs.status().members.forEach(m => print("  " + m.name + "  " + m.stateStr));
