import json
import os
import urllib.parse
import urllib.request

FINAL_VIDEO = "output/final/ai_with_aamir_final.mp4"
QC_REPORT = "output/final/qc_report.json"
PACKAGE_OUT = "output/final/youtube_package.json"

def get_youtube_access_token(client_id, client_secret, refresh_token):
    token_url = "https://googleapis.com"
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    req = urllib.request.Request(token_url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("access_token")

def upload_private_to_youtube(access_token, video_path, title, description, tags):
    init_url = "https://googleapis.com"
    metadata = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "ur"
        },
        "status": {
            "privacyStatus": "private",
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
    with urllib.request.urlopen(up_req, timeout=180) as up_resp:
        return json.loads(up_resp.read().decode("utf-8"))

def run_agent10():
    if os.path.exists(QC_REPORT):
        with open(QC_REPORT, "r", encoding="utf-8") as f:
            qc = json.load(f)
        if not qc.get("qc_passed", False):
            raise RuntimeError("Agent 10 stopped: Agent 9 QC did not pass.")

    title = os.environ.get("VIDEO_TITLE", "AI With Aamir - Complete Urdu AI Tutorial").strip()
    seo_raw = os.environ.get("SEO_TEXT", "").strip()
    description = seo_raw if seo_raw else f"{title}\n\nProduced by AI With Aamir Automation Studio.\n#AIWithAamir #UrduAI #ArtificialIntelligence"
    tags = ["AI With Aamir", "Urdu AI", "Artificial Intelligence Urdu", "AI Tutorial Pakistan"]

    package = {
        "title": title[:95],
        "description": description,
        "tags": tags,
        "privacy_status": "private (Approval Required)",
        "video_file": FINAL_VIDEO,
        "youtube_video_id": None,
        "status": "Prepared for Manual Review"
    }

    cid = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    csec = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    rtok = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()

    if cid and csec and rtok and os.path.exists(FINAL_VIDEO):
        try:
            token = get_youtube_access_token(cid, csec, rtok)
            yt_res = upload_private_to_youtube(token, FINAL_VIDEO, package["title"], description, tags)
            package["youtube_video_id"] = yt_res.get("id")
            package["status"] = "Uploaded as PRIVATE to YouTube (Waiting for Aamir Approval)"
            print(f"[Agent 10] Uploaded Privately! Video ID: {package['youtube_video_id']}")
        except Exception as e:
            package["status"] = f"YouTube API Upload Skipped/Error: {e}"
            print(f"[Agent 10] {package['status']}")
    else:
        print("[Agent 10] YouTube API keys not set yet. Video & SEO package ready for download.")

    with open(PACKAGE_OUT, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    return PACKAGE_OUT

if __name__ == "__main__":
    run_agent10()
