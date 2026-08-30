from pathlib import Path
import io
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import main


def test_app_smoke_routes():
    client = main.app.test_client()
    assert client.get("/").status_code == 200
    health = client.get("/api/health")
    assert health.status_code == 200
    payload = health.get_json()
    assert payload["status"] == "ok"
    assert payload["avatar_engine"] == "F1 Avatar Engine"
    assert payload["local_only"] is True
    assert client.get("/api/settings").status_code == 200
    assert client.get("/api/avatar/status").status_code == 200
    assert client.post("/api/import", json={"url": "not-a-url"}).status_code == 400
    assert client.post("/api/render/local", json={"product": {}, "concept": {}}).status_code == 400


def test_avatar_profile_and_render_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_BASE", tmp_path)
    monkeypatch.setattr(main, "OUTPUT", tmp_path / "output")
    main.OUTPUT.mkdir(parents=True, exist_ok=True)
    class DummyThread:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass
    monkeypatch.setattr(main.threading, "Thread", DummyThread)
    img = Image.new("RGB", (128, 128), "white")
    buf = io.BytesIO(); img.save(buf, format="JPEG"); buf.seek(0)
    client = main.app.test_client()
    r = client.post("/api/avatar/profile", data={"avatar": (buf, "avatar.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 200
    assert r.get_json()["avatar_configured"] is True
    r = client.post("/api/render/avatar", json={"product": {"title": "X"}, "concept": {"script": "Y"}, "duration": 8})
    assert r.status_code == 200
