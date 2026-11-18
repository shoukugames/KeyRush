#!/usr/bin/env python3
"""Build the browser version into build/web/ with pygbag.

1. Renders every sound once into web_sounds/*.ogg (making them takes seconds even on a PC,
   too slow for a browser), plus web_sounds/index.json.
2. Runs pygbag, which packs the game folder into build/web/ (index.html + keyrush.apk).

Needs: pygame, pygbag (python3 -m pip install pygbag) and ffmpeg on PATH (or FFMPEG=/path).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from keyrush import audio  # noqa: E402


def render_sounds():
    ffmpeg = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("ffmpeg not found (set FFMPEG=/path/to/ffmpeg)")
    out = os.path.join(ROOT, "web_sounds")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    sounds = audio.build_all()
    with tempfile.TemporaryDirectory() as tmp:
        for name, data in sounds.items():
            wav = os.path.join(tmp, f"{name}.wav")
            with wave.open(wav, "wb") as handle:
                handle.setnchannels(2)
                handle.setsampwidth(2)
                handle.setframerate(audio.SAMPLE_RATE)
                handle.writeframes(bytes(data))
            subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "4",
                            os.path.join(out, f"{name}.ogg")], check=True)
    with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as handle:
        json.dump(sorted(sounds), handle)
    size = sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out))
    print(f"web_sounds: {len(sounds)} sounds, {size // 1024} KB")


def run_pygbag():
    subprocess.run([sys.executable, "-m", "pygbag", "--build", "--title", "Key Rush", "--app_name", "keyrush",
                    "--icon", "assets/icon.png", "."], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print("build/web ready: upload index.html, keyrush.apk, keyrush.tar.gz and favicon.png")


if __name__ == "__main__":
    render_sounds()
    run_pygbag()
