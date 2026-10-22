# 图书情报检索与统计平台

《NoSQL数据库技术与应用（第2版）》第 3 章 MongoDB 基础操作 · 实训项目。

基于 MongoDB 实现的图书情报系统，覆盖实例部署、数据建模、检索、聚合统计、索引优化、权限管理与图形化验收，并提供一个菜单式的命令行程序。

## 技术栈

| 项目 | 版本 |
|---|---|
| 数据库 | MongoDB 8.0.32 |
| 数据库 Shell | mongosh 2.11.1 |
| 图形化工具 | MongoDB Compass 1.53.0 |
| 编程语言 | Python 3.10 |
| 驱动 | PyMongo 4.18.3 |

数据库服务运行在 WSL2（Ubuntu 22.04）中，以命令行参数方式启动：

```bash
mongod --dbpath ~/mongo-lab/data --logpath ~/mongo-lab/log/mongod.log --fork --auth
```

## 项目结构

```
.
├── mongodb_connect.py    # 数据库连接模块（参数集中、支持认证）
├── book_manager.py       # 图书增删改查、条件检索、评分排行
├── reader_manager.py     # 读者查询、学院与等级统计
├── borrow_manager.py     # 借阅登记、归还处理、逾期查询
├── stat_manager.py       # 聚合统计管道
├── main.py               # 菜单式主程序
├── setup_library.py      # 建库、建索引并导入数据
├── data/                 # 三个数据集（Extended JSON）
├── exports/              # category_stats 与 books 的导出结果
├── screenshots/          # 实验截图
└── docs/                 # 技术文档
```

## 数据模型

| 集合 | 类型 | 说明 |
|---|---|---|
| books | 普通集合 | 图书信息，20 条 |
| readers | 普通集合 | 读者信息，16 条 |
| borrow_logs | 时间序列集合 | 借阅流水，按 borrow_date 分桶，2 年过期 |
| category_stats | 普通集合 | 分类统计结果，由 `$merge` 写入 |
| book_logs | 固定集合 | 1 MB / 1000 条，用于操作审计 |
| book_in_stock | 视图 | `books` 中 stock > 0 的图书 |

索引：`uniq_isbn`（唯一）、`idx_title`、`idx_category`、`idx_tags_multikey`（多键）、`idx_category_price`（复合）、`uniq_card_no`（唯一）。

## 快速开始

1. 安装依赖

```bash
pip install pymongo
```

2. 启动 MongoDB（需开启认证，首次使用先创建账号）

3. 配置连接信息（不写死在代码里）

```bash
export MONGO_USERNAME=libWriter
export MONGO_PASSWORD=<你的密码>
export MONGO_AUTH_SOURCE=library
```

4. 建立集合并导入数据

```bash
python setup_library.py
```

5. 运行程序

```bash
python main.py          # 交互菜单
python main.py --demo   # 演示模式，一次打印五项统计
```

## 功能

| 菜单 | 功能 |
|---|---|
| 1 | 图书条件检索（书名/作者关键词 + 类别 + 价格区间） |
| 2 | 评分排行 |
| 3 | 分类统计（数量、库存、均价、评分） |
| 4 | 借阅趋势（按年份） |
| 5 | 活跃读者榜（关联 readers） |
| 6 | 借阅登记（校验库存与借阅证） |
| 7 | 图书归还 |
| 8 | 调整库存 |
| 9 | 逾期记录查询 |
| 10 | 读者学院统计 |

## 两个实现上的取舍

**时间序列集合只能追加。** `borrow_logs` 未定义 metaField，MongoDB 不允许更新 `status` 这类普通字段（error 72）。因此归还操作不修改原记录，而是追加一条“已归还”记录并同步恢复库存；逾期判断改为按状态查询。`borrow_manager.mark_overdue` 中保留了 `update_many` 写法，但注明其在当前集合上不可用。

**TTL 会清理历史数据。** `borrow_logs` 按要求设置 `expireAfterSeconds = 63072000`（2 年），而数据集日期为 2023—2025 年，运行时的系统时间已超出窗口，导入后文档数会由 66 条逐步降至 26 条。统计取证时通过 `collMod` 临时延长过期时间以保证样本完整，取证后恢复原值。

## 作者

- 班级：24 数科 1 班
- 学号：202414870108
- 姓名：郭瀚铭
