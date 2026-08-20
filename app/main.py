import os, shutil, subprocess, uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.services.ai import transcribe_chinese, make_khmer_segments, make_tts
from app.services.media import make_timed_audio, make_srt, render_final

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))
MAX_BYTES = MAX_MB * 1024 * 1024

app = FastAPI(title="Chinese → Khmer Video AI")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/process")
async def process(video: UploadFile = File(...), style: str = Form("short")):
    if not video.filename:
        raise HTTPException(400, "No video selected")

    allowed = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
    ext = Path(video.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, "Unsupported video format")

    job = uuid.uuid4().hex
    work = DATA / job
    work.mkdir(parents=True, exist_ok=True)

    inp = work / f"input{ext}"
    audio = work / "audio.mp3"
    narration = work / "narration.wav"
    srt = work / "khmer.srt"
    final = work / "final.mp4"

    size = 0
    try:
        with inp.open("wb") as f:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, f"Video is larger than {MAX_MB} MB")
                f.write(chunk)

        run_ffmpeg([
            "ffmpeg", "-y", "-i", str(inp),
            "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
            str(audio)
        ])

        transcript = transcribe_chinese(audio)
        segments = make_khmer_segments(transcript)

        voices = []
        for i, seg in enumerate(segments):
            voice_path = work / f"voice_{i}.mp3"
            make_tts(seg["khmer"], voice_path)
            voices.append((seg, voice_path))

        make_timed_audio(voices, narration)
        make_srt(segments, srt)
        render_final(inp, narration, srt, final)

        return {
            "job_id": job,
            "segments": segments,
            "download_url": f"/api/download/{job}",
            "subtitle_url": f"/api/subtitles/{job}",
        }
    except HTTPException:
        raise
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, "FFmpeg failed while processing the video")
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")


@app.get("/api/download/{job}")
def download(job: str):
    path = DATA / job / "final.mp4"
    if not path.exists():
        raise HTTPException(404, "Video not found")
    return FileResponse(path, media_type="video/mp4", filename="khmer-video.mp4")


@app.get("/api/subtitles/{job}")
def subtitles(job: str):
    path = DATA / job / "khmer.srt"
    if not path.exists():
        raise HTTPException(404, "Subtitle not found")
    return FileResponse(path, media_type="application/x-subrip", filename="khmer.srt")


def run_ffmpeg(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
