import json

from tripkit.post import append_log, edited_fields, feedback_record, parse_hashtags, post_text

GEN = {"title": "ยามเย็น", "place": "กรุงเทพ", "caption": "แสงสวย", "hashtags": ["#a", "#b", "#c"]}


def test_parse_hashtags_accepts_spaces_and_commas():
    assert parse_hashtags("#a, b  #c,#a") == ["#a", "#b", "#c"]


def test_post_text_skips_empty_place():
    assert post_text("T", "", "C", "#a #b") == "T\nC\n#a #b"
    assert post_text("T", "กรุงเทพ", "C", "a b") == "T\n📍 กรุงเทพ\nC\n#a #b"


def test_edited_fields_ignores_whitespace_and_hash_formatting():
    final = {"title": " ยามเย็น ", "place": "กรุงเทพ", "caption": "แสงสวย", "hashtags": "a b, c"}
    assert edited_fields(GEN, final) == []


def test_edited_fields_reports_changes():
    final = {"title": "ยามเย็น", "place": "นนทบุรี", "caption": "แสงสวยมาก", "hashtags": "#a #b"}
    assert edited_fields(GEN, final) == ["place", "caption", "hashtags"]


def test_feedback_record_place_source():
    final = {**GEN, "hashtags": "#a #b #c"}
    assert feedback_record(b"x", "th", "as-is", GEN, final, "กรุงเทพ", "")["place_source"] == "guess"
    assert feedback_record(b"x", "th", "as-is", GEN, final, "เชียงใหม่", "")["place_source"] == "typed"
    assert feedback_record(b"x", "th", "as-is", GEN, {**final, "place": ""}, "", "")["place_source"] == "none"


def test_feedback_record_has_no_image_data():
    rec = feedback_record(b"secret-bytes", "th", "edited", GEN, GEN, "", "บันทึก")
    assert "secret" not in json.dumps(rec) and len(rec["photo_id"]) == 10


def test_append_log_writes_one_json_line(tmp_path):
    path = tmp_path / "logs" / "f.jsonl"
    append_log({"a": "ก"}, path)
    append_log({"a": "ข"}, path)
    assert [json.loads(line)["a"] for line in path.read_text(encoding="utf-8").splitlines()] == ["ก", "ข"]
