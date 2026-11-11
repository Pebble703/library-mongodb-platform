#!/bin/bash
# 在 nosql1 上再加一个节点 27023，加入副本集 rs0
PORT=27023
if pgrep -f "port $PORT" > /dev/null; then
  echo "27023 已在运行"
else
  mkdir -p ~/rs/db4
  mongod --replSet rs0 --port $PORT --dbpath ~/rs/db4 \
         --logpath ~/rs/mongod4.log --bind_ip 192.168.78.128,127.0.0.1 \
         --keyFile ~/rs/keyfile --fork > /dev/null 2>&1
  sleep 3
fi

URI="mongodb://root:Root2026@127.0.0.1:27018/admin?authSource=admin&replicaSet=rs0"
mongosh "$URI" --quiet --eval 'try { rs.remove("192.168.78.128:27023") } catch (e) {}' > /dev/null 2>&1
sleep 2
echo "== 新增第四个节点 192.168.78.128:27023 =="
mongosh "$URI" --quiet --eval 'const r = rs.add("192.168.78.128:27023"); print("加入结果 ok=" + r.ok)'
sleep 8
echo "== 当前成员 =="
mongosh "$URI" --quiet --eval 'rs.status().members.forEach(m => print("  " + m.name + "  " + m.stateStr))'