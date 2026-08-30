from __future__ import annotations

import math
import shutil
import subprocess
import textwrap
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFont


def _font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def download_images(urls: list[str], directory: Path, limit: int = 6) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    out = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for i, url in enumerate(urls[:limit]):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            path = directory / f"product_{i+1}.jpg"
            path.write_bytes(r.content)
            with Image.open(path) as im:
                im.verify()
            out.append(path)
        except Exception:
            continue
    return out


def _tts_windows(text: str, output_wav: Path) -> bool:
    ps = f'''$v = New-Object -ComObject SAPI.SpVoice; $s = New-Object -ComObject SAPI.SpFileStream; $s.Open("{str(output_wav).replace('"','`"')}",3,$false); $v.AudioOutputStream=$s; $v.Rate=1; $v.Volume=100; $v.Speak(@'\n{text}\n'@); $s.Close()'''
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True, timeout=120)
        return output_wav.exists() and output_wav.stat().st_size > 1024
    except Exception:
        return False


def _cover(im: Image.Image, size=(720, 1280), zoom=1.0) -> Image.Image:
    target_w, target_h = size
    im = im.convert("RGB")
    ratio = max(target_w / im.width, target_h / im.height) * zoom
    new_size = (max(target_w, int(im.width * ratio)), max(target_h, int(im.height * ratio)))
    im = im.resize(new_size, Image.Resampling.LANCZOS)
    left = max(0, (im.width - target_w) // 2)
    top = max(0, (im.height - target_h) // 2)
    return im.crop((left, top, left + target_w, top + target_h))


def _draw_text_panel(frame: Image.Image, hook: str, subtitle: str, cta: str, progress: float) -> Image.Image:
    draw = ImageDraw.Draw(frame, "RGBA")
    w, h = frame.size
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 28))

    hook_font = _font(48, True)
    sub_font = _font(34, True)
    cta_font = _font(30, True)

    hook_lines = textwrap.wrap(hook, width=24)[:3]
    hook_h = len(hook_lines) * 58 + 24
    draw.rounded_rectangle((34, 46, w - 34, 46 + hook_h), radius=24, fill=(0, 0, 0, 170))
    y = 60
    for line in hook_lines:
        box = draw.textbbox((0, 0), line, font=hook_font)
        tw = box[2] - box[0]
        draw.text(((w - tw) / 2, y), line, font=hook_font, fill="white")
        y += 58

    sub_lines = textwrap.wrap(subtitle, width=34)[:4]
    panel_h = len(sub_lines) * 44 + 32
    panel_y = h - panel_h - 145
    draw.rounded_rectangle((28, panel_y, w - 28, panel_y + panel_h), radius=22, fill=(0, 0, 0, 185))
    y = panel_y + 16
    for line in sub_lines:
        box = draw.textbbox((0, 0), line, font=sub_font)
        tw = box[2] - box[0]
        draw.text(((w - tw) / 2, y), line, font=sub_font, fill="white")
        y += 44

    if progress > 0.76:
        cta_box = (110, h - 112, w - 110, h - 46)
        draw.rounded_rectangle(cta_box, radius=28, fill=(255, 255, 255, 235))
        box = draw.textbbox((0, 0), cta, font=cta_font)
        tw = box[2] - box[0]
        draw.text(((w - tw) / 2, h - 99), cta, font=cta_font, fill=(10, 10, 10))

    draw.rectangle((0, h - 10, int(w * progress), h), fill=(255, 255, 255, 230))
    return frame


def render_video(product: dict, concept: dict, output_dir: Path, duration: int = 18, fps: int = 24) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    work = output_dir / "_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    images = download_images(product.get("images") or [], work / "images")
    if not images:
        placeholder = Image.new("RGB", (900, 1200), "white")
        d = ImageDraw.Draw(placeholder)
        title_font = _font(54, True)
        d.multiline_text((80, 480), product.get("title", "Prodotto Shopify"), font=title_font, fill="black", spacing=10)
        p = work / "images" / "placeholder.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        placeholder.save(p, quality=92)
        images = [p]

    scene_texts = concept.get("scenes") or []
    if not scene_texts:
        scene_texts = [concept.get("hook", "Guarda questo"), concept.get("script", ""), concept.get("cta", "Scopri di più")]

    silent = work / "silent.mp4"
    writer = imageio.get_writer(str(silent), fps=fps, codec="libx264", quality=7, pixelformat="yuv420p", ffmpeg_log_level="error")
    total_frames = duration * fps
    per_scene = max(1, total_frames // max(1, len(scene_texts)))

    opened = [Image.open(p).convert("RGB") for p in images]
    try:
        for frame_idx in range(total_frames):
            progress = frame_idx / max(1, total_frames - 1)
            scene_idx = min(len(scene_texts) - 1, frame_idx // per_scene)
            local = (frame_idx % per_scene) / max(1, per_scene - 1)
            base = opened[scene_idx % len(opened)]
            zoom = 1.0 + 0.055 * local
            frame = _cover(base, (720, 1280), zoom)
            frame = ImageEnhance.Contrast(frame).enhance(1.03)
            subtitle = scene_texts[scene_idx]
            frame = _draw_text_panel(frame, concept.get("hook", ""), subtitle, concept.get("cta", "Scopri di più"), progress)
            writer.append_data(np.asarray(frame))
    finally:
        writer.close()
        for im in opened:
            im.close()

    audio = work / "voice.wav"
    final = output_dir / "ugc_video.mp4"
    if _tts_windows(concept.get("script", ""), audio):
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg, "-y", "-i", str(silent), "-i", str(audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(final)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        shutil.copy2(silent, final)
    return final
