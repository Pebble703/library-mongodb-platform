#!/bin/bash
# nosql1：启动配置服务器（27019）并初始化 cfgrs
set -e
mkdir -p ~/cfg/db
pkill -f "port 27019" 2>/dev/null || true
sleep 1
mongod --configsvr --replSet cfgrs --port 27019 \
       --dbpath ~/cfg/db --logpath ~/cfg/mongod.log \
       --bind_ip 192.168.78.128,127.0.0.1 --keyFile ~/rs/keyfile --fork
sleep 3
mongosh --port 27019 --quiet --eval 'rs.initiate({_id:"cfgrs", configsvr:true, members:[{_id:0, host:"192.168.78.128:27019"}]})' || true
sleep 5
mongosh --port 27019 --quiet --eval 'print("configsvr 状态: " + rs.status().myState)'
