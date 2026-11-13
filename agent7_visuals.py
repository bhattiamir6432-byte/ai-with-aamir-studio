import json
import os
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "output/visuals"
VOICE_MANIFEST = "output/audio/voice_manifest.json"

SEARCH_TOPICS = [
    "Artificial intelligence",
    "Robotics technology",
    "Computer network",
    "Data center",
    "Machine learning",
    "Digital technology"
]

def download_wikimedia_image(query, out_path):
    encoded = urllib.parse.quote(query)
    api_url = (
        f"https://wikimedia.org"
        f"&gsrsearch=filetype:bitmap+{encoded}&gsrnamespace=6&gsrlimit=5"
        f"&prop=imageinfo&iiprop=url&iiurlwidth=1280&format=json"
    )
    req = urllib.request.Request(api_url, headers={"User-Agent": "AIWithAamirBot/1.0 (educational)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            info = page.get("imageinfo", [])
            if info:
                img_url = info[0].get("thumburl") or info[0].get("url")
                if img_url and (img_url.lower().endswith(".jpg") or img_url.lower().endswith(".jpeg") or img_url.lower().endswith(".png")):
                    ireq = urllib.request.Request(img_url, headers={"User-Agent": "AIWithAamirBot/1.0"})
                    with urllib.request.urlopen(ireq, timeout=45) as iresp:
                        with open(out_path, "wb") as f:
                            f.write(iresp.read())
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 15000:
                        return out_path
    return None

def search_pexels_video(query, api_key, out_path, orientation="landscape"):
    encoded_q = urllib.parse.quote(query)
    api_url = f"https://pexels.com{encoded_q}&orientation={orientation}&per_page=1"
    req = urllib.request.Request(api_url, headers={"Authorization": api_key, "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        videos = result.get("videos", [])
        if not videos:
            return None
        files = videos[0].get("video_files", [])
        hd_files = [f for f in files if f.get("width", 0) >= 1280] or files
        if not hd_files:
            return None
        video_url = hd_files[0]["link"]
        vreq = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(vreq, timeout=60) as vresp:
            with open(out_path, "wb") as f:
                f.write(vresp.read())
        return out_path

def create_branded_slide(scene_num, width, height, out_path):
    img = Image.new("RGB", (width, height), (12, 20, 38))
    draw = ImageDraw.Draw(img)
    # Gradient-style geometric accents
    for step in range(0, height, 8):
        shade = min(45, 12 + int((step / height) * 30))
        draw.line([(0, step), (width, step)], fill=(shade, shade + 12, shade + 35), width=8)
    draw.rectangle([(40, 40), (width - 40, height - 40)], outline=(218, 165, 32), width=4)
    draw.ellipse([(width // 2 - 220, height // 2 - 220), (width // 2 + 220, height // 2 + 220)], outline=(56, 189, 248), width=3)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    title_font = ImageFont.truetype(font_path, 58) if os.path.exists(font_path) else ImageFont.load_default()
    sub_font = ImageFont.truetype(font_path, 32) if os.path.exists(font_path) else ImageFont.load_default()

    brand = "AI WITH AAMIR"
    bbox = draw.textbbox((0, 0), brand, font=title_font)
    bw = bbox[2] - bbox[0]
    draw.text(((width - bw) // 2, height // 2 - 50), brand, font=title_font, fill=(255, 215, 0))

    label = f"SCENE {scene_num:02d}"
    sbbox = draw.textbbox((0, 0), label, font=sub_font)
    sw = sbbox[2] - sbbox[0]
    draw.text(((width - sw) // 2, height // 2 + 30), label, font=sub_font, fill=(147, 197, 253))

    img.save(out_path, "JPEG", quality=92)
    return out_path

def run_agent7(video_format="landscape"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if video_format == "shorts":
        width, height, orientation = 1080, 1920, "portrait"
    else:
        width, height, orientation = 1920, 1080, "landscape"

    if os.path.exists(VOICE_MANIFEST):
        with open(VOICE_MANIFEST, "r", encoding="utf-8") as f:
            segments = json.load(f)
    else:
        segments = [{"segment_id": 1, "urdu_text": "AI With Aamir test scene"}]

    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    visual_manifest = []

    for seg in segments:
        sid = seg["segment_id"]
        topic = SEARCH_TOPICS[(sid - 1) % len(SEARCH_TOPICS)]
        asset_path = None
        asset_type = "image"

        if pexels_key and sid % 2 == 0:
            try:
                vid_file = os.path.join(OUTPUT_DIR, f"scene_{sid:03d}.mp4")
                asset_path = search_pexels_video(topic, pexels_key, vid_file, orientation)
                if asset_path:
                    asset_type = "video"
            except Exception as e:
                print(f"[Agent 7] Pexels skipped for scene {sid}: {e}")

        if not asset_path:
            img_file = os.path.join(OUTPUT_DIR, f"scene_{sid:03d}.jpg")
            try:
                asset_path = download_wikimedia_image(topic, img_file)
            except Exception as e:
                print(f"[Agent 7] Wikimedia fallback for scene {sid}: {e}")

        if not asset_path:
            img_file = os.path.join(OUTPUT_DIR, f"scene_{sid:03d}.jpg")
            asset_path = create_branded_slide(sid, width, height, img_file)

        visual_manifest.append({
            "segment_id": sid,
            "asset_type": asset_type,
            "asset_file": asset_path
        })
        print(f"[Agent 7] Scene {sid} ready ({asset_type}) -> {asset_path}")

    manifest_path = os.path.join(OUTPUT_DIR, "visual_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(visual_manifest, f, ensure_ascii=False, indent=2)
    print(f"[Agent 7] Completed {len(visual_manifest)} visuals.")
    return manifest_path

if __name__ == "__main__":
    fmt = os.environ.get("VIDEO_FORMAT", "landscape")
    run_agent7(fmt)
