import os
import json
import random
import urllib.request
import urllib.error
from datetime import datetime

DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "").strip()
MANUAL_TOPIC = os.environ.get("MANUAL_TOPIC", "").strip()
HISTORY_FILE = "used_topics.json"

TOPIC_POOL = [
    "AI Se Ghar Baithe Paise Kamane Ke 5 Asan Tareeqe",
    "ChatGPT Aur Free AI Tools Se Freelancing Kaise Shuru Karein",
    "AI Video Editing Tools Jo Aapka Kaam 10 Guna Tez Kar Dein",
    "Mobile Phone Par Free AI Apps Se Content Creation Kaise Karein",
    "Future of AI in Pakistan: Naye Rozgar Aur Online Earning",
    "AI Agents Kya Hain Aur Yeh Khud-ba-Khud Kaam Kaise Karte Hain",
    "YouTube Automation With Free AI Tools Complete Guide in Urdu",
    "AI Se Graphic Design Aur Thumbnail Banane Ke Best Free Tools",
    "Artificial Intelligence Se English Seekhne Aur Bolne Ka Asan Tareeqa",
    "Students Ke Liye 5 Behtareen Free AI Study Aur Research Tools",
    "AI Voice Over Aur Text to Speech Tools Ki Haqeeqat",
    "Small Business Ko AI Tools Se Grow Karne Ke Practical Tareeqe",
    "Google Gemini Aur ChatGPT Mein Kya Farq Hai Konsa Behtar Hai",
    "AI Se Resume Aur CV Banakar Online Job Hasil Karne Ka Tareeqa",
    "Cyber Security Aur AI: Apne Online Accounts Ko Safe Kaise Rakhein"
]

def load_used_topics():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_used_topic(topic):
    used = load_used_topics()
    if topic not in used:
        used.append(topic)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)

def pick_unique_topic():
    if MANUAL_TOPIC:
        return MANUAL_TOPIC
    used = load_used_topics()
    available = [t for t in TOPIC_POOL if t not in used]
    if not available:
        used = []
        available = TOPIC_POOL[:]
    chosen = random.choice(available)
    save_used_topic(chosen)
    return chosen

def get_dify_input_var():
    try:
        req = urllib.request.Request(
            "https://dify.ai",
            headers={"Authorization": f"Bearer {DIFY_API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("user_input_form", []):
                for field_type in ["text-input", "paragraph", "select"]:
                    if field_type in item:
                        return item[field_type].get("variable", "topic")
    except Exception as e:
        print(f"Parameter lookup fallback: {e}")
    return "topic"

def run_dify_workflow(topic):
    if not DIFY_API_KEY:
        return None
    var_name = get_dify_input_var()
    print(f"Calling Dify Workflow with variable '{var_name}' = '{topic}'")
    payload = {
        "inputs": {var_name: topic},
        "response_mode": "blocking",
        "user": "ai-with-aamir-cron"
    }
    req = urllib.request.Request(
        "https://dify.ai",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            outputs = result.get("data", {}).get("outputs", {})
            print("Dify outputs keys:", list(outputs.keys()))
            return outputs
    except Exception as e:
        print(f"Dify API error (activating Self-Healing fallback): {e}")
        return None

def set_github_output(name, value):
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            delimiter = "EOF_AAMIR_8899"
            f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")

def main():
    topic = pick_unique_topic()
    print(f"Selected Unique Topic: {topic}")
    outputs = run_dify_workflow(topic)

    video_title = f"AI With Aamir - {topic}"
    urdu_script = ""
    seo_text = f"Title: {video_title}\nDescription: {topic} ke baray mein mukammal maloomat AI With Aamir par.\nTags: AI With Aamir, AI in Urdu, Artificial Intelligence Pakistan, Online Earning"

    if outputs and isinstance(outputs, dict):
        all_texts = [str(v) for v in outputs.values() if v]
        for k, v in outputs.items():
            kl = k.lower()
            val = str(v).strip()
            if not val:
                continue
            if "script" in kl or "urdu" in kl or len(val) > 350:
                if len(val) > len(urdu_script):
                    urdu_script = val
            if "seo" in kl or "title" in kl or "tag" in kl:
                seo_text = val
        if not urdu_script and all_texts:
            urdu_script = max(all_texts, key=len)

    if len(urdu_script.strip()) < 80:
        print("Using Self-Healing Urdu Script Generator...")
        urdu_script = (
            f"Assalam-o-Alaikum dosto! AI With Aamir mein khush amdeed. "
            f"Aaj hum baat karenge {topic} ke baray mein. "
            f"Aaj ke jadeed daur mein Artificial Intelligence ne zindagi ke har shobay ko badal kar rakh diya hai. "
            f"Chahe aap student hon, freelancer hon ya apna karobar chala rahe hon, free AI tools ki madad se aap apna waqt bacha sakte hain aur apni aamdani mein izafa kar sakte hain. "
            f"Sab se pehle aapko chahiye ke rozana kam az kam ek naya AI tool seekhein aur usay apne rozmarra ke kaam mein istemal karein. "
            f"Is tarah aap bina kisi investment ke apni digital skills ko behtar bana sakte hain. "
            f"Agar aapko yeh maloomat pasand aayi hon to AI With Aamir ko subscribe zaroor karein. Shukriya!"
        )

    set_github_output("video_title", video_title)
    set_github_output("urdu_script", urdu_script)
    set_github_output("seo_text", seo_text)
    print("Agent 0 Autonomous Brain completed successfully!")

if __name__ == "__main__":
    main()
