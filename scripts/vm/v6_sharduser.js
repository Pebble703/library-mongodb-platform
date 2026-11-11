const admin = db.getSiblingDB("admin");
try { admin.createUser({ user: "root", pwd: "Root2026", roles: ["root"] }); print("分片本地 root 已创建"); }
catch (e) { print("已存在: " + e.message); }
