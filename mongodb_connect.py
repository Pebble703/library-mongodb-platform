"""MongoDB connection helpers for the library information platform.

Connection settings are intentionally kept in one place.  The defaults match
the practical assignment setup, while environment variables make the same
code usable from Linux, WSL, or a remote MongoDB host.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from pymongo import MongoClient
from pymongo.database import Database


MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DATABASE_NAME = os.getenv("MONGO_DB", "library")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")
SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "5000"))


def get_client() -> MongoClient:
    """Create a client using the configured URI and optional credentials."""

    kwargs = {
        "serverSelectionTimeoutMS": SERVER_SELECTION_TIMEOUT_MS,
        "tz_aware": True,
    }
    if MONGO_USERNAME:
        kwargs.update(
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD or "",
            authSource=MONGO_AUTH_SOURCE,
        )
    return MongoClient(MONGO_URI, **kwargs)


def get_db(client: MongoClient | None = None) -> Database:
    """Return the configured database, optionally reusing a client."""

    if client is None:
        client = get_client()
    return client[DATABASE_NAME]


def check_connection(client: MongoClient | None = None) -> dict:
    """Return a small, JSON-friendly connection diagnostic."""

    owns_client = client is None
    client = client or get_client()
    try:
        ping = client.admin.command("ping")
        info = client.server_info()
        return {
            "ok": bool(ping.get("ok")),
            "uri": MONGO_URI,
            "database": DATABASE_NAME,
            "server_version": info.get("version"),
        }
    finally:
        if owns_client:
            client.close()


@contextmanager
def connected() -> Iterator[tuple[MongoClient, Database]]:
    """Yield a client and database and always close the client."""

    client = get_client()
    try:
        yield client, client[DATABASE_NAME]
    finally:
        client.close()


__all__ = [
    "DATABASE_NAME",
    "MONGO_URI",
    "check_connection",
    "connected",
    "get_client",
    "get_db",
]
