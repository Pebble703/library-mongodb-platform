"""智慧图书馆数字资源平台 · 菜单式主程序。

用法：
    python main.py          交互菜单
    python main.py --demo   非交互演示，一次打印主要检索与统计结果
"""

import sys
from pathlib import Path

from bson import json_util

import audit_manager
import book_manager
import borrow_manager
import gridfs_manager
import reader_manager
import stat_manager
from mongodb_connect import DATABASE_NAME, check_connection, get_client

BASE = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE / "downloads"


def show(value):
    print(json_util.dumps(value, ensure_ascii=False, indent=2))


def print_startup(db):
    print("=== 智慧图书馆数字资源平台 ===")
    show(check_connection())
    print("集合文档数：")
    for name, count in stat_manager.collection_counts(db).items():
        print("  %-14s %s" % (name, count))
    print("  %-14s %s" % ("gridfs.files", db.fs.files.count_documents({})))


def ask_number(prompt, cast=float):
    text = input(prompt).strip()
    return cast(text) if text else None


def run_demo(db):
    """一次性打印主要结果，便于截图。"""
    print("\n[检索] 类别=计算机，价格 50—100")
    show(book_manager.search_category_price(db, "计算机", 50, 100))
    print("\n[检索] 缺少 tags 字段的图书")
    show(book_manager.missing_tags(db))
    print("\n[统计] 分类统计")
    show(stat_manager.category_statistics(db))
    print("\n[统计] 学院借阅 Top5")
    show(stat_manager.college_borrow_top5(db))
    print("\n[统计] 借阅 Top10（含馆藏位置）")
    show(stat_manager.top_books(db, 10))
    print("\n[文件] GridFS 清单")
    show(gridfs_manager.list_files(db))


def gridfs_menu(db):
    print(
        "\n电子书子菜单：\n"
        "1. 按清单重新上传六个文件\n"
        "2. 按书名下载电子书并校验字节\n"
        "3. 查看 GridFS 文件清单\n"
        "0. 返回"
    )
    choice = input("请选择：").strip()
    try:
        if choice == "1":
            uploaded = gridfs_manager.upload_manifest(db, BASE / "data" / "gridfs_files")
            audit_manager.log(db, "upload", "fs.files", detail={"count": len(uploaded)})
            print("上传完成 %d 个文件" % len(uploaded))
        elif choice == "2":
            title = input("书名关键词：").strip()
            book, _ = gridfs_manager.find_ebook_by_title(db, title)
            if book is None:
                print("没有找到带电子书的图书。")
                return
            source = BASE / "data" / "gridfs_files" / book["ebook_name"]
            result = gridfs_manager.verify(db, book["isbn"], "ebook", source, DOWNLOAD_DIR)
            print("下载到：%s" % result["downloaded"])
            print("源文件 %d 字节，下载 %d 字节，字节一致：%s，MD5 一致：%s"
                  % (result["source_bytes"], result["downloaded_bytes"],
                     result["size_match"], result["md5_match"]))
        elif choice == "3":
            show(gridfs_manager.list_files(db))
        else:
            return
    except Exception as exc:
        print("操作失败：%s" % exc)


def reader_menu(db):
    """读者管理子菜单：分页浏览、新增、修改、删除、学院分布。"""
    print(
        "\n读者管理：\n"
        "1. 分页浏览读者\n"
        "2. 新增读者\n"
        "3. 修改读者\n"
        "4. 删除读者\n"
        "5. 学院分布统计\n"
        "0. 返回"
    )
    choice = input("请选择：").strip()
    try:
        if choice == "1":
            page = ask_number("第几页（默认 1）：", int) or 1
            size = ask_number("每页条数（默认 10）：", int) or 10
            result = reader_manager.list_page(db, page=page, size=size)
            print("共 %d 条，第 %d / %d 页" % (result["total"], result["page"], result["pages"]))
            show(result["rows"])
        elif choice == "2":
            card_no = input("借阅证号：").strip()
            name = input("姓名：").strip()
            college = input("学院：").strip()
            level = input("等级（普通/高级/教师，可空）：").strip() or "普通"
            email = input("邮箱（可空）：").strip()
            doc = {"card_no": card_no, "name": name, "college": college, "level": level}
            if email:
                doc["email"] = email
            reader_manager.insert_reader(db, doc)
            audit_manager.log(db, "insert", "readers", detail={"card_no": card_no})
            print("新增成功。")
        elif choice == "3":
            card_no = input("借阅证号：").strip()
            if reader_manager.get_reader(db, card_no) is None:
                print("读者不存在。")
                return
            field = input("要修改的字段（name / college / level / email）：").strip()
            value = input("新值：").strip()
            reader_manager.update_reader(db, card_no, {field: value})
            audit_manager.log(db, "update", "readers", detail={"card_no": card_no, "field": field})
            print("修改成功。")
        elif choice == "4":
            card_no = input("借阅证号：").strip()
            reader_manager.delete_reader(db, card_no)
            audit_manager.log(db, "delete", "readers", detail={"card_no": card_no})
            print("删除成功。")
        elif choice == "5":
            print("各学院读者人数：")
            show(reader_manager.college_statistics(db))
        else:
            return
    except Exception as exc:
        print("操作失败：%s" % exc)


def interactive(db):
    while True:
        print(
            "\n菜单：\n"
            "1. 类别 + 价格区间检索\n"
            "2. 标签多选检索\n"
            "3. 书名模糊检索\n"
            "4. 出版年份范围检索\n"
            "5. 缺少 tags 的图书\n"
            "6. 评分 Top10\n"
            "7. 分类统计（写入 category_stats）\n"
            "8. 学院借阅 Top5\n"
            "9. 年月借阅趋势\n"
            "10. 借阅排行榜（含馆藏位置）\n"
            "11. 电子书上传 / 下载 / 清单\n"
            "12. 审计日志最近 100 条\n"
            "13. 借阅登记\n"
            "14. 图书归还\n"
            "15. 读者管理（增删改查 / 分页）\n"
            "16. 图书分页浏览\n"
            "0. 退出"
        )
        choice = input("请选择：").strip()
        try:
            if choice == "0":
                print("数据库连接已关闭，程序退出。")
                return

            elif choice == "1":
                category = input("类别（如 计算机）：").strip()
                low = ask_number("最低价格（可空）：")
                high = ask_number("最高价格（可空）：")
                rows = book_manager.search_category_price(db, category, low, high)
                print("共 %d 条" % len(rows))
                show(rows) if rows else print("没有符合条件的图书。")

            elif choice == "2":
                tags = [t.strip() for t in input("标签，用逗号分隔：").split(",") if t.strip()]
                rows = book_manager.search_tags(db, tags)
                print("共 %d 条" % len(rows))
                show(rows) if rows else print("没有同时包含这些标签的图书。")

            elif choice == "3":
                keyword = input("书名关键词：").strip()
                rows = book_manager.search_title(db, keyword)
                print("共 %d 条" % len(rows))
                show(rows) if rows else print("没有匹配的图书。")

            elif choice == "4":
                y1 = ask_number("起始年份（默认 1900）：", int)
                y2 = ask_number("结束年份（默认 2100）：", int)
                y1 = y1 if y1 is not None else 1900
                y2 = y2 if y2 is not None else 2100
                rows = book_manager.search_year_range(db, y1, y2)
                print("共 %d 条" % len(rows))
                show(rows) if rows else print("该年份区间没有图书。")

            elif choice == "5":
                rows = book_manager.missing_tags(db)
                print("共 %d 条缺少 tags 字段" % len(rows))
                show(rows)

            elif choice == "6":
                show(book_manager.top_rated(db, 10))

            elif choice == "7":
                show(stat_manager.category_statistics(db))
                saved = stat_manager.save_category_stats(db)
                audit_manager.log(db, "merge", "category_stats", detail={"count": len(saved)})
                print("已写入 category_stats，共 %d 条" % len(saved))

            elif choice == "8":
                show(stat_manager.college_borrow_top5(db))

            elif choice == "9":
                show(stat_manager.monthly_trend(db))

            elif choice == "10":
                show(stat_manager.top_books(db, 10))

            elif choice == "11":
                gridfs_menu(db)

            elif choice == "12":
                total = audit_manager.count(db)
                print("审计日志共 %d 条，显示最近 10 条：" % total)
                show(audit_manager.recent(db, 10))

            elif choice == "13":
                card_no = input("借阅证号：").strip()
                isbn = input("ISBN：").strip()
                days = ask_number("借期天数（默认 30）：", int) or 30
                borrow_manager.borrow_book(db, card_no, isbn, duration_days=days)
                audit_manager.log(db, "insert", "borrow_logs", detail={"card_no": card_no, "isbn": isbn})
                print("借阅登记成功。")

            elif choice == "14":
                card_no = input("借阅证号：").strip()
                isbn = input("ISBN：").strip()
                result = borrow_manager.return_book(db, card_no, isbn)
                if result is None:
                    print("没有找到未归还的借阅记录。")
                else:
                    audit_manager.log(db, "update", "borrow_logs", detail={"card_no": card_no, "isbn": isbn})
                    print("归还成功，受影响文档数：%d" % result.modified_count)

            elif choice == "15":
                reader_menu(db)

            elif choice == "16":
                page = ask_number("第几页（默认 1）：", int) or 1
                size = ask_number("每页条数（默认 10）：", int) or 10
                result = book_manager.list_page(db, page=page, size=size)
                print("共 %d 条，第 %d / %d 页" % (result["total"], result["page"], result["pages"]))
                show(result["rows"])

            else:
                print("无效菜单项，请重新选择。")

        except Exception as exc:
            print("操作失败：%s" % exc)


def main():
    client = get_client()
    db = client[DATABASE_NAME]
    try:
        print_startup(db)
        if "--demo" in sys.argv:
            run_demo(db)
        else:
            interactive(db)
    finally:
        client.close()


if __name__ == "__main__":
    main()
