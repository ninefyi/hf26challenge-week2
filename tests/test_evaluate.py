from tripkit.evaluate import (accuracy_bar, auto_checks, guess_outcome, guess_summary, latest_verdicts,
                              summarize_run)

KIT = {"title": "ยามเย็น", "place": "กรุงเทพ", "caption": "แสงสวย", "hashtags": ["#a", "#b", "#c"]}


def row(photo, photo_id, place="กรุงเทพ", ok=True, attempts=1, auto="hit"):
    checks = auto_checks({**KIT, "place": place if ok else "ที่แต่งขึ้น"}, place)
    return {"photo": photo, "photo_id": photo_id, "checks": checks, "attempts": attempts,
            "guess_seconds": 8.0, "kit_seconds": 14.0, "guess_auto": auto}


def test_auto_checks_pass_for_good_kit():
    assert all(auto_checks(KIT, "กรุงเทพ").values())


def test_auto_checks_flag_each_rule():
    assert not auto_checks({**KIT, "hashtags": ["#a", "#b"]}, "กรุงเทพ")["hashtags"]
    assert not auto_checks({**KIT, "hashtags": ["a", "#b", "#c"]}, "กรุงเทพ")["hashtags"]
    assert not auto_checks({**KIT, "caption": "ก\nข"}, "กรุงเทพ")["caption"]
    assert not auto_checks({**KIT, "caption": "ก" * 121}, "กรุงเทพ")["caption"]
    assert not auto_checks({**KIT, "title": " "}, "กรุงเทพ")["title"]


def test_invented_place_is_any_place_the_traveller_did_not_type():
    assert not auto_checks({**KIT, "place": "เชียงใหม่"}, "กรุงเทพ")["place_not_invented"]
    assert not auto_checks({**KIT, "place": "เชียงใหม่"}, "")["place_not_invented"]
    assert auto_checks({**KIT, "place": ""}, "")["place_not_invented"]


def test_guess_outcome():
    assert guess_outcome("พระนครศรีอยุธยา", "อยุธยา พระนคร ศรีอยุธยา") == "hit"
    assert guess_outcome("พระนครศรีอยุธยา", "พระนครศรีอยุธยา") == "hit"
    assert guess_outcome("อ่าวมะพร้าว", "เกาะตะปู") == "wrong"
    assert guess_outcome("unknown", "เกาะตะปู") == "unknown"
    assert guess_outcome("", "") == "unknown"
    assert guess_outcome("วัดอะไรสักแห่ง", "") == "wrong"


def test_guess_summary_manual_overrides_auto():
    rows = [row("a.jpg", "1", auto="wrong"), row("b.jpg", "2", auto="hit")]
    assert guess_summary(rows) == {"hit": 1, "wrong": 1, "unknown": 0}
    assert guess_summary(rows, {"a.jpg": "hit"}) == {"hit": 2, "wrong": 0, "unknown": 0}


def test_summarize_run_counts_and_times():
    rows = [row("a.jpg", "1"), row("b.jpg", "2", ok=False, attempts=2)]
    s = summarize_run(rows)
    assert s["photos"] == 2 and s["invented_places"] == 1 and s["retried"] == 1
    assert s["all_rules_pass"] == 1 and s["seconds_mean"] == 22.0


def test_latest_verdicts_last_row_wins():
    fb = [{"photo_id": "1", "verdict": "edited"}, {"photo_id": "1", "verdict": "as-is"}]
    assert latest_verdicts(fb)["1"]["verdict"] == "as-is"


def fb(photo_id, verdict):
    return {"photo_id": photo_id, "verdict": verdict}


def test_accuracy_bar_met_needs_14_of_20_and_no_invented_places():
    rows = [row(f"{i}.jpg", str(i)) for i in range(20)]
    feedback = [fb(str(i), "as-is" if i < 14 else "edited") for i in range(20)]
    result = accuracy_bar(rows, feedback)
    assert result["status"] == "MET" and result["needed_as_is"] == 14


def test_accuracy_bar_not_met_at_13_of_20():
    rows = [row(f"{i}.jpg", str(i)) for i in range(20)]
    feedback = [fb(str(i), "as-is" if i < 13 else "edited") for i in range(20)]
    assert accuracy_bar(rows, feedback)["status"] == "NOT MET"


def test_accuracy_bar_fails_on_one_invented_place_even_at_100_percent():
    rows = [row(f"{i}.jpg", str(i), ok=(i != 0)) for i in range(20)]
    feedback = [fb(str(i), "as-is") for i in range(20)]
    assert accuracy_bar(rows, feedback)["status"] == "NOT MET"


def test_accuracy_bar_incomplete_lists_photos_without_a_verdict():
    rows = [row(f"{i}.jpg", str(i)) for i in range(20)]
    result = accuracy_bar(rows, [fb(str(i), "as-is") for i in range(19)])
    assert result["status"] == "INCOMPLETE" and result["missing_verdict"] == ["19.jpg"]


def test_accuracy_bar_is_not_tested_below_20_photos_even_at_100_percent():
    rows = [row("a.jpg", "1")]
    result = accuracy_bar(rows, [fb("1", "as-is")])
    assert result["status"].startswith("NOT TESTED") and result["as_is_rate"] == 1.0


def test_accuracy_bar_falls_back_to_file_name_when_hash_differs():
    rows = [row("a.jpg", "hash-from-eval")]
    feedback = [{"photo_id": "other-hash", "photo_name": "a.jpg", "verdict": "as-is"}]
    assert accuracy_bar(rows, feedback)["verdicts"]["as-is"] == 1
