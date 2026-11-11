#!/bin/bash
# 启动副本集节点：rs_start.sh <本机IP>
set -e
IP=$1
mkdir -p ~/rs/db
pkill -f "port 27018" 2>/dev/null || true
sleep 1
mongod --replSet rs0 --port 27018 \
       --dbpath ~/rs/db --logpath ~/rs/mongod.log \
       --bind_ip "$IP,127.0.0.1" --keyFile ~/rs/keyfile --fork
sleep 2
pgrep -a mongod
