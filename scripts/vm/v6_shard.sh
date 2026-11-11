#!/bin/bash
# nosql2/nosql3：启动分片实例（单节点副本集）
# 用法：v6_shard.sh <端口> <本机IP> <副本集名>
set -e
PORT=$1
IP=$2
RS=$3
mkdir -p ~/shard/db
pkill -f "port $PORT" 2>/dev/null || true
sleep 1
mongod --shardsvr --replSet "$RS" --port "$PORT" \
       --dbpath ~/shard/db --logpath ~/shard/mongod.log \
       --bind_ip "$IP,127.0.0.1" --keyFile ~/rs/keyfile --fork
sleep 3
mongosh --port "$PORT" --quiet --eval "rs.initiate({_id:'$RS', members:[{_id:0, host:'$IP:$PORT'}]})" || true
sleep 6
mongosh --port "$PORT" --quiet --eval "print('$RS 角色: ' + rs.status().myState + ' (1=PRIMARY)')"
pgrep -a mongod
