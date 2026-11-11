const h = db.hello();
print("连接节点: " + h.me);
print("是否主节点: " + h.isWritablePrimary);
print("读到 RS-VM-001 条数: " + db.books.countDocuments({ isbn: "RS-VM-001" }));
print("books 总数: " + db.books.countDocuments());
