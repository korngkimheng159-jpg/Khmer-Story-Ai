import subprocess


def srt_time(seconds):
    seconds = max(0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def make_srt(segments, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(
                f"{i}\n{srt_time(seg['start'])} --> {srt_time(seg['end'])}\n"
                f"{seg['khmer']}\n\n"
            )


def make_timed_audio(items, output_path):
    if not items:
        raise ValueError("No narration segments")

    cmd = ["ffmpeg", "-y"]
    for _, audio in items:
        cmd += ["-i", str(audio)]

    filters = []
    labels = []
    for i, (seg, _) in enumerate(items):
        delay = max(0, int(float(seg["start"]) * 1000))
        label = f"a{i}"
        filters.append(f"[{i}:a]adelay={delay}|{delay}[{label}]")
        labels.append(f"[{label}]")

    mix = "".join(labels)
    filter_complex = ";".join(filters) + (
        f";{mix}amix=inputs={len(items)}:duration=longest:normalize=0,"
        f"apad[a]"
    )

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[a]",
        "-ar", "48000",
        "-ac", "2",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def render_final(video, narration, subtitle, output):
    # Burn Khmer subtitles and replace the original audio with Khmer narration.
    subtitle_filter = str(subtitle).replace("\\", "\\\\").replace(":", "\\:")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(narration),
        "-vf", f"subtitles={subtitle_filter}",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
