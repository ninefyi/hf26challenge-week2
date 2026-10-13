"""Pure helpers for the web page: the text to paste, and the record for the evaluation log."""
import hashlib
import json
import time
from pathlib import Path

from .validate import clean_hashtags, one_line

FIELDS = ("title", "place", "caption", "hashtags")


def parse_hashtags(text: str) -> list[str]:
    """Hashtags typed in one box, separated by spaces or commas."""
    return clean_hashtags(text.replace(",", " ").split())


def post_text(title: str, place: str, caption: str, hashtags: str) -> str:
    """The text a Traveller pastes into their own social account."""
    lines = [one_line(title), f"📍 {one_line(place)}" if one_line(place) else "", one_line(caption),
             " ".join(parse_hashtags(hashtags))]
    return "\n".join(line for line in lines if line)


def edited_fields(generated: dict, final: dict) -> list[str]:
    """Names of the fields the Traveller changed after generation."""
    changed = []
    for name in FIELDS:
        before, after = generated.get(name, ""), final.get(name, "")
        if name == "hashtags":
            before, after = (" ".join(parse_hashtags(" ".join(v) if isinstance(v, list) else v))
                             for v in (before, after))
        else:
            before, after = one_line(before), one_line(after)
        if before != after:
            changed.append(name)
    return changed


def feedback_record(image_bytes: bytes, lang: str, verdict: str, generated: dict, final: dict,
                    guess_place: str, typed_note: str) -> dict:
    """One row of the evaluation log. No photo, no GPS: only a short hash to tell photos apart."""
    changed = edited_fields(generated, final)
    place = one_line(final.get("place", ""))
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "photo_id": hashlib.sha1(image_bytes).hexdigest()[:10],
        "lang": lang,
        "verdict": verdict,  # "as-is" | "edited" | "unusable", chosen by the person
        "edited_fields": changed,
        "place_source": ("none" if not place else
                         "guess" if guess_place and place == one_line(guess_place) else "typed"),
        "guess_place": guess_place,
        "note": typed_note,
        "generated": generated,
        "final": final,
    }


def append_log(record: dict, path: Path) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
