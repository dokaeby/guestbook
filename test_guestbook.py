"""서버를 띄우지 않고 임시 SQLite 파일로 동작과 경계값을 검증합니다."""
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from main import MAX_DB_BYTES, create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "test.sqlite3", cooldown=0)) as test_client:
        yield test_client


def post(client, **changes):
    return client.post("/api/entries", json={"name": "방문자", "message": "반갑습니다!", **changes})


def test_create_list_and_secret(client):
    created = post(client)
    assert created.status_code == 201
    entry = created.json()
    assert entry["name"] == "방문자"
    assert len(entry["delete_token"]) >= 40
    page = client.get("/api/entries").json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == entry["id"]
    assert set(page["items"][0]) == {"id", "name", "message", "created_at"}
    assert created.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("changes", [
    {"name": ""}, {"name": "   "}, {"name": "가" * 21},
    {"message": ""}, {"message": " \n\t"}, {"message": "가" * 501},
    {"name": 1}, {"message": None}, {"unexpected": True},
    {"name": "a\x00b"}, {"message": "a\x00b"},
])
def test_invalid_input(client, changes):
    assert post(client, **changes).status_code == 422
    assert client.get("/api/entries").json()["total"] == 0


def test_exact_boundaries_and_whitespace(client):
    assert post(client, name="가" * 20, message="나" * 500).status_code == 201
    entry = post(client, name=" 가 ", message=" 나 ").json()
    assert entry["name"] == "가" and entry["message"] == "나"


def test_required_and_bad_json(client):
    assert client.post("/api/entries", json={}).status_code == 422
    assert client.post("/api/entries", content="{", headers={"Content-Type": "application/json"}).status_code == 422


@pytest.mark.parametrize("query", ["page=0", "page=1001", "page_size=0", "page_size=21", "page=x"])
def test_invalid_pagination(client, query):
    assert client.get(f"/api/entries?{query}").status_code == 422


def test_pagination_order(client):
    for n in range(12):
        post(client, message=str(n))
    first = client.get("/api/entries").json()
    second = client.get("/api/entries?page=2").json()
    assert first["total"] == 12
    assert [e["message"] for e in first["items"]] == [str(n) for n in range(11, 1, -1)]
    assert [e["message"] for e in second["items"]] == ["1", "0"]


def test_delete_requires_correct_key(client):
    entry = post(client).json()
    url = f"/api/entries/{entry['id']}"
    assert client.delete(url).status_code == 403
    assert client.delete(url, headers={"Authorization": "Bearer wrong"}).status_code == 403
    assert client.delete(url, headers={"Authorization": f"Bearer {entry['delete_token']}"}).status_code == 204
    assert client.delete(url).status_code == 404
    assert client.get("/api/entries").json()["total"] == 0


def test_sql_injection_is_only_text(client):
    message = "'); DROP TABLE entries; --"
    assert post(client, message=message).status_code == 201
    assert client.get("/api/entries").json()["items"][0]["message"] == message
    assert post(client).status_code == 201


def test_xss_stays_data_and_frontend_uses_text(client):
    assert post(client, message="<script>alert(1)</script>").status_code == 201
    assert "<script>" in client.get("/api/entries").json()["items"][0]["message"]
    script = client.get("/static/app.js").text
    assert "message.textContent = entry.message" in script
    assert "innerHTML" not in script
    assert "script-src 'self'" in client.get("/").headers["content-security-policy"]


def test_capacity_atomic_and_no_silent_deletion(tmp_path):
    with TestClient(create_app(tmp_path / "capacity.sqlite3", max_entries=3, cooldown=0)) as client:
        with ThreadPoolExecutor(max_workers=6) as pool:
            responses = list(pool.map(lambda _: post(client), range(6)))
        assert sorted(r.status_code for r in responses) == [201, 201, 201, 409, 409, 409]
        assert client.get("/api/entries").json()["total"] == 3
        entry = next(r.json() for r in responses if r.status_code == 201)
        client.delete(f"/api/entries/{entry['id']}", headers={"Authorization": f"Bearer {entry['delete_token']}"})
        assert post(client).status_code == 201


def test_post_cooldown(tmp_path):
    with TestClient(create_app(tmp_path / "cooldown.sqlite3")) as client:
        assert post(client).status_code == 201
        response = post(client)
        assert response.status_code == 429
        assert response.headers["retry-after"] == "3"


def test_body_limit_with_and_without_length(client):
    assert client.post("/api/entries", content=b"x" * 8193).status_code == 413
    assert client.post("/api/entries", content=iter([b"x" * 4096, b"y" * 4097])).status_code == 413


def test_persistence_one_table_and_db_budget(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    with TestClient(create_app(path, cooldown=0)) as client:
        entry = post(client).json()
    with TestClient(create_app(path)) as restarted:
        assert restarted.get("/api/entries").json()["total"] == 1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("entries",)]
        assert db.execute("PRAGMA foreign_key_list(entries)").fetchall() == []
        digest = db.execute("SELECT delete_token_hash FROM entries").fetchone()[0]
        assert digest == hashlib.sha256(entry["delete_token"].encode()).hexdigest()
    assert path.stat().st_size < MAX_DB_BYTES


def test_health_and_static(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "작은 방명록" in client.get("/").text
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/../../main.py").status_code == 404


def test_worst_case_storage_budget(tmp_path):
    from main import connect
    path = tmp_path / "budget.sqlite3"
    create_app(path)
    with connect(path) as db:
        assert db.execute("PRAGMA max_page_count").fetchone()[0] * 4096 == MAX_DB_BYTES
        db.executemany(
            "INSERT INTO entries(name, message, created_at, delete_token_hash) VALUES (?, ?, ?, ?)",
            [("😀" * 20, "😀" * 500, "2026-10-23T00:00:00+00:00", "a" * 64)] * 1000,
        )
    assert path.stat().st_size < 8 * 1024 * 1024


def test_sqlite_busy_returns_no_internal_details(client, tmp_path):
    import main
    original = main.connect

    def broken(path):
        raise sqlite3.OperationalError("sensitive internal path")

    try:
        main.connect = broken
        response = client.get("/api/entries")
    finally:
        main.connect = original
    assert response.status_code == 503
    assert "sensitive" not in response.text
