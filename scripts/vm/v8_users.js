const admin = db.getSiblingDB("admin");
try { admin.createUser({ user: "root", pwd: "Root2026", roles: ["root"] }); print("root created"); }
catch (e) { print("root: " + e.message); }
admin.auth("root", "Root2026");
const lib = db.getSiblingDB("smartlib");
[["app_rw", "App2026", "readWrite"], ["app_ro", "Ro2026", "read"]].forEach(function (t) {
  try { lib.createUser({ user: t[0], pwd: t[1], roles: [{ role: t[2], db: "smartlib" }] }); print("created " + t[0]); }
  catch (e) { print(t[0] + ": " + e.message); }
});
print("users: " + lib.getUsers().users.map(u => u.user).join(","));
