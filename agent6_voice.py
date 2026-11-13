import asyncio
import json
import os
import re
import edge_tts

VOICE = "ur-PK-AsadNeural"
OUTPUT_DIR = "output/audio"

def split_urdu_script(script_text):
    raw_lines = [line.strip() for line in script_text.split("\n") if line.strip()]
    segments = []
    for line in raw_lines:
        parts = re.split(r'(?<=[۔!?])\s+', line)
        for p in parts:
            clean = p.strip()
            if clean:
                segments.append(clean)
    return segments

async def generate_segment_audio(index, text, out_dir):
    filename = f"seg_{index:03d}.mp3"
    filepath = os.path.join(out_dir, filename)
    communicate = edge_tts.Communicate(text, VOICE, rate="+0%", pitch="+0Hz")
    await communicate.save(filepath)
    return filepath

async def run_agent6(script_text):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    segments = split_urdu_script(script_text)
    manifest = []
    for idx, text in enumerate(segments, start=1):
        audio_path = await generate_segment_audio(idx, text, OUTPUT_DIR)
        manifest.append({
            "segment_id": idx,
            "urdu_text": text,
            "audio_file": audio_path
        })
        print(f"[Agent 6] Generated {audio_path} -> {text[:40]}")
    manifest_path = os.path.join(OUTPUT_DIR, "voice_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[Agent 6] Completed {len(manifest)} voice segments.")
    return manifest_path

if __name__ == "__main__":
    sample_script = os.environ.get(
        "URDU_SCRIPT",
        "السلام علیکم دوستو! AI With Aamir میں خوش آمدید۔ آج کی ویڈیو میں ہم سیکھیں گے کہ مصنوعی ذہانت سے کیسے فائدہ اٹھایا جائے۔"
    )
    asyncio.run(run_agent6(sample_script))
