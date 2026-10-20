"""Menu-driven command line application for the library platform."""

from __future__ import annotations

import argparse
import json
from typing import Any

from bson import json_util

import book_manager
import borrow_manager
import reader_manager
import stat_manager
from mongodb_connect import check_connection, connected


def dump(value: Any) -> str:
    return json_util.dumps(value, ensure_ascii=False, indent=2)


def print_startup(db) -> None:
    print("=== 图书情报检索与统计平台 ===")
    print(dump(check_connection()))
    print("集合文档数：")
    for name, count in stat_manager.collection_counts(db).items():
        print(f"  {name}: {count}")


def run_demo(db) -> None:
    """Non-interactive smoke run useful for screenshots and classroom demos."""

    print("\n[演示] 评分前 5 图书")
    print(dump(book_manager.top_rated(db)))
    print("\n[演示] 分类统计")
    print(dump(stat_manager.category_statistics(db)))
    print("\n[演示] 借阅趋势")
    print(dump(stat_manager.borrow_trend(db)))
    print("\n[演示] 活跃读者")
    print(dump(stat_manager.reader_top5(db)))


def ask_number(prompt: str, cast=float):
    raw = input(prompt).strip()
    return cast(raw) if raw else None


def interactive(db) -> None:
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
            if choice == "1":
                keyword = input("书名或作者关键词（可空）：").strip() or None
                category = input("类别（可空）：").strip() or None
                min_price = ask_number("最低价格（可空）：")
                max_price = ask_number("最高价格（可空）：")
                rows = book_manager.search_books(
                    db,
                    keyword=keyword,
                    category=category,
                    price_min=min_price,
                    price_max=max_price,
                )
                print(dump(rows) if rows else "没有符合条件的图书。")
            elif choice == "2":
                print(dump(book_manager.top_rated(db)))
            elif choice == "3":
                print(dump(stat_manager.category_statistics(db)))
            elif choice == "4":
                print(dump(stat_manager.borrow_trend(db)))
            elif choice == "5":
                print(dump(stat_manager.reader_top5(db)))
            elif choice == "6":
                card = input("借阅证号：").strip()
                isbn = input("ISBN：").strip()
                result, doc = borrow_manager.borrow_book(db, card, isbn)
                print(f"借阅登记成功，新增文档数：{result.inserted_id is not None}")
            elif choice == "7":
                card = input("借阅证号：").strip()
                isbn = input("ISBN：").strip()
                result = borrow_manager.return_book(db, card, isbn)
                print("归还成功，受影响文档数：1" if result else "没有找到该读者的未归还记录。")
            elif choice == "8":
                isbn = input("ISBN：").strip()
                delta = int(input("库存变化量（减少填负数）：").strip())
                result = book_manager.update_stock(db, isbn, delta)
                print(f"库存更新完成，受影响文档数：{result.modified_count}")
            elif choice == "9":
                rows = borrow_manager.overdue_loans(db)
                print(dump(rows) if rows else "当前没有逾期记录。")
            elif choice == "10":
                print(dump(reader_manager.college_statistics(db)))
            else:
                print("无效菜单项，请重新选择。")
        except Exception as exc:  # keep the teaching CLI alive after bad input
            print(f"操作失败：{exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run a non-interactive demonstration")
    args = parser.parse_args()
    with connected() as (_, db):
        print_startup(db)
        if args.demo:
            run_demo(db)
        else:
            interactive(db)


if __name__ == "__main__":
    main()

