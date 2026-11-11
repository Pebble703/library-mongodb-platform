"""数据库连接模块：连接参数统一写在这里，其它文件都从这里取连接。"""

import os

from pymongo import MongoClient

# 换环境只改环境变量：单机 27017、副本集 27018、分片 mongos 27022
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DATABASE_NAME = os.getenv("MONGO_DB", "smartlib")

# 启用认证后通过环境变量传入账号，没设置就按无认证连接
USERNAME = os.getenv("MONGO_USERNAME")
PASSWORD = os.getenv("MONGO_PASSWORD")
AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", DATABASE_NAME)


def get_client():
    """创建 MongoClient，设置了账号就自动带上认证信息。"""
    if USERNAME:
        return MongoClient(
            MONGO_URI,
            username=USERNAME,
            password=PASSWORD or "",
            authSource=AUTH_SOURCE,
            serverSelectionTimeoutMS=5000,
        )
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def get_db(client=None):
    """取得当前配置的数据库对象（默认 smartlib）。"""
    return (client or get_client())[DATABASE_NAME]


def check_connection(client=None):
    """返回连接信息，程序启动时打印。"""
    own_client = client is None
    client = client or get_client()
    try:
        client.admin.command("ping")
        info = client.server_info()
        return {
            "ok": True,
            "uri": MONGO_URI,
            "database": DATABASE_NAME,
            "server_version": info.get("version"),
        }
    finally:
        if own_client:
            client.close()
