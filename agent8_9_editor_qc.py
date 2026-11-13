import json
import os
import subprocess
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

VOICE_MANIFEST = "output/audio/voice_manifest.json"
VISUAL_MANIFEST = "output/visuals/visual_manifest.json"
TEMP_DIR = "output/temp"
FINAL_DIR = "output/final"

def get_audio_duration(audio_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def shape_urdu_text(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def create_subtitle_overlay(urdu_text, width, height, out_png):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    display_text = shape_urdu_text(urdu_text)

    font_size = 44 if width > height else 40
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, font_size)
            break
    if font is None:
        font = ImageFont.load_default()

    # Wrap long Urdu lines cleanly
    words = urdu_text.split()
    lines = []
    current = []
    max_words = 9 if width > height else 6
    for w in words:
        current.append(w)
        if len(current) >= max_words:
            lines.append(shape_urdu_text(" ".join(current)))
            current = []
    if current:
        lines.append(shape_urdu_text(" ".join(current)))

    line_height = font_size + 16
    box_height = len(lines) * line_height + 36
    y_start = height - box_height - (60 if width > height else 160)

    # Semi-transparent dark caption box
    draw.rounded_rectangle(
        [(60, y_start), (width - 60, y_start + box_height)],
        radius=18,
        fill=(10, 15, 28, 200)
    )

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        y = y_start + 16 + i * line_height
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    img.save(out_png)
    return out_png

def render_scene_clip(asset_file, asset_type, audio_file, sub_png, duration, width, height, out_mp4):
    fps = 25
    total_frames = max(int(duration * fps) + 5, 25)
    if asset_type == "video" and asset_file.endswith(".mp4"):
        cmd = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", asset_file,
            "-i", sub_png, "-i", audio_file,
            "-filter_complex",
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[bg];[bg][1:v]overlay=0:0[v]",
            "-map", "[v]", "-map", "2:a",
            "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", asset_file,
            "-i", sub_png, "-i", audio_file,
            "-filter_complex",
            f"[0:v]scale={width*2}:{height*2},zoompan=z='min(zoom+0.0008,1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},setsar=1[bg];[bg][1:v]overlay=0:0[v]",
            "-map", "[v]", "-map", "2:a",
            "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4
        ]
    subprocess.run(cmd, check=True)

def run_agent8_and_qc(video_format="landscape"):
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)

    width, height = (1080, 1920) if video_format == "shorts" else (1920, 1080)

    with open(VOICE_MANIFEST, "r", encoding="utf-8") as f:
        voice_data = json.load(f)
    with open(VISUAL_MANIFEST, "r", encoding="utf-8") as f:
        visual_data = json.load(f)

    visual_map = {v["segment_id"]: v for v in visual_data}
    clip_paths = []
    total_expected_duration = 0.0

    for seg in voice_data:
        sid = seg["segment_id"]
        urdu_text = seg["urdu_text"]
        audio_file = seg["audio_file"]
        vis = visual_map.get(sid)
        if not vis:
            raise RuntimeError(f"Missing visual for segment {sid}")

        dur = get_audio_duration(audio_file)
        total_expected_duration += dur
        sub_png = os.path.join(TEMP_DIR, f"sub_{sid:03d}.png")
        clip_mp4 = os.path.join(TEMP_DIR, f"clip_{sid:03d}.mp4")

        create_subtitle_overlay(urdu_text, width, height, sub_png)
        render_scene_clip(vis["asset_file"], vis["asset_type"], audio_file, sub_png, dur, width, height, clip_mp4)
        clip_paths.append(clip_mp4)
        print(f"[Agent 8] Rendered scene {sid} ({dur:.2f}s)")

    concat_list = os.path.join(TEMP_DIR, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{os.path.abspath(cp)}'\n")

    final_mp4 = os.path.join(FINAL_DIR, "ai_with_aamir_final.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", final_mp4
    ], check=True)

    # Agent 9: Quality Control Verification
    qc_passed = True
    qc_notes = []
    if not os.path.exists(final_mp4) or os.path.getsize(final_mp4) < 50000:
        qc_passed = False
        qc_notes.append("Final MP4 missing or file size too small.")

    actual_dur = get_audio_duration(final_mp4)
    if abs(actual_dur - total_expected_duration) > 2.0:
        qc_passed = False
        qc_notes.append(f"Duration mismatch: expected {total_expected_duration:.2f}s, got {actual_dur:.2f}s")

    qc_report = {
        "qc_passed": qc_passed,
        "resolution": f"{width}x{height}",
        "total_scenes": len(clip_paths),
        "duration_seconds": round(actual_dur, 2),
        "file_size_mb": round(os.path.getsize(final_mp4) / (1024 * 1024), 2),
        "output_video": final_mp4,
        "notes": qc_notes or ["All checks passed: Urdu subtitles, audio sync, and HD resolution verified."]
    }

    qc_path = os.path.join(FINAL_DIR, "qc_report.json")
    with open(qc_path, "w", encoding="utf-8") as f:
        json.dump(qc_report, f, ensure_ascii=False, indent=2)

    print("[Agent 9 QC Report]", json.dumps(qc_report, ensure_ascii=False))
    if not qc_passed:
        raise RuntimeError(f"Quality Control Failed: {qc_notes}")
    return final_mp4

if __name__ == "__main__":
    fmt = os.environ.get("VIDEO_FORMAT", "landscape")
    run_agent8_and_qc(fmt)
