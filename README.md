# 智慧图书馆数字资源平台

《NoSQL数据库技术与应用（第2版）》综合实践 · 期末项目。

在第三章「图书情报检索与统计平台」基础上扩展为完整的数字资源平台：管理纸质馆藏与借阅，
用 GridFS 存储电子书与封面，并部署三台虚拟机的副本集与分片集群，支撑高可用与水平扩展。

## 一、完成情况

| 任务 | 状态 | 产出 |
|---|---|---|
| 一 技术选型 | 完成 | 文档第 2 章（约 1800 字，3 张对比表、CAP 双场景、两个风险） |
| 二 数据建模 | 完成 | 文档第 3 章（字段类型论证、location 拆合、borrow_logs 选型、索引清单） |
| 三 单机实现 | 完成 | nosql1:27017（6.0.29），50 / 30 / 3000 + 6 个 GridFS 文件，11 项功能，explain 与 20 万条耗时对比，三账号 |
| 四 应用开发 | 完成 | 9 个模块、16 项菜单（含读者增删改查与分页），GridFS 字节与 MD5 校验一致，审计日志 |
| 五 副本集 | 完成 | 三节点 rs0（27018），故障转移有完整时间线，节点增删 |
| 六 分片集群 | 完成 | configsvr + 2 分片 + mongos（27019—27022），1500 / 1500 分布 |
| 七 验收 | 完成 | 文档 14 页（27 表 4 图），Compass 聚合与命令行一致，导出两个集合，46 张截图（本项目不设答辩） |

## 二、环境

| 项 | 配置 |
|---|---|
| 虚拟机 | 3 台 Ubuntu 18.04.6，静态 IP 192.168.78.128/129/130（nosql1/2/3） |
| 数据库 | MongoDB 6.0.29（18.04 官方源最高版本） |
| Shell / 图形化 | mongosh 2.14.1 / Compass 1.53.0 |
| 程序 | Python 3.10 + PyMongo 4.18 |

端口分配：单机 27017、副本集 27018、配置服务器 27019、分片 27020/27021、mongos 27022。

## 三、项目结构

```
mongodb_connect.py   连接封装（URI、库名、账号全部走环境变量）
book_manager.py      馆藏检索
reader_manager.py    读者与学院、等级统计
borrow_manager.py    借阅、归还、逾期
stat_manager.py      分类统计、排行、趋势、结果落库
gridfs_manager.py    电子书上传、下载、校验、清单
audit_manager.py     操作日志
setup_smartlib.py    建库、建索引、导入、上传（带数量断言）
main.py              菜单主程序（16 项）
data/                三份数据集 + gridfs_files
docs/final/          期末项目文档（md 源 + docx 成稿 + 构建脚本）
scripts/vm/          虚拟机部署脚本（安装、固定 IP、副本集、分片）
evidence/            生成截图用的脚本
screenshots/         46 张执行截图（三、四在虚拟机 6.0.29 上重跑）
exports/             导出的 JSON
legacy/              第三章课程项目旧版（git 标签 v1-coursework）
```

## 四、运行

```bash
export MONGO_URI="mongodb://127.0.0.1:27017"
export MONGO_DB="smartlib"
export MONGO_USERNAME="app_rw"
export MONGO_PASSWORD="App2026"
export MONGO_AUTH_SOURCE="smartlib"

python setup_smartlib.py --reset   # 建库、导入 50/30/3000、上传 6 个文件
python main.py --demo              # 非交互演示
python main.py                     # 交互菜单（16 项）
```

副本集：`MONGO_URI="mongodb://192.168.78.128:27018,192.168.78.129:27018,192.168.78.130:27018/?replicaSet=rs0"`
分片：`MONGO_URI="mongodb://192.168.78.128:27022"`

## 五、文档与截图

- 期末项目文档：[docs/final/智慧图书馆数字资源平台-期末项目文档.docx](docs/final/智慧图书馆数字资源平台-期末项目文档.docx)
- 重新生成文档：`python docs/final/build_report.py`（依赖 python-docx）
- 截图清单：[docs/final/截图清单.md](docs/final/截图清单.md)
- 部署手册：[scripts/副本集部署.md](scripts/副本集部署.md)、[scripts/分片集群部署.md](scripts/分片集群部署.md)

## 六、两个关键设计取舍

**borrow_logs 用普通集合。** 平台需要按 status 更新归还状态、需要按 `{reader_card, borrow_date}` 分片；
时间序列集合只允许更新 metaField、分片键受 metaField 约束，两者冲突。代价是放弃自动分桶压缩，
用 `borrow_date` 索引弥补。

**audit_logs 用固定集合。** 日志只追加、按时间倒序读最近 100 条，capped 集合自动淘汰旧记录；
参数 16MB / 10 万条。

## 七、提交包

`submission/` 目录已按交付要求整理：`src/`（9 个源文件）、`data/`、`screenshots/`（46 张）、`exports/`、`scripts/`（部署脚本与手册）、`docs/`（放最终文档）。

## 八、作者

- 班级：24 数科 1 班　学号：202414870108　姓名：郭瀚铭