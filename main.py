"""主程序：菜单式交互，把各个功能模块串起来。

用法：
    python main.py          交互菜单
    python main.py --demo   先打印连接信息和四项统计，方便截图
"""

import sys

from bson import json_util

import book_manager
import borrow_manager
import reader_manager
import stat_manager
from mongodb_connect import check_connection, get_client


def show(value):
    """统一按 JSON 格式打印，中文不转义。"""
    print(json_util.dumps(value, ensure_ascii=False, indent=2))


def print_startup(db):
    print("=== 图书情报检索与统计平台 ===")
    show(check_connection())
    print("集合文档数：")
    for name, count in stat_manager.collection_counts(db).items():
        print("  %s: %s" % (name, count))


def run_demo(db):
    """非交互演示，一次跑完五项统计。"""
    print("\n[演示] 评分前 5 图书")
    show(book_manager.top_rated(db))
    print("\n[演示] 畅销榜")
    show(stat_manager.best_sellers(db))
    print("\n[演示] 分类统计")
    show(stat_manager.category_statistics(db))
    print("\n[演示] 借阅趋势")
    show(stat_manager.borrow_trend(db))
    print("\n[演示] 活跃读者")
    show(stat_manager.reader_top5(db))


def ask_number(prompt):
    """读入一个数字，直接回车表示不限制。"""
    text = input(prompt).strip()
    return float(text) if text else None


def interactive(db):
    while True:
        print(
            "\n菜单：\n"
            "1. 图书条件检索\n"
            "2. 评分排行\n"
            "3. 分类统计\n"
            "4. 借阅趋势\n"
            "5. 活跃读者榜\n"
            "6. 借阅登记\n"
            "7. 图书归还\n"
            "8. 调整库存\n"
            "9. 逾期记录\n"
            "10. 读者学院统计\n"
            "0. 退出"
        )
        choice = input("请选择：").strip()

        try:
            if choice == "0":
                print("数据库连接已关闭，程序退出。")
                return

            elif choice == "1":
                keyword = input("书名或作者关键词（可空）：").strip() or None
                category = input("类别（可空）：").strip() or None
                price_min = ask_number("最低价格（可空）：")
                price_max = ask_number("最高价格（可空）：")
                rows = book_manager.search_books(
                    db,
                    keyword=keyword,
                    category=category,
                    price_min=price_min,
                    price_max=price_max,
                )
                print("共 %d 条" % len(rows))
                if rows:
                    show(rows)
                else:
                    print("没有符合条件的图书。")

            elif choice == "2":
                show(book_manager.top_rated(db))

            elif choice == "3":
                show(stat_manager.category_statistics(db))

            elif choice == "4":
                show(stat_manager.borrow_trend(db))

            elif choice == "5":
                show(stat_manager.reader_top5(db))

            elif choice == "6":
                card_no = input("借阅证号：").strip()
                isbn = input("ISBN：").strip()
                borrow_manager.borrow_book(db, card_no, isbn)
                print("借阅登记成功，新增文档数：1")

            elif choice == "7":
                card_no = input("借阅证号：").strip()
                isbn = input("ISBN：").strip()
                result = borrow_manager.return_book(db, card_no, isbn)
                if result is None:
                    print("没有找到该读者的未归还记录。")
                else:
                    print("归还成功，新增文档数：1")

            elif choice == "8":
                isbn = input("ISBN：").strip()
                delta = int(input("库存变化量（减少填负数）：").strip())
                result = book_manager.update_stock(db, isbn, delta)
                print("库存更新完成，受影响文档数：%d" % result.modified_count)

            elif choice == "9":
                rows = borrow_manager.overdue_loans(db)
                if rows:
                    show(rows)
                else:
                    print("当前没有逾期记录。")

            elif choice == "10":
                show(reader_manager.college_statistics(db))

            else:
                print("无效菜单项，请重新选择。")

        except Exception as exc:
            print("操作失败：%s" % exc)


def main():
    client = get_client()
    try:
        db = client["library"]
        print_startup(db)
        if "--demo" in sys.argv:
            run_demo(db)
        else:
            interactive(db)
    finally:
        client.close()


if __name__ == "__main__":
    main()
