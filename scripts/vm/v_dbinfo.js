const cfg = db.getSiblingDB("config");
const d = cfg.databases.findOne({ _id: "smartlib" });
printjson(d);
