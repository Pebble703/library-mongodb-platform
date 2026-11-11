echo "== nosql1 =="
ps -eo args | grep -E "mongod|mongos" | grep -v grep | cut -c1-110
echo ""
echo "== 监听端口 =="
ss -lnt | grep -E "2701[89]|2702[0-2]" | awk '{print $4}'
