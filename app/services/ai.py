import os
import requests


def transcribe_chinese(audio_file):
    """
    Transcribe Chinese audio.
    Returns text.
    """
    api_url = os.getenv("TRANSCRIBE_API_URL")

    if not api_url:
        return ""

    try:
        with open(audio_file, "rb") as f:
            response = requests.post(
                api_url,
                files={"file": f},
                timeout=120
            )

        response.raise_for_status()
        data = response.json()

        return data.get("text", "")

    except Exception as e:
        print(f"transcribe_chinese error: {e}")
        return ""


def make_khmer_segments(text):
    """
    Convert text into Khmer segments.
    """
    if not text:
        return []

    # Split into manageable segments
    segments = []
    current = ""

    for sentence in text.replace("。", "។").split("។"):
        sentence = sentence.strip()

        if not sentence:
            continue

        current += sentence + "។"

        if len(current) >= 120:
            segments.append(current.strip())
            current = ""

    if current.strip():
        segments.append(current.strip())

    return segments


def make_tts(text, output_file):
    """
    Create TTS audio.
    """
    api_url = os.getenv("TTS_API_URL")

    if not api_url or not text:
        return False

    try:
        response = requests.post(
            api_url,
            json={"text": text},
            timeout=120
        )

        response.raise_for_status()

        with open(output_file, "wb") as f:
            f.write(response.content)

        return True

    except Exception as e:
        print(f"make_tts error: {e}")
        return False
