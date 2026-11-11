#!/bin/bash
set -e
mkdir -p ~/single/db
pkill -f "port 27017" 2>/dev/null || true
sleep 1
mongod --port 27017 --dbpath ~/single/db --logpath ~/single/mongod.log \
       --bind_ip 192.168.78.128,127.0.0.1 --auth --fork
sleep 3
pgrep -a mongod | grep 27017
