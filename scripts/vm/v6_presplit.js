// 空集合上先切分并迁移 chunk，再导入数据：无数据迁移，不会产生孤儿文档
const cfg = db.getSiblingDB("config");
const NS = "smartlib.borrow_logs";

sh.splitAt(NS, { reader_card: "R20240016", borrow_date: ISODate("2023-01-01") });
sleep(1000);
print("切分后 chunk 数: " + cfg.chunks.countDocuments({ ns: NS }));

sh.moveChunk(NS, { reader_card: "R20240020", borrow_date: ISODate("2024-06-01") }, "shard2");
sleep(1000);

const chunks = cfg.chunks.find({ ns: NS }, { shard: 1, min: 1, max: 1 }).sort({ min: 1 }).toArray();
print("迁移后 chunk 数: " + chunks.length);
chunks.forEach(c => print("  " + c.shard + "   " + JSON.stringify(c.min) + "  ->  " + JSON.stringify(c.max)));
