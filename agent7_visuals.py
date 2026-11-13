import json
import os
import time
import urllib.parse
import urllib.request

OUTPUT_DIR = "output/visuals"
VOICE_MANIFEST = "output/audio/voice_manifest.json"
STYLE_SUFFIX = ", cinematic lighting, ultra detailed, digital art, clean composition, 8k resolution, no text, no watermark"
POLLINATIONS_BASE = "https://pollinations.ai" + "/prompt/"

def build_prompt_from_urdu(urdu_text, segment_id):
    base = f"Scene {segment_id}: futuristic artificial intelligence technology, glowing blue and gold digital network, modern educational YouTube visual"
    return urllib.parse.quote(base + STYLE_SUFFIX)

def download_ai_image(prompt_encoded, out_path, width=1280, height=720, seed=42):
    url = f"{POLLINATIONS_BASE}{prompt_encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        with open(out_path, "wb") as f:
            f.write(data)
    return out_path

def search_pexels_video(query, api_key, out_path, orientation="landscape"):
    encoded_q = urllib.parse.quote(query)
    api_url = f"https://pexels.com{encoded_q}&orientation={orientation}&per_page=1"
    req = urllib.request.Request(api_url, headers={"Authorization": api_key, "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        videos = result.get("videos", [])
        if not videos:
            return None
        files = videos.get("video_files", [])
        hd_files = [f for f in files if f.get("width", 0) >= 1280] or files
        if not hd_files:
            return None
        video_url = hd_files["link"]
        vreq = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(vreq, timeout=60) as vresp:
            with open(out_path, "wb") as f:
                f.write(vresp.read())
        return out_path

def run_agent7(video_format="landscape"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if video_format == "shorts":
        width, height, orientation = 720, 1280, "portrait"
    else:
        width, height, orientation = 1280, 720, "landscape"

    if os.path.exists(VOICE_MANIFEST):
        with open(VOICE_MANIFEST, "r", encoding="utf-8") as f:
            segments = json.load(f)
    else:
        segments = [{"segment_id": 1, "urdu_text": "AI With Aamir test scene"}]

    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    visual_manifest = []

    for seg in segments:
        sid = seg["segment_id"]
        urdu_text = seg.get("urdu_text", "")
        asset_path = None
        asset_type = "image"

        if pexels_key and sid % 2 == 0:
            try:
                vid_file = os.path.join(OUTPUT_DIR, f"scene_{sid:03d}.mp4")
                asset_path = search_pexels_video("artificial intelligence technology", pexels_key, vid_file, orientation)
                if asset_path:
                    asset_type = "video"
            except Exception as e:
                print(f"[Agent 7] Pexels fallback to AI image for scene {sid}: {e}")

        if not asset_path:
            img_file = os.path.join(OUTPUT_DIR, f"scene_{sid:03d}.jpg")
            prompt_enc = build_prompt_from_urdu(urdu_text, sid)
            asset_path = download_ai_image(prompt_enc, img_file, width=width, height=height, seed=100 + sid)
            asset_type = "image"
            time.sleep(1)

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
