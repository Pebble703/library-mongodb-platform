db.books.updateOne({ isbn: "RS-VM-001" }, { $set: { title: "虚拟机副本集写入验证", price: 1, stock: 1 } }, { upsert: true });
print("写入成功，books 总数 = " + db.books.countDocuments());
