"""Day1~Day8 복습 방명록. 실행: python -m uvicorn main:app --workers 1"""

import hashlib
import secrets
import sqlite3
import threading
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from moderation import validate_text

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "guestbook.sqlite3"
MAX_ENTRIES = 1000
MAX_DB_BYTES = 16 * 1024 * 1024
MAX_BODY_BYTES = 8192


class EntryIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=20)
    message: str = Field(min_length=1, max_length=500)

    @field_validator("name", "message")
    @classmethod
    def no_null_character(cls, value: str):
        if "\x00" in value:
            raise ValueError("널 문자는 사용할 수 없습니다.")
        return validate_text(value)


class EntryOut(BaseModel):
    id: int
    name: str
    message: str
    created_at: str


class CreatedEntry(EntryOut):
    delete_token: str


class EntryPage(BaseModel):
    items: list[EntryOut]
    total: int
    page: int
    page_size: int
    capacity: int


class BodyLimit:
    """Content-Length가 없거나 거짓이어도 실제 수신 본문을 제한합니다."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD"}:
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            size += len(event.get("body", b""))
            if size > MAX_BODY_BYTES:
                response = JSONResponse({"detail": "요청 본문은 8 KiB 이하여야 합니다."}, 413)
                return await response(scope, receive, send)
            chunks.append(event)
            if not event.get("more_body", False):
                break

        async def replay():
            return chunks.pop(0) if chunks else await receive()

        await self.app(scope, replay, send)


def connect(path: Path):
    connection = sqlite3.connect(path, timeout=3)
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA max_page_count = {MAX_DB_BYTES // 4096}")
    return connection


def initialize(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as db, db:
        db.execute("PRAGMA page_size = 4096")
        db.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 20),
                message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 500),
                created_at TEXT NOT NULL,
                delete_token_hash TEXT NOT NULL
            )
        """)


def create_app(db_path: Path = DB_PATH, *, max_entries=MAX_ENTRIES, cooldown=3.0):
    """테스트에서는 임시 DB를 주입합니다. 운영 기본값은 작게 유지합니다."""
    db_path = Path(db_path)
    initialize(db_path)
    app = FastAPI(title="작은 방명록", version="1.0.0")
    app.add_middleware(BodyLimit)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    write_lock = threading.Lock()
    last_post = -float("inf")

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if request.url.path == "/":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; object-src 'none'; base-uri 'none'; "
                "frame-ancestors 'none'; form-action 'self'"
            )
        return response

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, error):
        return JSONResponse(
            {"detail": "저장 공간이 부족하거나 DB가 사용 중입니다. 잠시 후 다시 시도하세요."},
            status_code=503,
        )

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/entries", response_model=EntryPage)
    def list_entries(page: int = Query(1, ge=1, le=1000),
                     page_size: int = Query(10, ge=1, le=20)):
        with closing(connect(db_path)) as db:
            db.execute("BEGIN")
            total = db.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            rows = db.execute(
                "SELECT id, name, message, created_at FROM entries ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, (page - 1) * page_size),
            ).fetchall()
        return {"items": [dict(row) for row in rows], "total": total,
                "page": page, "page_size": page_size, "capacity": max_entries}

    @app.post("/api/entries", response_model=CreatedEntry, status_code=201)
    def add_entry(body: EntryIn):
        nonlocal last_post
        token = secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        # 쓰기 잠금과 트랜잭션으로 동시 요청에서도 글 수 제한을 지킵니다.
        with write_lock, closing(connect(db_path)) as db, db:
            if time.monotonic() - last_post < cooldown:
                raise HTTPException(429, "전체 방문자 기준 3초에 한 번 등록할 수 있습니다.",
                                    headers={"Retry-After": "3"})
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT COUNT(*) FROM entries").fetchone()[0] >= max_entries:
                raise HTTPException(409, "방명록이 가득 찼습니다. 기존 글을 삭제한 뒤 이용하세요.")
            cursor = db.execute(
                "INSERT INTO entries (name, message, created_at, delete_token_hash) VALUES (?, ?, ?, ?)",
                (body.name, body.message, created_at, hashlib.sha256(token.encode()).hexdigest()),
            )
            db.commit()
            last_post = time.monotonic()
        return {"id": cursor.lastrowid, "name": body.name, "message": body.message,
                "created_at": created_at, "delete_token": token}

    @app.delete("/api/entries/{entry_id}", status_code=204)
    def delete_entry(entry_id: int, authorization: str = Header(default="", max_length=100)):
        with closing(connect(db_path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT delete_token_hash FROM entries WHERE id = ?", (entry_id,)).fetchone()
            if row is None:
                raise HTTPException(404, "글을 찾을 수 없습니다.")
            token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
            digest = hashlib.sha256(token.encode()).hexdigest()
            if not token or not secrets.compare_digest(row["delete_token_hash"], digest):
                raise HTTPException(403, "이 글의 삭제 키가 필요합니다.")
            db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        return Response(status_code=204)

    return app


app = create_app()
