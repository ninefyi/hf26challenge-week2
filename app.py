"""Trip photo + Place + Note -> title, place, one-sentence caption, hashtags. Gemma runs on this computer."""
import socket
from pathlib import Path

import gradio as gr

from tripkit.generate import guess_place, make_kit
from tripkit.post import append_log, feedback_record, post_text

LOG = Path("results/feedback.jsonl")
LANGS = {"ไทย": "th", "English": "en"}
VERDICTS = {"โพสต์ได้เลย": "as-is", "ต้องแก้ก่อนโพสต์": "edited", "ใช้ไม่ได้": "unusable"}
GUESS_NOTE = "⚠ AI เดาจากรูป อาจผิด ตรวจก่อนใช้ ไม่ได้ใส่ในช่องสถานที่ให้อัตโนมัติ"


def _bytes(photo: str) -> bytes:
    return Path(photo).read_bytes()


def on_guess(photo, lang):
    if not photo:
        raise gr.Error("เลือกรูปก่อน")
    guess = guess_place(_bytes(photo), LANGS[lang])
    if not guess.place or guess.place.lower() == "unknown":
        return "AI ไม่แน่ใจว่าที่นี่คือที่ไหน ไม่เดา ให้พิมพ์ชื่อสถานที่เอง", "", gr.update(visible=False)
    return f"**AI เดาว่า: {guess.place}**\n\n{GUESS_NOTE}", guess.place, gr.update(visible=True)


def on_use_guess(guess):
    return guess


def on_make(photo, place, note, lang):
    if not photo:
        raise gr.Error("เลือกรูปก่อน")
    res = make_kit(_bytes(photo), place or "", note or "", LANGS[lang])
    kit = res.kit
    tags = " ".join(kit["hashtags"])
    warnings = "\n".join(f"- ⚠ {w}" for w in res.warnings) or "ไม่มีคำเตือน"
    info = f"{warnings}\n\nใช้เวลา {res.seconds:.0f} วินาที"
    return (kit["title"], kit["place"], kit["caption"], tags,
            post_text(kit["title"], kit["place"], kit["caption"], tags), info, kit)


def on_edit(title, place, caption, tags):
    return post_text(title, place, caption, tags)


def on_save(photo, lang, verdict, title, place, caption, tags, note, generated, guess):
    if not photo or not generated:
        raise gr.Error("สร้างชุดโพสต์ก่อน")
    final = {"title": title, "place": place, "caption": caption, "hashtags": tags}
    append_log(feedback_record(_bytes(photo), LANGS[lang], VERDICTS[verdict], generated, final,
                               guess or "", note or "", Path(photo).name), LOG)
    return "บันทึกผลแล้ว ขอบคุณครับ"


with gr.Blocks(title="ชุดโพสต์จากรูปท่องเที่ยว") as demo:
    gr.Markdown("# ชุดโพสต์จากรูปท่องเที่ยว\n"
                "ใส่รูป แล้วได้ชื่อภาพ คำบรรยาย 1 ประโยค และแฮชแท็ก ไว้โพสต์ลงโซเชียลของคุณเอง  \n"
                "โมเดล (Gemma) ทำงานบนเครื่องนี้ รูปไม่ถูกส่งออกไปที่อื่น")
    photo = gr.Image(type="filepath", sources=["upload"], label="รูปท่องเที่ยว")
    lang = gr.Radio(list(LANGS), value="ไทย", label="ภาษา")
    place = gr.Textbox(label="ชื่อสถานที่ (ไม่ใส่ก็ได้)", placeholder="เช่น พระที่นั่งสันติไชยปราการ")
    guess_btn = gr.Button("ไม่แน่ใจว่าที่ไหน? ให้ AI เดา")
    guess_md = gr.Markdown()
    guess_state = gr.State("")
    use_guess_btn = gr.Button("ใช้ชื่อที่ AI เดา (แก้ได้)", visible=False)
    note = gr.Textbox(label="บันทึกสั้น ๆ (ไม่ใส่ก็ได้)", placeholder="เช่น หมอกลงตอนเช้า")
    make_btn = gr.Button("สร้างชุดโพสต์", variant="primary")

    gr.Markdown("### ผลลัพธ์ (แก้ได้ทุกช่อง)")
    title = gr.Textbox(label="ชื่อภาพ", interactive=True, buttons=["copy"])
    place_out = gr.Textbox(label="สถานที่", interactive=True, buttons=["copy"])
    caption = gr.Textbox(label="คำบรรยาย", interactive=True, buttons=["copy"])
    tags = gr.Textbox(label="แฮชแท็ก", interactive=True, buttons=["copy"])
    full = gr.Textbox(label="ข้อความพร้อมคัดลอก", lines=5, interactive=False, buttons=["copy"])
    info = gr.Markdown()
    generated = gr.State(None)

    gr.Markdown("### ช่วยตรวจ (สำหรับทดสอบ)")
    verdict = gr.Radio(list(VERDICTS), label="ผลลัพธ์นี้เป็นอย่างไร")
    save_btn = gr.Button("บันทึกผล")
    saved = gr.Markdown()

    guess_btn.click(on_guess, [photo, lang], [guess_md, guess_state, use_guess_btn])
    use_guess_btn.click(on_use_guess, guess_state, place)
    make_btn.click(on_make, [photo, place, note, lang], [title, place_out, caption, tags, full, info, generated])
    for box in (title, place_out, caption, tags):
        box.change(on_edit, [title, place_out, caption, tags], full, show_progress="hidden")
    save_btn.click(on_save, [photo, lang, verdict, title, place_out, caption, tags, note, generated, guess_state], saved)


def lan_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


if __name__ == "__main__":
    print(f"เปิดจากมือถือ (Wi-Fi เดียวกัน): http://{lan_ip()}:7860")
    demo.launch(server_name="0.0.0.0", server_port=7860)
