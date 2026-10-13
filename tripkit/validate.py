"""Rules a Post kit must satisfy (see EVAL.md). Pure functions, no model calls."""
import re

MIN_HASHTAGS = 3
MAX_CAPTION_CHARS = 120


def clean_hashtag(tag: str) -> str:
    """Make one hashtag: leading '#', no spaces or other '#'. Empty if nothing is left."""
    body = re.sub(r"\s+", "", tag).replace("#", "")
    return f"#{body}" if body else ""


def clean_hashtags(tags: list[str]) -> list[str]:
    """Clean every hashtag, drop empties, drop duplicates (case-insensitive), keep order."""
    seen: set[str] = set()
    out: list[str] = []
    for tag in tags:
        tag = clean_hashtag(tag)
        if tag and tag.casefold() not in seen:
            seen.add(tag.casefold())
            out.append(tag)
    return out


def one_line(text: str) -> str:
    return " ".join(text.split())


def problems(kit: dict) -> list[str]:
    """Hard failures that should trigger a retry. An empty Place is a warning, not a failure."""
    found: list[str] = []
    if not kit.get("title", "").strip():
        found.append("empty title")
    caption = kit.get("caption", "")
    if not caption.strip():
        found.append("empty caption")
    if "\n" in caption.strip():
        found.append("caption is not a single line")
    if len(one_line(caption)) > MAX_CAPTION_CHARS:
        found.append(f"caption longer than {MAX_CAPTION_CHARS} characters")
    if len(clean_hashtags(kit.get("hashtags", []))) < MIN_HASHTAGS:
        found.append(f"fewer than {MIN_HASHTAGS} hashtags")
    return found
