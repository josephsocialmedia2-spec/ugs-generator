from __future__ import annotations

import argparse
import json
import os
import tempfile
import threading
import time
import uuid
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from ai_engine import generate_concepts
from avatar_engine import model_status, render_avatar, save_avatar_image, save_voice_sample
from runtime import data_root, resource_root
from settings_store import load_settings, public_settings, save_settings
from shopify_admin import list_products
from shopify_import import fetch_product
from video_engine import render_video

RESOURCE_BASE = resource_root()
DATA_BASE = data_root()
OUTPUT = DATA_BASE / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder=str(RESOURCE_BASE / "templates"), static_folder=str(RESOURCE_BASE / "static"))
JOBS: dict[str, dict] = {}


def save_job(job_id: str):
    folder = OUTPUT / job_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "job.json").write_text(json.dumps(JOBS[job_id], ensure_ascii=False, indent=2), encoding="utf-8")


def _load_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        file = OUTPUT / job_id / "job.json"
        if file.exists():
            job = json.loads(file.read_text(encoding="utf-8"))
            JOBS[job_id] = job
    return job


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def api_health():
    return jsonify({"status": "ok", "version": "2.2.0", "avatar_engine": "F1 Avatar Engine", "local_only": True})


@app.get("/api/settings")
def api_settings_get():
    data = public_settings(load_settings(DATA_BASE))
    data["avatar"] = model_status(DATA_BASE)
    return jsonify(data)


@app.post("/api/settings")
def api_settings_save():
    data = request.get_json(force=True) or {}
    existing = load_settings(DATA_BASE)
    updates = {}
    for key in ["shopify_shop", "avatar_name", "avatar_voice_mode"]:
        if key in data:
            updates[key] = data.get(key)
    if str(data.get("shopify_access_token") or "").strip():
        updates["shopify_access_token"] = data["shopify_access_token"]
    elif data.get("clear_shopify_token"):
        updates["shopify_access_token"] = ""
    current = save_settings(DATA_BASE, {**existing, **updates})
    response = public_settings(current)
    response["avatar"] = model_status(DATA_BASE)
    return jsonify(response)


@app.get("/api/avatar/status")
def api_avatar_status():
    return jsonify(model_status(DATA_BASE))


@app.post("/api/avatar/profile")
def api_avatar_profile():
    try:
        image = request.files.get("avatar")
        voice = request.files.get("voice")
        if image and image.filename:
            save_avatar_image(DATA_BASE, image.read(), image.filename)
        if voice and voice.filename:
            save_voice_sample(DATA_BASE, voice.read(), voice.filename)
        if not image and not voice:
            return jsonify({"error": "Seleziona almeno una foto avatar o un campione voce."}), 400
        return jsonify(model_status(DATA_BASE))
    except Exception as exc:
        return jsonify({"error": f"Profilo avatar non salvato: {exc}"}), 400


@app.post("/api/import")
def api_import():
    data = request.get_json(force=True)
    url = str(data.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Inserisci un URL prodotto Shopify valido."}), 400
    try:
        product = fetch_product(url).to_dict()
        return jsonify({"product": product})
    except Exception as exc:
        return jsonify({"error": f"Importazione non riuscita: {exc}"}), 500


@app.get("/api/shopify/catalog")
def api_shopify_catalog():
    settings = load_settings(DATA_BASE)
    try:
        products = list_products(settings.get("shopify_shop", ""), settings.get("shopify_access_token", ""), search=str(request.args.get("q") or ""), limit=int(request.args.get("limit") or 30))
        return jsonify({"products": products})
    except Exception as exc:
        return jsonify({"error": f"Catalogo Shopify non disponibile: {exc}"}), 400


@app.post("/api/concepts")
def api_concepts():
    data = request.get_json(force=True)
    product = data.get("product") or {}
    if not product.get("title"):
        return jsonify({"error": "Prima importa o scegli un prodotto."}), 400
    concepts = generate_concepts(product, audience=str(data.get("audience") or ""), language=str(data.get("language") or "Italiano"), count=int(data.get("count") or 3), model=os.environ.get("UGC_OLLAMA_MODEL", "qwen2.5-coder:7b"), base_url=os.environ.get("UGC_OLLAMA_URL", "http://127.0.0.1:11434"))
    return jsonify({"concepts": [c.to_dict() for c in concepts]})


def _new_job(mode: str, product: dict, concept: dict, duration: int) -> str:
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"id": job_id, "mode": mode, "status": "queued", "created_at": time.time(), "product": product, "concept": concept, "duration": duration}
    save_job(job_id)
    return job_id


def _render_local_job(job_id: str, product: dict, concept: dict, duration: int):
    try:
        JOBS[job_id]["status"] = "rendering_local"; save_job(job_id)
        video = render_video(product, concept, OUTPUT / job_id, duration=duration)
        JOBS[job_id].update({"status": "ready", "video": str(video), "engine": "ugc_motion", "finished_at": time.time()}); save_job(job_id)
    except Exception as exc:
        JOBS[job_id]["status"] = "error"; JOBS[job_id]["error"] = str(exc); save_job(job_id)


def _render_avatar_job(job_id: str, product: dict, concept: dict, duration: int):
    try:
        JOBS[job_id]["status"] = "avatar_preparing"; save_job(job_id)
        video, backend = render_avatar(DATA_BASE, str(concept.get("script") or ""), OUTPUT / job_id, duration=duration)
        JOBS[job_id].update({"status": "ready", "video": str(video), "engine": "f1_avatar", "avatar_backend": backend, "finished_at": time.time()}); save_job(job_id)
    except Exception as exc:
        JOBS[job_id]["status"] = "error"; JOBS[job_id]["error"] = str(exc); save_job(job_id)


@app.post("/api/render/local")
def api_render_local():
    data = request.get_json(force=True); product = data.get("product") or {}; concept = data.get("concept") or {}; duration = max(8, min(30, int(data.get("duration") or 18)))
    if not product.get("title") or not concept.get("script"):
        return jsonify({"error": "Prodotto o concept mancanti."}), 400
    job_id = _new_job("local", product, concept, duration)
    threading.Thread(target=_render_local_job, args=(job_id, product, concept, duration), daemon=True).start()
    return jsonify({"job_id": job_id, "status": "queued"})


@app.post("/api/render/avatar")
def api_render_avatar():
    data = request.get_json(force=True); product = data.get("product") or {}; concept = data.get("concept") or {}; duration = max(8, min(60, int(data.get("duration") or 20)))
    if not product.get("title") or not concept.get("script"):
        return jsonify({"error": "Prodotto o concept mancanti."}), 400
    if not model_status(DATA_BASE).get("avatar_configured"):
        return jsonify({"error": "Carica prima una foto nel profilo F1 Avatar."}), 400
    job_id = _new_job("f1_avatar", product, concept, duration)
    threading.Thread(target=_render_avatar_job, args=(job_id, product, concept, duration), daemon=True).start()
    return jsonify({"job_id": job_id, "status": "queued"})


@app.post("/api/render")
def api_render_compat():
    return api_render_local()


@app.get("/api/jobs/<job_id>")
def api_job(job_id: str):
    job = _load_job(job_id)
    if not job:
        return jsonify({"error": "Job non trovato"}), 404
    response = dict(job); response.pop("video", None)
    if job.get("status") == "ready": response["download_url"] = f"/download/{job_id}"
    return jsonify(response)


@app.get("/download/<job_id>")
def download(job_id: str):
    job = _load_job(job_id) or {}
    if job.get("mode") == "f1_avatar": path = OUTPUT / job_id / "avatar_video.mp4"; name = f"F1_AVATAR_{job_id}.mp4"
    else: path = OUTPUT / job_id / "ugc_video.mp4"; name = f"UGC_LOCAL_{job_id}.mp4"
    if not path.exists(): return "Video non ancora disponibile", 404
    return send_file(path, as_attachment=True, download_name=name)


def run_self_test() -> bool:
    try:
        client = app.test_client()
        checks = [client.get("/"), client.get("/api/health"), client.get("/api/settings"), client.get("/api/avatar/status")]
        if any(r.status_code != 200 for r in checks): return False
        health = checks[1].get_json() or {}
        if health.get("local_only") is not True or health.get("avatar_engine") != "F1 Avatar Engine": return False
        if client.post("/api/import", json={"url": "not-a-url"}).status_code != 400: return False
        if client.post("/api/render/avatar", json={"product": {"title": "X"}, "concept": {"script": "Y"}}).status_code != 400: return False
        with tempfile.TemporaryDirectory(prefix="shopify-ugc-selftest-") as tmp:
            video = render_video({"title": "Self Test Product", "images": []}, {"hook": "Self test", "script": "Verifica automatica del motore video locale.", "cta": "OK", "scenes": ["Hook", "Demo", "CTA"]}, Path(tmp), duration=2, fps=3)
            if not video.exists() or video.stat().st_size < 5000: return False
        return True
    except Exception:
        return False


def _open_browser_later():
    time.sleep(1.2)
    try: webbrowser.open("http://127.0.0.1:7865")
    except Exception: pass


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Shopify UGC Studio"); parser.add_argument("--self-test", action="store_true"); parser.add_argument("--no-browser", action="store_true"); args = parser.parse_args(argv)
    if args.self_test:
        ok = run_self_test(); print("SELF_TEST_OK" if ok else "SELF_TEST_FAILED"); return 0 if ok else 1
    if not args.no_browser: threading.Thread(target=_open_browser_later, daemon=True).start()
    app.run(host="127.0.0.1", port=7865, debug=False, threaded=True, use_reloader=False); return 0


if __name__ == "__main__": raise SystemExit(cli())
