import json
import os
import glob
import urllib.parse
import urllib.request

PACKAGE_OUT = "output/final/youtube_package.json"

def find_final_video():
    for candidate in [
        "output/final/ai_with_aamir_daily.mp4",
        "output/final/ai_with_aamir_final.mp4"
    ]:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 50000:
            return candidate
    mp4s = glob.glob("output/final/*.mp4")
    if mp4s:
        return max(mp4s, key=os.path.getmtime)
    return None

def get_youtube_access_token(client_id, client_secret, refresh_token):
    token_url = "https://" + "://googleapis.com" + "/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    if not client_secret:
        payload.pop("client_secret", None)

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(token_url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("access_token")

def upload_to_youtube(access_token, video_path, title, description, tags, privacy="public"):
    init_url = (
        "https://" + "://googleapis.com"
        + "/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    )
    metadata = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "ur"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(os.path.getsize(video_path))
    }
    req = urllib.request.Request(
        init_url,
        data=json.dumps(metadata).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        upload_url = resp.headers.get("Location")

    with open(video_path, "rb") as vf:
        video_bytes = vf.read()

    up_req = urllib.request.Request(
        upload_url,
        data=video_bytes,
        headers={"Content-Type": "video/mp4"},
        method="PUT"
    )
    with urllib.request.urlopen(up_req, timeout=240) as up_resp:
        return json.loads(up_resp.read().decode("utf-8"))

def run_agent10():
    video_path = find_final_video()
    if not video_path:
        raise RuntimeError("Agent 10 stopped: No final MP4 video found!")

    title = os.environ.get("VIDEO_TITLE", "AI With Aamir - Complete Urdu AI Tutorial").strip()
    seo_raw = os.environ.get("SEO_TEXT", "").strip()
    description = (
        seo_raw if seo_raw else
        f"{title}\n\nProduced by AI With Aamir Autonomous Studio.\n#AIWithAamir #UrduAI #ArtificialIntelligence #OnlineEarningPakistan"
    )
    tags = ["AI With Aamir", "Urdu AI", "Artificial Intelligence Urdu", "AI Tutorial Pakistan", "Online Earning"]

    os.makedirs("output/final", exist_ok=True)
    package = {
        "title": title[:95],
        "description": description,
        "tags": tags,
        "video_file": video_path
    }
    with open(PACKAGE_OUT, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)

    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()

    if not refresh_token or not client_id:
        print("[Agent 10] YouTube secrets not set yet; saved package locally.")
        return

    print(f"[Agent 10] Uploading {video_path} to YouTube channel AI With Aamir...")
    access_token = get_youtube_access_token(client_id, client_secret, refresh_token)
    if not access_token:
        raise RuntimeError("Agent 10 failed to obtain YouTube access token!")

    result = upload_to_youtube(access_token, video_path, title, description, tags, privacy="public")
    video_id = result.get("id", "unknown")
    print(f"[Agent 10 SUCCESS] Video published to YouTube! Video ID: {video_id}")

if __name__ == "__main__":
    run_agent10()
