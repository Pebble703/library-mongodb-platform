# 图书情报检索与统计平台

《NoSQL数据库技术与应用（第2版）》第3章 MongoDB 基础操作实训项目。

## 项目简介

基于 MongoDB 开发的图书情报检索与统计平台，实现了图书管理、读者管理、借阅流水和多维度统计分析功能，并提供菜单式命令行交互界面。

## 技术栈

- **数据库**：MongoDB 8.2.3
- **编程语言**：Python 3.10+
- **驱动**：PyMongo
- **开发工具**：PyCharm / MongoDB Compass / mongosh

## 功能模块

| 模块 | 功能 |
|------|------|
| 图书管理 | 图书增删改查、条件检索、评分排行 |
| 读者管理 | 读者信息管理、学院统计、等级分布 |
| 借阅管理 | 借阅登记、归还处理、逾期查询 |
| 统计分析 | 分类统计、借阅趋势、畅销榜、活跃读者 |

## 数据库设计

### 集合列表

| 集合名 | 类型 | 说明 |
|--------|------|------|
| books | 普通集合 | 图书信息（20条） |
| readers | 普通集合 | 读者信息（16条） |
| borrow_logs | 时间序列集合 | 借阅流水（66条），TTL 2年 |
| category_stats | 普通集合 | 分类统计结果 |
| book_logs | 固定集合 | 容量上限 1MB / 1000条 |
| book_in_stock | 视图 | 在架图书（stock > 0） |

### 索引设计

- `uniq_isbn`：books.isbn 唯一索引
- `idx_title`：books.title 单键索引
- `idx_category`：books.category 单键索引
- `idx_tags_multikey`：books.tags 多键索引
- `idx_category_price`：category + price 复合索引
- `uniq_card_no`：readers.card_no 唯一索引

## 项目结构

```
databasemanagementsystem/
├── mongodb_connect.py      # 数据库连接模块
├── book_manager.py        # 图书管理模块
├── reader_manager.py     # 读者管理模块
├── borrow_manager.py      # 借阅管理模块
├── stat_manager.py        # 统计分析模块
├── main.py                # 主程序（菜单交互）
├── setup_library.py       # 建库与数据导入脚本
├── validate_library.py    # 功能验证脚本
├── configure_users.py     # 用户权限配置脚本
├── books.txt              # 图书数据集
├── readers.txt            # 读者数据集
├── borrow_logs.txt        # 借阅流水数据集
└── artifacts/             # 运行结果输出
```

## 快速开始

### 环境要求

- MongoDB 8.0+ 已安装并启动（默认端口 27017）
- Python 3.10+
- PyMongo：`pip install pymongo`

### 初始化数据库

```bash
python setup_library.py
```

### 运行程序

```bash
# 交互式菜单
python main.py

# 演示模式（自动运行示例查询）
python main.py --demo
```

### 配置用户权限

```bash
python configure_users.py
```

## 实验报告

详见：`24数科1班-202414870108-郭瀚铭.docx`

## 作者

- 班级：24数科1班
- 学号：202414870108
- 姓名：郭瀚铭
