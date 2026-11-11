// 重建 borrow_logs：先分片、先切 chunk，再导入，保证两个分片各一半且无孤儿文档
const lib = db.getSiblingDB("smartlib");

lib.borrow_logs.drop();
print("已删除旧的 borrow_logs");

lib.createCollection("borrow_logs");
lib.borrow_logs.createIndex({ reader_card: 1, borrow_date: 1 }, { name: "idx_reader_date" });
lib.borrow_logs.createIndex({ book_isbn: 1, borrow_date: -1 }, { name: "idx_book_date" });
lib.borrow_logs.createIndex({ borrow_date: 1 }, { name: "idx_borrow_date" });
print("已重建集合与三个索引");

sh.shardCollection("smartlib.borrow_logs", { reader_card: 1, borrow_date: 1 });
print("已按 {reader_card:1, borrow_date:1} 分片");

const splitKey = { reader_card: "R20240016", borrow_date: ISODate("2023-01-01") };
sh.splitAt("smartlib.borrow_logs", splitKey);
sleep(2000);
sh.moveChunk("smartlib.borrow_logs", { reader_card: "R20240020", borrow_date: ISODate("2024-06-01") }, "shard2");
sleep(2000);

const chunks = db.getSiblingDB("config").chunks.find({}).sort({ min: 1 }).toArray();
print("当前 chunk 布局:");
chunks.forEach(c => print("  " + c.shard + "   " + JSON.stringify(c.min) + "  ->  " + JSON.stringify(c.max)));
