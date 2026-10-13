"""Model spike: Place guess and Post kit over a folder of photos; saves raw results.

usage: uv run python spike.py [--model gemma3:12b] [--lang th]
"""
import argparse
import json
from pathlib import Path

from tripkit.generate import MODEL, guess_place, make_kit

PHOTOS = Path("spike-photos")
RESULTS = Path("results")

# True place (author's knowledge of the public sample photos) and a Note. Two photos have no
# recognisable named place on purpose: the right answer there is "unknown".
CASES = {
    "ayutthaya.jpg": ("พระนครศรีอยุธยา", "อากาศร้อนมาก"),
    "santichaiprakarn.jpg": ("พระที่นั่งสันติไชยปราการ", "ตอนเย็น"),
    "thung_salaeng_luang.jpg": ("ทุ่งแสลงหลวง", "หมอกลงตอนเช้า"),
    "phi_phi_lay.jpg": ("เกาะพีพีเล", "ทะเลสวยมาก"),
    "tapu_phuket.jpg": ("", "นั่งเรือผ่านเกาะแปลก ๆ ทะเลใส"),
    "chiangmai_library.jpg": ("", "ห้องสมุดเก่าแก่ เงียบมาก"),
}
# What the Commons file page says the photo shows; used only to score the guesses by hand.
TRUTH = {
    "ayutthaya.jpg": "Ayutthaya (ruins)",
    "santichaiprakarn.jpg": "Santichaiprakarn Throne Hall, Bangkok",
    "thung_salaeng_luang.jpg": "Thung Salaeng Luang",
    "phi_phi_lay.jpg": "Phi Phi Lay island",
    "tapu_phuket.jpg": "Ko Tapu / Tapu island, Phuket (per file name)",
    "chiangmai_library.jpg": "Buddhist Manuscript Library and Museum, Chiang Mai",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--lang", default="th", choices=["th", "en"])
    args = parser.parse_args()

    RESULTS.mkdir(exist_ok=True)
    rows = []
    for name, (true_place, note) in CASES.items():
        image = (PHOTOS / name).read_bytes()
        guess = guess_place(image, args.lang, args.model)
        # The Traveller types the true place if they know it; the guess is never fed to the kit.
        kit = make_kit(image, true_place, note, args.lang, args.model)
        row = {"photo": name, "truth": TRUTH[name], "typed_place": true_place, "note": note, "model": args.model,
               "lang": args.lang, "guess": guess.__dict__, "kit_seconds": kit.seconds,
               "attempts": kit.attempts, "warnings": kit.warnings, "kit": kit.kit}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    out = RESULTS / f"spike2-{args.model.replace(':', '_')}-{args.lang}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(r["guess"]["seconds"] + r["kit_seconds"] for r in rows) / len(rows)
    print(f"saved {out}; mean {total:.1f}s per photo (guess + kit)")


if __name__ == "__main__":
    main()
