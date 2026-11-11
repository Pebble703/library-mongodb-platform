#!/bin/bash
# nosql1：启动 mongos（27022）
set -e
pkill -f "port 27022" 2>/dev/null || true
sleep 1
mongos --configdb cfgrs/192.168.78.128:27019 \
       --port 27022 --bind_ip 192.168.78.128,127.0.0.1 \
       --logpath ~/mongos.log --keyFile ~/rs/keyfile --fork
sleep 4
pgrep -a mongos
