import os, json, random, subprocess, asyncio, re
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import *

VOICE_FALLBACKS = {
    "en": {"long": ["en-US-GuyNeural","en-US-DavisNeural","en-US-JaredNeural"], "short": ["en-US-AriaNeural","en-US-JennyNeural"]},
    "es": {"long": ["es-ES-AlvaroNeural","es-ES-SergioNeural","es-MX-JorgeNeural"], "short": ["es-ES-ElviraNeural","es-ES-LuciaNeural"]},
    "hi": {"long": ["hi-IN-MadhurNeural","hi-IN-SwaraNeural"], "short": ["hi-IN-SwaraNeural","hi-IN-MadhurNeural"]},
    "fr": {"long": ["fr-FR-HenriNeural","fr-FR-BrigitteNeural"], "short": ["fr-FR-DeniseNeural","fr-FR-LucieNeural"]},
    "pt": {"long": ["pt-BR-AntonioNeural","pt-BR-RicardoNeural"], "short": ["pt-BR-FranciscaNeural","pt-BR-LeticiaNeural"]},
    "de": {"long": ["de-DE-ConradNeural","de-DE-AmalaNeural"], "short": ["de-DE-KatjaNeural","de-DE-GiselaNeural"]},
    "ja": {"long": ["ja-JP-KeitaNeural","ja-JP-NaokiNeural"], "short": ["ja-JP-NanamiNeural","ja-JP-MizukiNeural"]},
    "ar": {"long": ["ar-SA-NaayfNeural","ar-AE-FatimaNeural"], "short": ["ar-SA-LailaNeural","ar-AE-MaryamNeural"]},
}

async def try_voice(text, voice, audio_path, sub_path):
    comm = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    got_audio = False
    with open(audio_path, "wb") as af:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                af.write(chunk["data"])
                got_audio = True
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    if got_audio:
        with open(sub_path, "w", encoding="utf-8") as sf:
            sf.write(submaker.generate_subs())
        return True
    if os.path.exists(audio_path):
        os.remove(audio_path)
    return False

async def generate_tts(text, lang_code, kind, audio_path, sub_path):
    kind_key = "short" if kind == "short" else "long"
    voices = VOICE_FALLBACKS.get(lang_code, VOICE_FALLBACKS["en"]).get(kind_key, VOICE_FALLBACKS["en"][kind_key])
    for voice in voices:
        print(f"    Trying: {voice}")
        try:
            if await try_voice(text, voice, audio_path, sub_path):
                print(f"    OK: {voice}")
                return True
            print(f"    No audio from {voice}")
        except Exception as e:
            print(f"    Failed: {voice} - {str(e)[:60]}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
    print(f"    All voices failed for {lang_code}")
    return False

def clean_text(text):
    clean = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '.', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = re.sub(r'(\.\s*){3,}', '. ', clean)
    return clean.strip('. ')

def vtt_to_srt(vtt_path):
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("WEBVTT", "").strip()
    content = re.sub(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})', lambda m: f"{m.group(1)}:{m.group(2)}:{m.group(3)},{m.group(4)}", content)
    srt_path = vtt_path.replace(".vtt", ".srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(content)
    return srt_path

def get_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 60.0

def render_video(images, audio_path, srt_path, output_path, is_short=False):
    w = SHORT_W if is_short else VIDEO_W
    h = SHORT_H if is_short else VIDEO_H
    duration = get_duration(audio_path)
    n = len(images)
    seg_dur = duration / n
    fps = FPS
    os.makedirs(TEMP, exist_ok=True)
    clip_files = []

    for i, img_path in enumerate(images):
        clip_path = os.path.join(TEMP, f"clip_{i:04d}.mp4")
        frames = max(1, int(seg_dur * fps))
        ze = random.uniform(1.08, 1.25)
        px = random.uniform(-30, 30)
        py = random.uniform(-30, 30)
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
              f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
              f"zoompan=z='1.0+({ze}-1.0)*on/{frames}':x='iw/2-(iw/zoom/2)+{px}*on/{frames}':y='ih/2-(ih/zoom/2)+{py}*on/{frames}':d={frames}:s={w}x{h}:fps={fps},"
              f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0, seg_dur-0.4)}:d=0.4,format=yuv420p")
        r = subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", img_path, "-vf", vf, "-t", str(seg_dur), "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF), clip_path], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:d={seg_dur}:r={fps}", "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF), clip_path], capture_output=True, timeout=30)
        clip_files.append(clip_path)
        if (i + 1) % 10 == 0:
            print(f"    Clips: {i+1}/{n}")

    concat_list = os.path.join(TEMP, "concat.txt")
    with open(concat_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")
    concat_out = os.path.join(TEMP, "merged.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", concat_out], capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not os.path.exists(concat_out):
        concat_out = clip_files[0]

    fs = 16 if is_short else 20
    esc = srt_path.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")
    cmd = ["ffmpeg", "-y", "-i", concat_out, "-i", audio_path,
           "-vf", f"subtitles='{esc}':force_style='FontSize={fs},PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=35'",
           "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF), "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", output_path]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        subprocess.run(["ffmpeg", "-y", "-i", concat_out, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", output_path], capture_output=True, timeout=300)
    if os.path.exists(output_path):
        print(f"    Video: {os.path.basename(output_path)} ({os.path.getsize(output_path)/(1024*1024):.1f}MB)")
    else:
        raise Exception("Video not created")

def create_thumbnail(title, images, output_path, is_short=False):
    w = SHORT_W if is_short else 1280
    h = SHORT_H if is_short else 720
    bg = Image.new("RGB", (w, h), (10, 10, 18))
    if images:
        try:
            b = Image.open(random.choice(images)).convert("RGB").resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(12)).point(lambda p: int(p*0.25))
            ov = Image.new("RGBA", (w, h), (0, 0, 0, 140))
            bg = Image.alpha_composite(b.convert("RGBA"), ov).convert("RGB")
        except:
            pass
    draw = ImageDraw.Draw(bg)
    by = (h//2-3) if not is_short else (h*2//3)
    draw.rectangle([0, by, w, by+4], fill=(196, 30, 58))
    try:
        fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52 if not is_short else 48)
        fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        fb = fs = ImageFont.load_default()
    def wrap(t, f, mw):
        lines, cur = [], ""
        for word in t.split():
            test = cur + " " + word if cur else word
            if draw.textlength(test, font=f) <= mw:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = word
        if cur: lines.append(cur)
        return lines
    lines = wrap(title, fb, w-80)
    sy = (by - len(lines)*62) // 2
    for i, line in enumerate(lines):
        y = sy + i * 62
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((40+dx, y+dy), line, font=fb, fill=(0,0,0))
        draw.text((40, y), line, font=fb, fill=(255,255,255))
    draw.text((40, by+20), "TRUE CRIME", font=fs, fill=(196, 30, 58))
    bg.save(output_path, quality=95)
    print(f"    Thumb: {os.path.basename(output_path)}")

def process_language(lang_code, is_short=False):
    info = LANGUAGES[lang_code]
    kind = "short" if is_short else "long"
    script_path = os.path.join(OUT, "scripts", f"{kind}_{lang_code}.txt")
    if not os.path.exists(script_path):
        print(f"  SKIP {lang_code} {kind}: no script")
        return None

    raw = open(script_path, "r", encoding="utf-8").read()
    clean = clean_text(raw)
    if len(re.sub(r'[^\w]', '', clean)) < 20:
        print(f"  SKIP {lang_code} {kind}: text too short")
        return None

    print(f"Processing {info['name']} {kind} ({len(clean.split())} words)...")
    audio_path = os.path.join(OUT, f"audio_{kind}_{lang_code}.mp3")
    vtt_path = os.path.join(OUT, f"subs_{kind}_{lang_code}.vtt")

    ok = asyncio.run(generate_tts(clean, lang_code, kind, audio_path, vtt_path))
    if not ok or not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
        print(f"  FAIL {lang_code} {kind}: TTS failed")
        return None

    srt_path = vtt_to_srt(vtt_path)
    all_imgs = sorted([os.path.join(IMGS, f) for f in os.listdir(IMGS) if f.lower().endswith(('.jpg','.jpeg','.png'))])
    if not all_imgs:
        print(f"  FAIL: no images")
        return None
    n_imgs = IMAGES_PER_SHORT if is_short else IMAGES_PER_VIDEO
    imgs = random.sample(all_imgs, min(n_imgs, len(all_imgs)))

    video_path = os.path.join(OUT, f"video_{kind}_{lang_code}.mp4")
    try:
        render_video(imgs, audio_path, srt_path, video_path, is_short)
    except Exception as e:
        print(f"  FAIL {lang_code} {kind}: render error - {e}")
        return None
    if not os.path.exists(video_path):
        return None

    thumb_path = os.path.join(OUT, f"thumb_{kind}_{lang_code}.jpg")
    try:
        create_thumbnail(f"{info['name']} Crime Story", imgs, thumb_path, is_short)
    except:
        try:
            fb = Image.new("RGB", (1280 if not is_short else 1080, 720 if not is_short else 1920), (10,10,18))
            ImageDraw.Draw(fb).text((40, 360 if not is_short else 960), "TRUE CRIME", fill=(196,30,58))
            fb.save(thumb_path, quality=95)
        except:
            pass
    return {"video": video_path, "thumbnail": thumb_path, "lang": lang_code, "kind": kind}

def main():
    lang_code = os.environ.get("LANG_CODE", "en")
    is_short = os.environ.get("VIDEO_TYPE", "long") == "short"
    result = process_language(lang_code, is_short)
    if result:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump(result, f)
        print(f"\nDone: {lang_code} {'short' if is_short else 'long'}")
    else:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump({"skip": True}, f)
        print(f"\nSkipped: {lang_code} {'short' if is_short else 'long'}")

if __name__ == "__main__":
    main()
