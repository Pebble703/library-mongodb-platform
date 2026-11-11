const lib = db.getSiblingDB("smartlib");
print("=== 跨分片查询（完全不带分片键）===");
print("条件: status=逾期");
const e = lib.borrow_logs.find({ status: "逾期" }).explain("executionStats");
print("  顶层 stage: " + e.queryPlanner.winningPlan.stage);
print("  参与分片数: " + (e.queryPlanner.winningPlan.shards ? e.queryPlanner.winningPlan.shards.length : 0));
print("  返回文档数: " + e.executionStats.nReturned);
