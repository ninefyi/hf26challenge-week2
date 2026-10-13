from tripkit.validate import clean_hashtag, clean_hashtags, one_line, problems

GOOD = {
    "title": "แสงเย็นที่พระที่นั่ง",
    "caption": "แสงสุดท้ายของวันทำให้ริมแม่น้ำเงียบและอบอุ่น",
    "hashtags": ["#กรุงเทพ", "#เที่ยวไทย", "#sunset"],
}


def test_good_kit_has_no_problems():
    assert problems(GOOD) == []


def test_fewer_than_three_hashtags_fails():
    assert "fewer than 3 hashtags" in problems({**GOOD, "hashtags": ["#a", "#b"]})


def test_duplicate_hashtags_count_once():
    assert "fewer than 3 hashtags" in problems({**GOOD, "hashtags": ["#a", "#A", "#b"]})


def test_multiline_caption_fails():
    assert "caption is not a single line" in problems({**GOOD, "caption": "บรรทัดหนึ่ง\nบรรทัดสอง"})


def test_long_caption_fails():
    assert any("longer than" in p for p in problems({**GOOD, "caption": "ก" * 121}))


def test_empty_title_and_caption_fail():
    found = problems({**GOOD, "title": " ", "caption": ""})
    assert "empty title" in found and "empty caption" in found


def test_clean_hashtag_adds_hash_and_removes_spaces():
    assert clean_hashtag("เที่ยว ไทย") == "#เที่ยวไทย"
    assert clean_hashtag("##sea") == "#sea"
    assert clean_hashtag("  ") == ""


def test_clean_hashtags_drops_empty_and_duplicates():
    assert clean_hashtags(["#a", "A", "", "#b"]) == ["#a", "#b"]


def test_one_line_collapses_whitespace():
    assert one_line("a\n b   c") == "a b c"
