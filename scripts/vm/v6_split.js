// 3000 条数据远小于 chunk 上限（128MB），自动均衡器不会切分，这里手动切分并迁移
const lib = db.getSiblingDB("smartlib");
const cfg = db.getSiblingDB("config");

const mid = lib.borrow_logs
  .find({}, { reader_card: 1, borrow_date: 1 })
  .sort({ reader_card: 1, borrow_date: 1 })
  .skip(1500)
  .limit(1)
  .toArray()[0];

print("第 1501 条（切分点）: " + JSON.stringify(mid));

sh.splitAt("smartlib.borrow_logs", { reader_card: mid.reader_card, borrow_date: mid.borrow_date });
sleep(4000);

let chunks = cfg.chunks.find({}).sort({ min: 1 }).toArray();
print("切分后 chunk 数: " + chunks.length);
chunks.forEach(c => print("  " + c.shard + "   " + JSON.stringify(c.min) + "  ->  " + JSON.stringify(c.max)));

sh.moveChunk("smartlib.borrow_logs", { reader_card: mid.reader_card, borrow_date: mid.borrow_date }, "shard2");
sleep(4000);

chunks = cfg.chunks.find({}).sort({ min: 1 }).toArray();
print("");
print("迁移后 chunk 数: " + chunks.length);
chunks.forEach(c => print("  " + c.shard + "   " + JSON.stringify(c.min) + "  ->  " + JSON.stringify(c.max)));
