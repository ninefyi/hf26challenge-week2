"""Run the evaluation in EVAL.md and report it against the pre-set accuracy bar.

usage:
  uv run python eval.py run --set eval-set/manifest.csv [--lang th] [--model gemma3:12b]
  uv run python eval.py report [--run results/eval-<stamp>-....json] [--feedback results/feedback.jsonl]

The manifest is a CSV with columns: photo, place, note, truth
  photo  file name, relative to the manifest's folder
  place  the Place the Traveller types (empty for an ordinary view)
  note   the short Note
  truth  the real place name, only used to score the Place guess (empty if there is none)
"""
import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

from tripkit.evaluate import (MIN_AS_IS_RATE, accuracy_bar, auto_checks, guess_outcome, guess_summary,
                              summarize_run)
from tripkit.generate import MODEL, guess_place, make_kit

RESULTS = Path("results")
EXPECTED_PHOTOS = 20


def read_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    for r in rows:
        if not r.get("photo"):
            raise SystemExit(f"{path}: a row has no photo name")
        if not (path.parent / r["photo"]).is_file():
            raise SystemExit(f"{path}: photo not found: {path.parent / r['photo']}")
    return rows


def run(args: argparse.Namespace) -> None:
    manifest = Path(args.set)
    cases = read_manifest(manifest)
    ids = [hashlib.sha1((manifest.parent / c["photo"]).read_bytes()).hexdigest()[:10] for c in cases]
    if len(set(ids)) != len(ids):
        raise SystemExit("two rows use the same photo (same bytes); each photo must appear once")
    if len(cases) != EXPECTED_PHOTOS:
        print(f"warning: {len(cases)} photos, EVAL.md plans {EXPECTED_PHOTOS}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stem = f"eval-{stamp}-{args.model.replace(':', '_')}-{args.lang}"
    RESULTS.mkdir(exist_ok=True)
    rows = []
    for i, (case, photo_id) in enumerate(zip(cases, ids), 1):
        image = (manifest.parent / case["photo"]).read_bytes()
        guess = guess_place(image, args.lang, args.model)
        kit = make_kit(image, case["place"], case["note"], args.lang, args.model)
        row = {
            "photo": case["photo"], "photo_id": photo_id, "typed_place": case["place"], "note": case["note"],
            "truth": case["truth"], "guess": guess.place, "guess_confidence": guess.confidence,
            "guess_auto": guess_outcome(guess.place, case["truth"]), "guess_seconds": guess.seconds,
            "kit_seconds": kit.seconds, "attempts": kit.attempts, "warnings": kit.warnings,
            "kit": kit.kit, "checks": auto_checks(kit.kit, case["place"]),
        }
        rows.append(row)
        failed = [k for k, ok in row["checks"].items() if not ok]
        print(f"[{i}/{len(cases)}] {case['photo']}: guess={guess.place or '-'} ({row['guess_auto']}), "
              f"{guess.seconds + kit.seconds:.0f}s, rules {'ok' if not failed else 'FAILED ' + ','.join(failed)}",
              flush=True)

    out = RESULTS / f"{stem}.json"
    meta = {"stamp": stamp, "model": args.model, "lang": args.lang, "manifest": str(manifest)}
    out.write_text(json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    review = RESULTS / f"{stem}-guess-review.csv"
    with review.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["photo", "guess", "truth", "auto", "manual"])
        for r in rows:
            w.writerow([r["photo"], r["guess"], r["truth"], r["guess_auto"], ""])
    print(f"saved {out}\nsaved {review}  (fill the 'manual' column with hit / wrong / unknown, then run report)")
    print("Next: have the First user open the page, check each photo, and press the verdict button; "
          "then run: uv run python eval.py report")


def latest_run() -> Path:
    runs = sorted(p for p in RESULTS.glob("eval-*.json"))
    if not runs:
        raise SystemExit("no eval run found in results/; run `eval.py run` first")
    return runs[-1]


def read_review(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {r["photo"]: r["manual"].strip().lower() for r in csv.DictReader(f)
                if r.get("manual", "").strip().lower() in ("hit", "wrong", "unknown")}


def report(args: argparse.Namespace) -> None:
    run_path = Path(args.run) if args.run else latest_run()
    data = json.loads(run_path.read_text(encoding="utf-8"))
    rows = data["rows"]
    fb_path = Path(args.feedback)
    feedback = ([json.loads(line) for line in fb_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                if fb_path.is_file() else [])
    review_path = run_path.with_name(run_path.stem + "-guess-review.csv")
    manual = read_review(review_path)

    s = summarize_run(rows)
    g = guess_summary(rows, manual)
    bar = accuracy_bar(rows, feedback)
    n = s["photos"]
    lines = [
        f"# Evaluation report: {run_path.name}", "",
        f"Model `{data['meta']['model']}`, language `{data['meta']['lang']}`, {n} photos.", "",
        "## Accuracy bar (fixed in EVAL.md before any run)", "",
        f"- Post-as-is rate: {bar['verdicts']['as-is']} of {n} ({bar['as_is_rate']:.0%}); "
        f"needed at least {bar['needed_as_is']} ({MIN_AS_IS_RATE:.0%})",
        f"- Other verdicts: {bar['verdicts']['edited']} needed edits, {bar['verdicts']['unusable']} unusable",
        f"- Invented place names: {bar['invented_places']} (must be 0)",
        f"- **Status: {bar['status']}**",
    ]
    if bar["missing_verdict"]:
        lines.append(f"- No verdict yet for {len(bar['missing_verdict'])} photos: "
                     + ", ".join(bar["missing_verdict"]))
    lines += ["", "## Automatic rules", ""]
    for rule, count in s["rule_pass"].items():
        lines.append(f"- {rule}: {count} of {n}")
    lines += [f"- all rules at once: {s['all_rules_pass']} of {n}; needed a retry: {s['retried']}", "",
              "## Place guess (no threshold)", "",
              f"- hit {g['hit']}, wrong {g['wrong']}, unknown {g['unknown']} "
              f"({'hand-labelled where filled in' if manual else 'automatic labels only, review by hand'})", "",
              "## Time per photo (guess + kit)", "",
              f"- mean {s['seconds_mean']} s, median {s['seconds_median']} s, max {s['seconds_max']} s"]
    text = "\n".join(lines) + "\n"
    out = run_path.with_name(run_path.stem + "-report.md")
    out.write_text(text, encoding="utf-8")
    print(text + f"saved {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run", help="run the model over the evaluation set")
    p_run.add_argument("--set", default="eval-set/manifest.csv")
    p_run.add_argument("--model", default=MODEL)
    p_run.add_argument("--lang", default="th", choices=["th", "en"])
    p_run.set_defaults(func=run)
    p_rep = sub.add_parser("report", help="score a run against the accuracy bar")
    p_rep.add_argument("--run", default="")
    p_rep.add_argument("--feedback", default=str(RESULTS / "feedback.jsonl"))
    p_rep.set_defaults(func=report)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
