"""电子书与封面图的 GridFS 存取。

电子书 PDF 与封面 PNG 存入 GridFS，通过 books.ebook_name 关联。
按任务书要求，上传时写入 isbn、文件类型、原始文件名、字节数与校验和，
下载后可用字节数或 MD5 校验。
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from gridfs import GridFSBucket


def bucket(db):
    """统一的 GridFS 桶，桶名 fs，集合为 fs.files / fs.chunks。"""
    return GridFSBucket(db, bucket_name="fs")


def md5_of(path):
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 256), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload(db, path, isbn, kind):
    """上传一个文件，返回 file_id。kind 取 ebook 或 cover。"""
    path = Path(path)
    data = path.read_bytes()
    metadata = {
        "isbn": isbn,
        "kind": kind,
        "original_name": path.name,
        "bytes": len(data),
        "md5": hashlib.md5(data).hexdigest(),
        "uploaded_at": datetime.now(timezone.utc),
    }
    file_id = bucket(db).upload_from_stream(path.name, data, metadata=metadata)
    return file_id


def upload_manifest(db, files_dir, manifest_path=None):
    """按 files_manifest.txt 的清单批量上传，返回已上传记录。"""
    import json

    files_dir = Path(files_dir)
    manifest_path = Path(manifest_path) if manifest_path else files_dir / "files_manifest.txt"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

    uploaded = []
    for group, kind in (("ebooks", "ebook"), ("covers", "cover")):
        for item in manifest.get(group, []):
            path = files_dir / item["filename"]
            if not path.exists():
                raise FileNotFoundError(path)
            file_id = upload(db, path, item["related_isbn"], kind)
            uploaded.append(
                {
                    "filename": item["filename"],
                    "isbn": item["related_isbn"],
                    "kind": kind,
                    "bytes": item["bytes"],
                    "file_id": file_id,
                }
            )
    return uploaded


def list_files(db):
    """列出 GridFS 中的全部文件，按上传时间倒序。"""
    rows = []
    for doc in db.fs.files.find({}).sort("uploadDate", -1):
        meta = doc.get("metadata", {})
        rows.append(
            {
                "filename": doc.get("filename"),
                "length": doc.get("length"),
                "uploadDate": doc.get("uploadDate"),
                "isbn": meta.get("isbn"),
                "kind": meta.get("kind"),
                "md5": meta.get("md5"),
            }
        )
    return rows


def find_for_isbn(db, isbn, kind=None):
    """按 ISBN 找 GridFS 文件，可限定 ebook / cover。"""
    query = {"metadata.isbn": isbn}
    if kind:
        query["metadata.kind"] = kind
    return db.fs.files.find_one(query, sort=[("uploadDate", -1)])


def download(db, isbn, kind, out_dir):
    """按 ISBN 下载文件到目录，返回本地路径与字节数。"""
    doc = find_for_isbn(db, isbn, kind)
    if doc is None:
        raise LookupError("未找到该 ISBN 对应的文件：%s / %s" % (isbn, kind))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / doc["filename"]

    stream = bucket(db).open_download_stream(doc["_id"])
    data = stream.read()
    out_path.write_bytes(data)
    return out_path, len(data)


def verify(db, isbn, kind, source_path, out_dir):
    """下载并与源文件比对字节数与 MD5，返回校验结果。"""
    source_path = Path(source_path)
    out_path, size = download(db, isbn, kind, out_dir)
    source_size = source_path.stat().st_size
    return {
        "isbn": isbn,
        "kind": kind,
        "downloaded": str(out_path),
        "source_bytes": source_size,
        "downloaded_bytes": size,
        "size_match": source_size == size,
        "md5_match": md5_of(source_path) == md5_of(out_path),
    }


def find_ebook_by_title(db, title):
    """按书名模糊查电子书：返回 (图书文档, GridFS 文件文档)。"""
    book = db.books.find_one(
        {"title": {"$regex": title, "$options": "i"}, "ebook_name": {"$exists": True}},
        {"_id": 0, "isbn": 1, "title": 1, "ebook_name": 1},
    )
    if book is None:
        return None, None
    return book, find_for_isbn(db, book["isbn"], "ebook")
