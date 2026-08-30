from __future__ import annotations

import math
import os
import shutil
import subprocess
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

MODEL_NAME = "F1 Avatar Engine"
MODEL_VERSION = "0.1.0"


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


def avatar_dir(base: Path) -> Path:
    path = base / "avatar"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_avatar_image(base: Path, raw: bytes, filename: str = "avatar.jpg") -> Path:
    if not raw:
        raise ValueError("Immagine avatar vuota")
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError("Immagine avatar troppo grande (max 20 MB)")
    folder = avatar_dir(base)
    temp = folder / ("upload_" + Path(filename or "avatar.jpg").name)
    temp.write_bytes(raw)
    try:
        with Image.open(temp) as im:
            im.verify()
        with Image.open(temp) as im:
            rgb = im.convert("RGB")
            target = folder / "avatar.jpg"
            rgb.save(target, quality=94)
    finally:
        if temp.exists() and temp.name != "avatar.jpg":
            temp.unlink(missing_ok=True)
    return folder / "avatar.jpg"


def save_voice_sample(base: Path, raw: bytes, filename: str = "voice.wav") -> Path:
    if not raw:
        raise ValueError("Campione voce vuoto")
    if len(raw) > 30 * 1024 * 1024:
        raise ValueError("Campione voce troppo grande (max 30 MB)")
    suffix = Path(filename or "voice.wav").suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}:
        raise ValueError("Formato voce non supportato")
    target = avatar_dir(base) / ("voice_sample" + suffix)
    target.write_bytes(raw)
    return target


def model_status(base: Path) -> dict:
    model_root = base / "models" / "f1-avatar"
    neural_exe = Path(os.environ.get("F1_AVATAR_NEURAL_EXE", "").strip()) if os.environ.get("F1_AVATAR_NEURAL_EXE") else model_root / "F1AvatarNeural.exe"
    avatar = avatar_dir(base) / "avatar.jpg"
    voice_samples = list(avatar_dir(base).glob("voice_sample.*"))
    return {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "avatar_configured": avatar.exists(),
        "voice_sample_configured": bool(voice_samples),
        "neural_backend_ready": neural_exe.exists(),
        "neural_backend": "F1AvatarNeural local runtime" if neural_exe.exists() else "not installed",
        "fallback_backend": "F1Avatar Lite local renderer",
        "remote_provider": None,
    }


def _synthesize_windows(text: str, output_wav: Path) -> bool:
    if os.name != "nt":
        return False
    escaped = str(output_wav).replace('"', '`"')
    ps = f'''$v = New-Object -ComObject SAPI.SpVoice; $s = New-Object -ComObject SAPI.SpFileStream; $s.Open("{escaped}",3,$false); $v.AudioOutputStream=$s; $v.Rate=1; $v.Volume=100; $v.Speak(@'\n{text}\n'@); $s.Close()'''
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True, timeout=180)
        return output_wav.exists() and output_wav.stat().st_size > 1024
    except Exception:
        return False


def _audio_envelope(audio: Path, fps: int, total_frames: int) -> np.ndarray:
    envelope = np.zeros(total_frames, dtype=np.float32)
    if not audio.exists():
        return envelope
    try:
        with wave.open(str(audio), "rb") as wf:
            channels = wf.getnchannels(); rate = wf.getframerate(); width = wf.getsampwidth(); frames = wf.readframes(wf.getnframes())
        if width != 2:
            return envelope
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)
        samples /= 32768.0
        for i in range(total_frames):
            a = int((i / fps) * rate); b = int(((i + 1) / fps) * rate); chunk = samples[a:b]
            if chunk.size:
                envelope[i] = float(np.sqrt(np.mean(chunk * chunk)))
        peak = float(envelope.max())
        if peak > 1e-6:
            envelope = np.clip(envelope / peak, 0, 1)
        return envelope
    except Exception:
        return envelope


def _cover(im: Image.Image, size=(720, 1280), zoom=1.0) -> Image.Image:
    tw, th = size; im = im.convert("RGB")
    ratio = max(tw / im.width, th / im.height) * zoom
    nw, nh = max(tw, int(im.width * ratio)), max(th, int(im.height * ratio))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2); top = max(0, (nh - th) // 2)
    return resized.crop((left, top, left + tw, top + th))


def _render_lite(avatar_path: Path, script: str, output_dir: Path, duration: int, fps: int = 24) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    work = output_dir / "_avatar_work"; shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True, exist_ok=True)
    audio = work / "voice.wav"; has_audio = _synthesize_windows(script, audio)
    total_frames = max(1, int(duration * fps)); envelope = _audio_envelope(audio, fps, total_frames) if has_audio else np.zeros(total_frames, dtype=np.float32)
    base = Image.open(avatar_path).convert("RGB"); silent = work / "avatar_silent.mp4"
    writer = imageio.get_writer(str(silent), fps=fps, codec="libx264", quality=7, pixelformat="yuv420p", ffmpeg_log_level="error")
    title_font = _font(34, True)
    try:
        for i in range(total_frames):
            p = i / max(1, total_frames - 1); zoom = 1.015 + 0.02 * math.sin(p * math.pi * 2)
            frame = ImageEnhance.Contrast(_cover(base, (720, 1280), zoom)).enhance(1.02)
            draw = ImageDraw.Draw(frame, "RGBA")
            mouth_open = float(envelope[i]) if has_audio else (0.2 + 0.2 * max(0.0, math.sin(i * 0.45)))
            cx, cy, mw, mh = 360, 825, 94, int(8 + 34 * mouth_open)
            draw.ellipse((cx - mw // 2, cy - mh // 2, cx + mw // 2, cy + mh // 2), fill=(38, 8, 12, 155))
            if mh > 18: draw.ellipse((cx - 24, cy - 4, cx + 24, cy + 8), fill=(225, 120, 130, 120))
            draw.rounded_rectangle((26, 1125, 694, 1235), radius=24, fill=(0, 0, 0, 150))
            label = "F1 AVATAR · LOCAL"; box = draw.textbbox((0, 0), label, font=title_font)
            draw.text(((720 - (box[2]-box[0]))/2, 1158), label, font=title_font, fill="white")
            writer.append_data(np.asarray(frame))
    finally:
        writer.close(); base.close()
    final = output_dir / "avatar_video.mp4"
    if has_audio:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-y", "-i", str(silent), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(final)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        shutil.copy2(silent, final)
    return final


def _render_neural(base: Path, avatar_path: Path, script: str, output_dir: Path, duration: int) -> Path | None:
    model_root = base / "models" / "f1-avatar"
    neural_exe = Path(os.environ.get("F1_AVATAR_NEURAL_EXE", "").strip()) if os.environ.get("F1_AVATAR_NEURAL_EXE") else model_root / "F1AvatarNeural.exe"
    if not neural_exe.exists():
        return None
    output = output_dir / "avatar_video.mp4"
    cmd = [str(neural_exe), "--avatar", str(avatar_path), "--text", script, "--output", str(output), "--duration", str(duration)]
    voice_samples = list(avatar_dir(base).glob("voice_sample.*"))
    if voice_samples: cmd += ["--voice-sample", str(voice_samples[0])]
    subprocess.run(cmd, check=True, timeout=max(300, duration * 30))
    if not output.exists() or output.stat().st_size < 5000:
        raise RuntimeError("Il backend neurale locale non ha prodotto un video valido")
    return output


def render_avatar(base: Path, script: str, output_dir: Path, duration: int = 20) -> tuple[Path, str]:
    avatar_path = avatar_dir(base) / "avatar.jpg"
    if not avatar_path.exists():
        raise ValueError("Carica prima una foto avatar autorizzata")
    output_dir.mkdir(parents=True, exist_ok=True)
    neural = _render_neural(base, avatar_path, script, output_dir, duration)
    if neural: return neural, "neural"
    return _render_lite(avatar_path, script, output_dir, duration), "lite"
