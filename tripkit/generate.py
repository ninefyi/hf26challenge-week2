"""Make a Place guess and a Post kit from a Trip photo with a local model via Ollama."""
import io
import json
import time
from dataclasses import dataclass, field

import ollama
from PIL import Image, ImageOps

from .validate import clean_hashtags, one_line, problems

MODEL = "gemma3:12b"
MAX_SIDE = 1024
RETRIES = 2

KIT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "caption": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "caption", "hashtags"],
}

GUESS_SCHEMA = {
    "type": "object",
    "properties": {
        "place": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low", "unknown"]},
    },
    "required": ["place", "confidence"],
}

GUESS_PROMPT = """Look at this travel photo. If it shows a place you recognise with confidence (a named landmark,
temple, island, park, building or town), give its name in {language}, as it is usually written.
If you do not recognise it, use "" for place and "unknown" for confidence. Do not guess from general scenery
(a beach, a forest, a street). Set confidence to high only when the place is clearly identifiable."""

KIT_PROMPT = """You help a traveller write a social media post about one trip photo.
Place (given by the traveller; do not change it, and do not mention any other place): "{place}"
Note from the traveller: "{note}"

Write everything in {language}. Return JSON with:
- title: a short title for the photo, based on what you see.
- caption: ONE sentence on a single line, at most {max_chars} characters, about what you see and feel.
  Do not invent facts, names or events that are not visible or in the Note. Avoid gendered polite
  particles such as ค่ะ or ครับ.
- hashtags: at least {min_tags} hashtags that fit the photo, each starting with '#', no spaces inside a hashtag.
  Mix {tag_mix}."""

LANGUAGES = {
    "th": ("Thai", "Thai and English hashtags (for example two Thai and one English)"),
    "en": ("English", "English hashtags only"),
}


@dataclass
class Guess:
    place: str
    confidence: str
    seconds: float


@dataclass
class Result:
    kit: dict
    warnings: list[str] = field(default_factory=list)
    attempts: int = 0
    seconds: float = 0.0


def prepare_image(data: bytes) -> bytes:
    """Fix rotation, shrink, and re-encode as JPEG without any EXIF (so GPS is never sent or kept)."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def guess_place(image_bytes: bytes, lang: str = "th", model: str = MODEL) -> Guess:
    """Suggest what place the photo shows. A suggestion only: the Traveller must confirm it."""
    start = time.monotonic()
    reply = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": GUESS_PROMPT.format(language=LANGUAGES[lang][0]),
                   "images": [prepare_image(image_bytes)]}],
        format=GUESS_SCHEMA,
        options={"temperature": 0},
    )
    data = json.loads(reply.message.content)
    place = one_line(data.get("place", ""))
    confidence = data.get("confidence", "unknown")
    if not place:
        confidence = "unknown"
    return Guess(place, confidence, round(time.monotonic() - start, 1))


def make_kit(image_bytes: bytes, place: str, note: str, lang: str = "th", model: str = MODEL) -> Result:
    """Write title, caption and hashtags. `place` is the Traveller's own text and is passed through as is."""
    language, tag_mix = LANGUAGES[lang]
    prompt = KIT_PROMPT.format(place=place or "(not given)", note=note or "(none)", language=language,
                               max_chars=120, min_tags=3, tag_mix=tag_mix)
    image = prepare_image(image_bytes)
    start = time.monotonic()
    kit: dict = {}
    issues: list[str] = []
    attempts = 0
    for attempts in range(1, RETRIES + 2):
        reply = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt, "images": [image]}],
            format=KIT_SCHEMA,
            options={"temperature": 0.4},
        )
        kit = json.loads(reply.message.content)
        issues = problems(kit)
        if not issues:
            break
    final = {
        "title": one_line(kit.get("title", "")),
        "place": place.strip(),
        "caption": one_line(kit.get("caption", "")),
        "hashtags": clean_hashtags(kit.get("hashtags", [])),
    }
    warnings = list(issues)
    if not final["place"]:
        warnings.append("no Place given")
    return Result(final, warnings, attempts, round(time.monotonic() - start, 1))
