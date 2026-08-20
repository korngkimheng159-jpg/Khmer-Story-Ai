import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def transcribe_chinese(audio_path):
    with open(audio_path, "rb") as f:
        return client.audio.transcriptions.create(
            model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe"),
            file=f,
            language="zh",
            response_format="verbose_json",
        )


def make_khmer_segments(transcript, style):
    source = []
    for item in (getattr(transcript, "segments", None) or []):
        source.append({
            "start": float(item.start),
            "end": float(item.end),
            "text": item.text.strip(),
        })

    if not source:
        text = getattr(transcript, "text", "") or ""
        source = [{"start": 0, "end": 30, "text": text}]

    instruction = {
        "short": "សម្រាយខ្លី និងទាក់ទាញ សមសម្រាប់ TikTok/Shorts។",
        "normal": "សម្រាយធម្មតា រក្សាចំណុចសំខាន់ៗ និងស្តាប់ធម្មជាតិ។",
        "detail": "សម្រាយលម្អិតជាងមុន ប៉ុន្តែកុំប្រឌិតព័ត៌មាន។",
    }.get(style, "សម្រាយខ្លី និងធម្មជាតិ។")

    prompt = f"""
អ្នកជាអ្នកសម្រាយវីដេអូចិនជាភាសាខ្មែរ។
{instruction}
រក្សាអត្ថន័យពិតពី transcript។ កុំបន្ថែមព័ត៌មានដែលមិនមាន។
រក្សា start/end របស់ segment ដើម។ សរសេរខ្មែរឲ្យខ្លីគ្រប់គ្រាន់សម្រាប់និយាយក្នុងពេលវេលានោះ។

Return ONLY valid JSON array:
[
  {{"start": 0.0, "end": 2.5, "khmer": "ស្គ្រីបខ្មែរ"}}
]

Timestamped Chinese transcript:
{json.dumps(source, ensure_ascii=False)}
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_TEXT_MODEL", "gpt-5.6-luna"),
        input=prompt,
    )

    data = json.loads(response.output_text)
    cleaned = []
    for s in data:
        start = float(s["start"])
        end = float(s["end"])
        if end > start and str(s["khmer"]).strip():
            cleaned.append({
                "start": start,
                "end": end,
                "khmer": str(s["khmer"]).strip(),
            })
    return cleaned


def make_tts(text, output_path):
    speech = client.audio.speech.create(
        model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
        input=text,
        instructions="Speak clearly and naturally in Khmer as a short-video narrator. Do not imitate a real person's identity.",
    )
    speech.stream_to_file(output_path)
