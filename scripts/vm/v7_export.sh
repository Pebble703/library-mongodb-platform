mkdir -p ~/exports
mongoexport --uri="mongodb://root:Root2026@127.0.0.1:27022/smartlib?authSource=admin" --collection=category_stats --type=json --out=/home/guohanming/exports/category_stats.json
mongoexport --uri="mongodb://root:Root2026@127.0.0.1:27022/smartlib?authSource=admin" --collection=books --type=json --out=/home/guohanming/exports/books.json
echo "== 导出结果 =="
ls -lh /home/guohanming/exports
echo "== category_stats 内容 =="
cat /home/guohanming/exports/category_stats.json