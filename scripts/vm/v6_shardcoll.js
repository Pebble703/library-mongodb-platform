sh.enableSharding("smartlib");

const lib = db.getSiblingDB("smartlib");

// 索引已由 setup 脚本创建（名字 idx_reader_date），这里只校验
lib.borrow_logs.createIndex({ reader_card: 1, borrow_date: 1 }, { name: "idx_reader_date" });
print("索引已就绪: " + JSON.stringify(lib.borrow_logs.getIndexes().map(i => i.name)));

sh.shardCollection("smartlib.borrow_logs", { reader_card: 1, borrow_date: 1 });
print("borrow_logs 已按 {reader_card:1, borrow_date:1} 分片");

sleep(3000);
const c = db.getSiblingDB("config").collections.findOne({ _id: "smartlib.borrow_logs" });
print("配置库记录: " + JSON.stringify(c.key) + "  已分区=" + c.partitioned);
