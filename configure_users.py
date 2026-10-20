"""Create the read-only and read-write accounts required by task S1-S3.

Passwords are entered interactively or supplied through the command line when
running in an automated lab environment.  The script does not store passwords.
"""

from __future__ import annotations

import argparse
import getpass

from mongodb_connect import get_client


def upsert_user(db, username: str, password: str, roles: list[dict]) -> dict:
    try:
        db.command("updateUser", username, pwd=password, roles=roles)
        action = "updated"
    except Exception as exc:
        if getattr(exc, "details", {}).get("codeName") != "UserNotFound":
            raise
        db.command("createUser", username, pwd=password, roles=roles)
        action = "created"
    return {"user": username, "action": action, "roles": roles}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader-password")
    parser.add_argument("--writer-password")
    args = parser.parse_args()
    reader_password = args.reader_password or getpass.getpass("libReader 密码：")
    writer_password = args.writer_password or getpass.getpass("libWriter 密码：")
    if not reader_password or not writer_password:
        raise SystemExit("密码不能为空")
    client = get_client()
    try:
        db = client["library"]
        result = [
            upsert_user(db, "libReader", reader_password, [{"role": "read", "db": "library"}]),
            upsert_user(db, "libWriter", writer_password, [{"role": "readWrite", "db": "library"}, {"role": "dbAdmin", "db": "library"}]),
        ]
        print(result)
        print("服务启用 security.authorization 后，再用两个账号分别验证读写权限。")
    finally:
        client.close()


if __name__ == "__main__":
    main()

