# tripkit: a post kit for your trip photo

Upload a trip photo and get a **title, the place, a one-sentence caption and at least 3 hashtags** to paste into your own social account. Thai by default, with an English switch.

The model is [Gemma 3 12B](https://ollama.com/library/gemma3) running on your own computer through [Ollama](https://ollama.com). Your photo is not sent anywhere else.

Built for the [Hacktoberfest Open-Source AI Challenge: Week 2, "Side Hustle"](https://dev.to/challenges/hacktoberfest-week2-2026-10-12). It is free to use. Whether anyone would pay for it is not known yet.

**Status: work in progress.** The page works end to end. The evaluation described in [EVAL.md](EVAL.md) has not been run on the real photo set yet, so there are no accuracy numbers here.

## How it works

1. **Photo** (required), **Place** and **Note** (both optional). The Place is whatever you type.
2. **Place guess** (optional button). If you do not know where a photo was taken, Gemma can suggest a place. It is only a suggestion, clearly marked as a guess that may be wrong. It is never put in the Place field for you, and never used in the title, caption or hashtags until you press "use this".
3. **Make the post kit.** Gemma looks at the photo and writes the title, caption and hashtags. The Place on the kit is your own text, passed through unchanged. If you gave none, the kit says so instead of inventing one.
4. **Edit and copy.** Every field is editable, and a combined text box updates as you type.

Rules the kit must meet (checked in code, with a retry): at least 3 hashtags, each starting with `#` and without spaces; a single-line caption of at most 120 characters. Photos are rotated, shrunk to 1024 px and re-encoded without EXIF before the model sees them, so GPS data never reaches the model or the evaluation log. (Gradio keeps its own temporary copy of the uploaded original, so the file itself is not guaranteed to be gone from the machine.)

The page also has a small "help me check" form for testing. It appends one line per photo to `results/feedback.jsonl` (a short hash of the photo, your Note, the generated and the final text, which fields you edited, and your verdict). It does not store photos or coordinates, but it does store the text you typed, so treat the file as private. The `results/` folder is git-ignored.

## Run it

You need [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) and about 8 GB of free memory for the model (tested on an M1 Pro with 16 GB).

```bash
ollama pull gemma3:12b
uv run python app.py
```

Open http://localhost:7860. The program also prints a LAN address so a phone on the same Wi-Fi can use it. There is no login, so anyone on that network can reach the page while it runs.

A kit takes about 14 seconds on that machine, and a place guess about 8 to 16 seconds more.

## Tests

```bash
uv run pytest
```

Covers the hashtag and caption rules and the evaluation log. It does not call the model.

## Evaluation

The accuracy bar in [EVAL.md](EVAL.md) is checked by `eval.py`. Put the photos and a `manifest.csv` (see [manifest.example.csv](manifest.example.csv)) in `eval-set/`, which is git-ignored.

```bash
uv run python eval.py run --set eval-set/manifest.csv   # model pass: kits, automatic rules, place guesses
# the First user opens the page, checks each photo and presses a verdict button
uv run python eval.py report                            # scores the run against the bar
```

`run` also writes a `*-guess-review.csv`. Fill its `manual` column (`hit`, `wrong` or `unknown`) where the automatic label is off, for example when a guess is the right area under a different spelling. The report is `MET` only if every photo has a verdict, at least 70% are "post as is", and no Place was invented. Until every photo has a verdict it says `INCOMPLETE`.

## Model spike

`spike.py` runs the guess and the kit over six public photos from Wikimedia Commons, which are not included in this repository (add your own to `spike-photos/` and edit `CASES`). On those six photos the place guess was clearly right once, was wrong with a "high" confidence label three times, near the right place once, and declined once. The confidence label is not usable, which is why the page never shows it. Six photos is a spike, not an evaluation.

## Layout

```
app.py                Gradio page
tripkit/generate.py   Place guess and post kit with Gemma via Ollama
tripkit/validate.py   hashtag and caption rules
tripkit/post.py       text to paste, edit tracking, evaluation log
EVAL.md               the accuracy bar, written before any evaluation run
spike.py              model spike on a few photos
tests/                unit tests
```

## License

[MIT](LICENSE)
