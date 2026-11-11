#!/bin/bash
# 在 Ubuntu 18.04 上把 MongoDB 3.6 换成 6.0（18.04 支持的最高大版本）
set -e
export DEBIAN_FRONTEND=noninteractive

echo "== 1. 卸载旧版 3.6 =="
apt-get remove -y --purge mongodb-server mongodb-server-core mongodb-clients mongo-tools || true
apt-get autoremove -y || true
pkill mongod || true
sleep 1

echo "== 2. 添加 6.0 官方源 =="
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/6.0 multiverse" \
  > /etc/apt/sources.list.d/mongodb-org-6.0.list
apt-get update -qq

echo "== 3. 安装 mongodb-org =="
apt-get install -y mongodb-org

echo "== 4. 尝试安装 mongosh =="
apt-get install -y mongodb-mongosh || echo "mongodb-mongosh 包不可用，稍后单独处理"

echo "== 5. 停掉默认实例（集群用自定义目录与端口）=="
systemctl stop mongod 2>/dev/null || true
systemctl disable mongod 2>/dev/null || true

echo "== 6. 版本 =="
mongod --version | head -1
command -v mongosh >/dev/null && mongosh --version || echo "mongosh 未安装"

echo "SETUP_DONE"
