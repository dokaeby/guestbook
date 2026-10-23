import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from main import ROOT, create_app
from moderation import POLICY, POLICY_MESSAGE, TextPolicy


@pytest.mark.parametrize("text", [
    "씨발", "씨 발", "씨.발", "씨1발", "씨\u200b발", "씨\u0301발",
    "개새끼", "병신", "ㅅㅂ", "ㅂㅅ", "야 동", "포르노", "섹스",
    "FUCK", "ＦＵＣＫ", "f.u.c.k", "f_u_c_k", "f u c k", "sh1t",
    "fuck입니다", "S E X", "p.o.r.n", "성기 노출",
])
def test_blocked_variations(text):
    assert POLICY.blocked(text)


@pytest.mark.parametrize("text", [
    "안녕하세요. 좋은 하루 보내세요!", "아름다운 꽃 사진이네요.",
    "시발점이 되는 좋은 경험입니다.", "성교육 수업을 들었습니다.",
    "class assignment in Essex", "푸른 하늘과 초록 정원이 좋아요.",
    "500점 만점에 100점!", "<script>alert(1)</script>",
])
def test_normal_text_not_blocked(text):
    assert not POLICY.blocked(text)


@pytest.mark.parametrize("field", ["name", "message"])
def test_api_rejects_without_saving_or_using_cooldown(tmp_path, field):
    path = tmp_path / "filtered.sqlite3"
    with TestClient(create_app(path)) as client:
        payload = {"name": "방문자", "message": "좋은 하루 보내세요."}
        payload[field] = "씨.발"
        response = client.post("/api/entries", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"][0]["loc"] == ["body", field]
        assert POLICY_MESSAGE in response.json()["detail"][0]["msg"]
        assert client.get("/api/entries").json()["total"] == 0
        assert client.post("/api/entries", json={"name": "방문자", "message": "반가워요!"}).status_code == 201
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("entries",)]


def test_configurable_rules_and_literal_regex(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"custom": {"contains": ["금지테스트"], "words": ["a+b"]}}), encoding="utf-8")
    policy = TextPolicy(path)
    assert policy.blocked("금 지 테스트")
    assert policy.blocked("a+b")
    assert not policy.blocked("aaab")
    assert not policy.blocked("오늘도 반가워요")


@pytest.mark.parametrize("config", [{}, [], {"bad": {}}, {"bad": {"contains": "욕설", "words": []}}, {"bad": {"contains": [""], "words": []}}])
def test_invalid_policy_fails_instead_of_silently_disabling(tmp_path, config):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        TextPolicy(path)


def test_images_and_public_assets(tmp_path):
    with TestClient(create_app(tmp_path / "assets.sqlite3")) as client:
        for name in ["garden", "letter", "flowers"]:
            response = client.get(f"/static/images/{name}.jpg")
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("image/jpeg")
        assert client.get("/moderation.json").status_code == 404
    assert sum(path.stat().st_size for path in (ROOT / "static" / "images").iterdir()) < 400_000
