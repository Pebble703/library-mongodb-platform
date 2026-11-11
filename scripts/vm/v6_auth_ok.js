const c = db.runCommand({ connectionStatus: 1 });
print("认证用户: " + c.authInfo.authenticatedUsers.map(u => u.user + "@" + u.db).join(","));
print("角色: " + c.authInfo.authenticatedUserRoles.map(r => r.role).join(","));
print("分片数: " + db.adminCommand({ listShards: 1 }).shards.length);
