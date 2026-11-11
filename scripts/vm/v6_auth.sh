echo "== 错误密码应被拒绝 =="
mongosh "mongodb://root:WrongPwd@127.0.0.1:27022/admin?authSource=admin" --quiet --eval 'db.runCommand({ping:1})' 2>&1 | head -3
echo ""
echo "== 正确密码认证成功 =="
mongosh "mongodb://root:Root2026@127.0.0.1:27022/admin?authSource=admin" --quiet --eval 'const c=db.runCommand({connectionStatus:1}); print("认证用户: " + c.authInfo.authenticatedUsers.map(u=>u.user+"@"+u.db).join(",")); print("角色: " + c.authInfo.authenticatedUserRoles.map(r=>r.role).join(",")); print("分片数: " + db.adminCommand({listShards:1}).shards.length)'
