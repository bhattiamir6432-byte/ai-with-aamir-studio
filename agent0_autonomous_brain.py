import os
import re
import json
import random
import urllib.request
from datetime import datetime

DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "").strip()
MANUAL_TOPIC = os.environ.get("MANUAL_TOPIC", "").strip()
HISTORY_FILE = "used_topics.json"

TOPIC_ITEMS = [
    {
        "title": "AI Se Ghar Baithe Paise Kamane Ke 5 Asan Tareeqe",
        "urdu": "السلام علیکم دوستو! اے آئی ود عامر میں خوش آمدید۔ آج ہم بات کریں گے کہ آپ مصنوعی ذہانت یعنی اے آئی کی مدد سے گھر بیٹھے پیسے کیسے کما سکتے ہیں۔ سب سے پہلا طریقہ فری لانسنگ ہے جس میں آپ اے آئی ٹولز سے مضامین اور سکرپٹ لکھ کر کما سکتے ہیں۔ دوسرا طریقہ یوٹیوب آٹومیشن ہے جس میں آپ اے آئی وائس اور ویڈیوز بنا کر اپنا چینل چلا سکتے ہیں۔ تیسرا طریقہ گرافک ڈیزائننگ اور تھمب نیل بنانا ہے۔ اگر آپ روزانہ ایک نیا اے آئی ٹول سیکھیں تو بغیر کسی سرمایہ کاری کے بہترین آن لائن آمدنی حاصل کر سکتے ہیں۔ مزید معلومات کے لیے اے آئی ود عامر کو سبسکرائب ضرور کریں۔ شکریہ!"
    },
    {
        "title": "ChatGPT Aur Free AI Tools Se Freelancing Kaise Shuru Karein",
        "urdu": "السلام علیکم دوستو! اے آئی ود عامر میں خوش آمدید۔ آج کی ویڈیو میں ہم سیکھیں گے کہ چیٹ جی پی ٹی اور مفت اے آئی ٹولز استعمال کر کے فری لانسنگ کیسے شروع کی جائے۔ اگر آپ کے پاس کوئی پرانا تجربہ نہیں ہے تب بھی آپ اے آئی کی مدد سے ترجمہ، مواد کی تیاری اور سوشل میڈیا پوسٹس بنا کر کلائنٹس کو خدمات دے سکتے ہیں۔ بس آپ کو صحیح پرامپٹ لکھنا سیکھنا ہوگا تاکہ بہترین نتیجہ حاصل ہو سکے۔ محنت اور مستقل مزاجی سے آپ گھر بیٹھے کامیاب فری لانسر بن سکتے ہیں۔ ویڈیو پسند آئے تو چینل کو سبسکرائب کریں۔ شکریہ!"
    },
    {
        "title": "AI Agents Kya Hain Aur Yeh Khud-ba-Khud Kaam Kaise Karte Hain",
        "urdu": "السلام علیکم دوستو! اے آئی ود عامر میں خوش آمدید۔ کیا آپ جانتے ہیں کہ اے آئی ایجنٹس کیا ہوتے ہیں اور یہ انسانوں کی طرح خود بخود کام کیسے کرتے ہیں۔ عام چیٹ بوٹ صرف سوال کا جواب دیتا ہے لیکن اے آئی ایجنٹ خود سوچتا ہے، منصوبہ بناتا ہے اور آپ کے دیے گئے ہدف کو مکمل کرتا ہے۔ مثال کے طور پر ویڈیو بنانا، ای میل بھیجنا اور ڈیٹا کا تجزیہ کرنا اب اے آئی ایجنٹس خود کر سکتے ہیں۔ مستقبل میں یہ ٹیکنالوجی ہر کاروبار کا لازمی حصہ بن جائے گی۔ مزید اے آئی معلومات کے لیے اے آئی ود عامر کے ساتھ جڑے رہیں۔ شکریہ!"
    },
    {
        "title": "YouTube Automation With Free AI Tools Complete Guide in Urdu",
        "urdu": "السلام علیکم دوستو! اے آئی ود عامر میں خوش آمدید۔ آج ہم آپ کو بتائیں گے کہ آپ سو فیصد مفت اے آئی ٹولز کے ذریعے یوٹیوب آٹومیشن چینل کیسے بنا سکتے ہیں۔ سب سے پہلے آپ کو ایک اچھا موضوع منتخب کرنا ہوتا ہے، اس کے بعد اردو سکرپٹ تیار کیا جاتا ہے اور پھر اے آئی آواز اور تصاویر کو جوڑ کر مکمل ویڈیو بنائی جاتی ہے۔ یوٹیوب کی پالیسی کے مطابق اگر آپ کی ویڈیو میں اصل آواز اور مفید معلومات شامل ہوں تو آپ کا چینل باآسانی مونیٹائز ہو سکتا ہے۔ مزید رہنمائی کے لیے سبسکرائب کرنا نہ بھولیں۔ شکریہ!"
    },
    {
        "title": "Mobile Phone Par Free AI Apps Se Content Creation Kaise Karein",
        "urdu": "السلام علیکم دوستو! اے آئی ود عامر میں خوش آمدید۔ اگر آپ کے پاس کمپیوٹر یا لیپ ٹاپ نہیں ہے تو پریشان ہونے کی بالکل ضرورت نہیں ہے۔ آج ہم آپ کو بتائیں گے کہ صرف اپنے اینڈرائیڈ موبائل فون پر مفت اے آئی ایپس استعمال کر کے بہترین ویڈیوز اور ڈیزائن کیسے بنائے جا سکتے ہیں۔ موبائل پر سکرپٹ لکھنے سے لے کر آواز ریکارڈ کرنے اور ایڈیٹنگ تک تمام کام چند منٹوں میں مکمل ہو جاتے ہیں۔ آج ہی اپنا ڈیجیٹل سفر شروع کریں اور اے آئی ود عامر کو سبسکرائب کریں۔ شکریہ!"
    }
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

def pick_unique_item():
    if MANUAL_TOPIC:
        return {"title": MANUAL_TOPIC, "urdu": TOPIC_ITEMS[0]["urdu"]}
    used = load_used_topics()
    available = [item for item in TOPIC_ITEMS if item["title"] not in used]
    if not available:
        used = []
        available = TOPIC_ITEMS[:]
    chosen = random.choice(available)
    save_used_topic(chosen["title"])
    return chosen

def has_urdu_script(text):
    urdu_chars = re.findall(r'[\u0600-\u06FF]', text)
    return len(urdu_chars) >= 40

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
    except Exception:
        pass
    return "topic"

def run_dify_workflow(topic):
    if not DIFY_API_KEY:
        return None
    var_name = get_dify_input_var()
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
            return result.get("data", {}).get("outputs", {})
    except Exception as e:
        print(f"Dify API fallback triggered: {e}")
        return None

def set_github_output(name, value):
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            delimiter = "EOF_AAMIR_8899"
            f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")

def main():
    item = pick_unique_item()
    topic = item["title"]
    print(f"Selected Unique Topic: {topic}")
    outputs = run_dify_workflow(topic)

    video_title = f"AI With Aamir - {topic}"
    urdu_script = ""
    seo_text = f"Title: {video_title}\nDescription: {topic} - Complete Urdu Guide by AI With Aamir.\nTags: AI With Aamir, AI in Urdu, Artificial Intelligence Pakistan, Online Earning"

    if outputs and isinstance(outputs, dict):
        for k, v in outputs.items():
            val = str(v).strip()
            if not val:
                continue
            if has_urdu_script(val) and len(val) > len(urdu_script):
                urdu_script = val
            if "seo" in k.lower() or "title" in k.lower() or "tag" in k.lower():
                seo_text = val

    if not has_urdu_script(urdu_script):
        print("Self-Healing: Ensuring pure Urdu Nastaliq script for Agent 6 edge-tts...")
        urdu_script = item["urdu"]

    set_github_output("video_title", video_title)
    set_github_output("urdu_script", urdu_script)
    set_github_output("seo_text", seo_text)
    print("Agent 0 Autonomous Brain completed with pure Urdu script!")

if __name__ == "__main__":
    main()
