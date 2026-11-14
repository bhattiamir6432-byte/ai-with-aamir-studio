import os
import re
import glob
import json
import urllib.parse
import urllib.request
import subprocess
from PIL import Image, ImageDraw, ImageFont

VIDEO_FORMAT = os.environ.get("VIDEO_FORMAT", "landscape").strip().lower()
URDU_SCRIPT = os.environ.get("URDU_SCRIPT", "").strip()
OUTPUT_DIR = "output/final"

def split_urdu_sentences(text):
    clean = " ".join(text.split())
    if not clean:
        return ["Welcome to AI With Aamir!"]
    parts = re.split(r'[۔!?؟\.\n]+', clean)
    sentences = [p.strip() for p in parts if len(p.strip()) > 3]
    return sentences if sentences else [clean]

def translate_sentence_to_english(urdu_sentence):
    try:
        encoded = urllib.parse.quote(urdu_sentence[:300], safe="")
        url = f"https://googleapis.com{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = "".join([part[0] for part in data[0] if part and part[0]])
            if translated.strip():
                return translated.strip()
    except Exception as e:
        print(f"[Agent 8] Subtitle translation fallback: {e}")
    return "Learn Artificial Intelligence & Online Earning with AI With Aamir."

def wrap_text(text, max_chars=54):
    words = text.split()
    lines = []
    current = []
    for w in words:
        if sum(len(x) + 1 for x in current) + len(w) <= max_chars:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines[:3])

def create_subtitle_png(english_text, width, height, out_png):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = 38 if width >= height else 42
    font = None
    for fpath in [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(fpath):
            font = ImageFont.truetype(fpath, font_size)
            break
    if font is None:
        font = ImageFont.load_default()

    wrapped = wrap_text(english_text, max_chars=54 if width >= height else 32)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x, pad_y = 34, 20
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2
    x0 = (width - box_w) // 2
    y0 = height - box_h - int(height * 0.07)
    x1 = x0 + box_w
    y1 = y0 + box_h

    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(10, 15, 30, 220), outline=(56, 189, 248, 255), width=3)
    draw.multiline_text((x0 + pad_x, y0 + pad_y), wrapped, font=font, fill=(255, 255, 255, 255), align="center")
    img.save(out_png, "PNG")

def find_audio_file():
    candidates = glob.glob("output/**/*.mp3", recursive=True) + glob.glob("output/**/*.wav", recursive=True)
    candidates = [c for c in candidates if os.path.getsize(c) > 1000]
    if candidates:
        candidates.sort()
        return candidates[0]
    return None

def find_visual_files():
    imgs = (
        glob.glob("output/**/*.png", recursive=True)
        + glob.glob("output/**/*.jpg", recursive=True)
        + glob.glob("output/**/*.jpeg", recursive=True)
    )
    imgs = [i for i in imgs if "sub_" not in os.path.basename(i) and "final" not in i and os.path.getsize(i) > 1000]
    imgs.sort()
    return imgs

def get_audio_duration(audio_path):
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        res = subprocess.check_output(cmd).decode("utf-8").strip()
        return max(float(res), 5.0)
    except Exception:
        return 25.0

def run_agent8_and_qc():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    width, height = (1080, 1920) if VIDEO_FORMAT == "shorts" else (1920, 1080)

    audio_path = find_audio_file()
    if not audio_path:
        raise RuntimeError("No valid audio file found from Agent 6!")

    duration = get_audio_duration(audio_path)
    print(f"[Agent 8] Audio found: {audio_path} ({duration:.1f}s)")

    urdu_sentences = split_urdu_sentences(URDU_SCRIPT)
    english_subs = [translate_sentence_to_english(s) for s in urdu_sentences]
    print(f"[Agent 8] Generated {len(english_subs)} synced English subtitle segments.")

    total_chars = sum(max(len(s), 1) for s in urdu_sentences)
    sub_items = []
    cur_t = 0.0
    for idx, (u_s, e_s) in enumerate(zip(urdu_sentences, english_subs)):
        seg_dur = duration * (max(len(u_s), 1) / total_chars)
        end_t = duration if idx == len(urdu_sentences) - 1 else cur_t + seg_dur
        png_path = os.path.join("output", f"sub_{idx}.png")
        create_subtitle_png(e_s, width, height, png_path)
        sub_items.append((png_path, cur_t, end_t))
        cur_t = end_t

    visuals = find_visual_files()
    if not visuals:
        fallback_bg = os.path.join("output", "fallback_bg.png")
        bg = Image.new("RGB", (width, height), (15, 23, 42))
        bg.save(fallback_bg)
        visuals = [fallback_bg]

    concat_txt = os.path.join("output", "slides_concat.txt")
    per_slide = max(duration / len(visuals), 2.0)
    with open(concat_txt, "w", encoding="utf-8") as f:
        for img_path in visuals:
            abs_p = os.path.abspath(img_path).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")
            f.write(f"duration {per_slide:.2f}\n")
        last_p = os.path.abspath(visuals[-1]).replace("\\", "/")
        f.write(f"file '{last_p}'\n")

    final_mp4 = os.path.join(OUTPUT_DIR, "ai_with_aamir_daily.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", audio_path
    ]
    for png_path, _, _ in sub_items:
        cmd.extend(["-i", png_path])

    filter_parts = [
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x0f172a,setsar=1[v0]"
    ]
    last_label = "v0"
    for idx, (_, st, et) in enumerate(sub_items):
        in_idx = idx + 2
        next_label = f"v{idx + 1}"
        filter_parts.append(
            f"[{last_label}][{in_idx}:v]overlay=0:0:enable='between(t,{st:.2f},{et:.2f})'[{next_label}]"
        )
        last_label = next_label

    cmd.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{last_label}]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", final_mp4
    ])
    subprocess.run(cmd, check=True)

    if not os.path.exists(final_mp4) or os.path.getsize(final_mp4) < 50000:
        raise RuntimeError("[Agent 9 QC] Final MP4 verification failed!")

    size_mb = os.path.getsize(final_mp4) / (1024 * 1024)
    print(f"[Agent 9 QC PASSED] Created {final_mp4} ({size_mb:.2f} MB) with synced English subtitles!")

if __name__ == "__main__":
    run_agent8_and_qc()
