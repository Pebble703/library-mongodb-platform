const lib = db.getSiblingDB("smartlib");

print("=== 定向查询：带完整分片键（reader_card + borrow_date）===");
const e1 = lib.borrow_logs.find({ reader_card: "R20240001", borrow_date: { $gte: ISODate("2024-01-01") } }).explain("executionStats");
print("  顶层 stage: " + e1.queryPlanner.winningPlan.stage);
print("  参与分片数: " + (e1.queryPlanner.winningPlan.shards ? e1.queryPlanner.winningPlan.shards.length : 0));
print("  返回文档数: " + e1.executionStats.nReturned);

print("=== 跨分片查询：不带分片键（按状态）===");
const e2 = lib.borrow_logs.find({ status: "逾期" }).explain("executionStats");
print("  顶层 stage: " + e2.queryPlanner.winningPlan.stage);
print("  参与分片数: " + (e2.queryPlanner.winningPlan.shards ? e2.queryPlanner.winningPlan.shards.length : 0));
print("  返回文档数: " + e2.executionStats.nReturned);
