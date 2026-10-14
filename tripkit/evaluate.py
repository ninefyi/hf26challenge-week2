"""Scoring for the evaluation in EVAL.md. Pure functions: no model calls, no file reads."""
import re
import statistics

from .validate import MAX_CAPTION_CHARS, MIN_HASHTAGS, clean_hashtags, one_line

# Fixed in EVAL.md before any evaluation run. Do not change after seeing results.
MIN_AS_IS_RATE = 0.70
MAX_INVENTED_PLACES = 0


def auto_checks(kit: dict, typed_place: str) -> dict[str, bool]:
    """Machine-checkable rules for one Post kit."""
    tags = kit.get("hashtags", [])
    caption = kit.get("caption", "")
    return {
        "title": bool(kit.get("title", "").strip()),
        "hashtags": len(clean_hashtags(tags)) >= MIN_HASHTAGS
        and all(t.startswith("#") and not re.search(r"\s", t) for t in tags),
        "caption": bool(caption.strip()) and "\n" not in caption.strip()
        and len(one_line(caption)) <= MAX_CAPTION_CHARS,
        # An invented place is a Place on the kit that the Traveller did not type.
        "place_not_invented": one_line(kit.get("place", "")) == one_line(typed_place),
    }


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def guess_outcome(guess: str, truth: str) -> str:
    """First-pass label for a Place guess: 'hit', 'wrong' or 'unknown'. Review it by hand:
    Thai place names have many spellings, so a substring match is only a starting point."""
    guess_n, truth_n = _norm(guess), _norm(truth)
    if not guess_n or guess_n == "unknown":
        return "unknown"
    if not truth_n:  # the photo has no named place, so any named guess is wrong
        return "wrong"
    return "hit" if truth_n in guess_n or guess_n in truth_n else "wrong"


def summarize_run(rows: list[dict]) -> dict:
    """Aggregate one run (a list of per-photo rows made by eval.py)."""
    n = len(rows)
    seconds = [r["guess_seconds"] + r["kit_seconds"] for r in rows]
    rules = ("title", "hashtags", "caption", "place_not_invented")
    return {
        "photos": n,
        "rule_pass": {rule: sum(r["checks"][rule] for r in rows) for rule in rules},
        "all_rules_pass": sum(all(r["checks"].values()) for r in rows),
        "invented_places": sum(not r["checks"]["place_not_invented"] for r in rows),
        "retried": sum(r["attempts"] > 1 for r in rows),
        "seconds_mean": round(statistics.mean(seconds), 1) if seconds else 0.0,
        "seconds_median": round(statistics.median(seconds), 1) if seconds else 0.0,
        "seconds_max": round(max(seconds), 1) if seconds else 0.0,
    }


def guess_summary(rows: list[dict], manual: dict[str, str] | None = None) -> dict[str, int]:
    """Count hit / wrong / unknown. A hand label (by photo name) overrides the automatic one."""
    manual = manual or {}
    counts = {"hit": 0, "wrong": 0, "unknown": 0}
    for r in rows:
        label = manual.get(r["photo"]) or r["guess_auto"]
        counts[label] = counts.get(label, 0) + 1
    return counts


def latest_verdicts(feedback: list[dict]) -> dict[str, dict]:
    """Last saved feedback row per photo (a person may re-check a photo). Keyed by photo_id, and also
    by `name:<file name>` as a fallback in case the uploaded bytes hash differently."""
    latest: dict[str, dict] = {}
    for row in feedback:
        latest[row["photo_id"]] = row
        if row.get("photo_name"):
            latest[f"name:{row['photo_name']}"] = row
    return latest


def accuracy_bar(rows: list[dict], feedback: list[dict]) -> dict:
    """Compare the run with the First user's verdicts against the bar in EVAL.md."""
    verdicts = latest_verdicts(feedback)
    n = len(rows)
    counts = {"as-is": 0, "edited": 0, "unusable": 0}
    missing = []
    for r in rows:
        fb = verdicts.get(r["photo_id"]) or verdicts.get(f"name:{r['photo']}")
        if fb is None:
            missing.append(r["photo"])
        else:
            counts[fb["verdict"]] = counts.get(fb["verdict"], 0) + 1
    rate = counts["as-is"] / n if n else 0.0
    invented = sum(not r["checks"]["place_not_invented"] for r in rows)
    meets = rate >= MIN_AS_IS_RATE and invented <= MAX_INVENTED_PLACES
    status = ("INCOMPLETE" if missing else ("MET" if meets else "NOT MET"))
    return {
        "photos": n,
        "verdicts": counts,
        "missing_verdict": missing,
        "as_is_rate": round(rate, 3),
        "needed_as_is": -(-int(MIN_AS_IS_RATE * 100) * n // 100),  # ceiling of 70% of n
        "invented_places": invented,
        "status": status,
    }
