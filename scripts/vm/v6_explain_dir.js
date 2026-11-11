const lib = db.getSiblingDB("smartlib");
print("=== 定向查询（带分片键 reader_card + borrow_date）===");
print("条件: reader_card=R20240001, borrow_date>=2024-01-01");
const e = lib.borrow_logs.find({ reader_card: "R20240001", borrow_date: { $gte: ISODate("2024-01-01") } }).explain("executionStats");
print("  顶层 stage: " + e.queryPlanner.winningPlan.stage);
print("  参与分片数: " + (e.queryPlanner.winningPlan.shards ? e.queryPlanner.winningPlan.shards.length : 0));
print("  返回文档数: " + e.executionStats.nReturned);
