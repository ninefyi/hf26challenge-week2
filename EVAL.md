# Evaluation plan (written before any eval run)

Fixed on 2026-10-13. Amended the same day after the model spike (6 public photos, not an eval run): Place and Note are now separate fields, and the model may suggest a Place guess. The numeric thresholds did not change. Do not edit them after seeing eval results.

## Set
20 of the author's own Trip photos, each with a known place and a short Note:
- about 15 are recognisable places
- about 5 are unnamed or ordinary views (the Place field is left empty)

## Accuracy bar
- Post-as-is rate >= 70%: the First user accepts at least 14 of 20 Post kits without editing.
- Invented place names: 0. The Place on a Post kit is only text the Traveller typed or accepted from a Place guess. A guess never enters the title, caption or hashtags before it is confirmed.
- Hashtags: every Post kit has at least 3, each starting with `#`, no spaces.
- Caption: a single line, at most 120 characters.

## Also record (no threshold)
- Place guess hit rate: how often the guess equals the true place, how often it is wrong, and how often it says "unknown". A confidently wrong guess is the case to count.
- Seconds per photo on the 16 GB M1 Pro (spike: about 16 s for a kit with Gemma 3 12B).
- Gemma 3 12B alone vs Gemma 3 12B + a small Thai text model, on 10 photos (Oct 14).
- Every edit the First user makes, and what they ask for next.

## Reporting
Report the real numbers even if they miss the bar. Raw outputs are saved next to the results.

## Deviation (2026-10-14)
The plan was 20 photos judged by the First user. The author decided to evaluate on **one photo**, judged by the author, who is also the First user and the Traveller. With n = 1 the post-as-is rate can only be 0% or 100%, so the accuracy bar above (at least 14 of 20, 0 invented places) **is not tested** and no accuracy rate may be claimed. The one-photo run is reported as a single worked example. The earlier six-photo spike on public photos (Place guess clearly right once, wrong with a "high" label three times) is a separate, unscored spike. The numeric thresholds above are unchanged.
