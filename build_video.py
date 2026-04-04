import os, json, random, subprocess, asyncio, re
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from config import *

print("BUILD_V4_LOADED")

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

# ─── TTS ─────────────────────────────────────────────────────

async def try_voice(text, voice, audio_path, sub_path):
    comm = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    got = False
    with open(audio_path, "wb") as af:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                af.write(chunk["data"])
                got = True
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    if got:
        with open(sub_path, "w", encoding="utf-8") as sf:
            sf.write(submaker.generate_subs())
        return True
    if os.path.exists(audio_path):
        os.remove(audio_path)
    return False

async def generate_tts(text, lang_code, kind, audio_path, sub_path):
    kk = "short" if kind == "short" else "long"
    voices = VOICE_FALLBACKS.get(lang_code, VOICE_FALLBACKS["en"]).get(kk, VOICE_FALLBACKS["en"][kk])
    for v in voices:
        print(f"    Voice: {v}")
        try:
            if await try_voice(text, v, audio_path, sub_path):
                print(f"    OK: {v}")
                return True
            print(f"    No audio: {v}")
        except Exception as e:
            print(f"    Err: {str(e)[:50]}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
    return False

def clean_text(text):
    c = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '.', text)
    c = re.sub(r'\s+', ' ', c).strip()
    c = re.sub(r'(\.\s*){3,}', '. ', c)
    return c.strip('. ')

def vtt_to_srt(vp):
    with open(vp, "r", encoding="utf-8") as f:
        c = f.read()
    c = c.replace("WEBVTT", "").strip()
    c = re.sub(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})', lambda m: f"{m.group(1)}:{m.group(2)}:{m.group(3)},{m.group(4)}", c)
    sp = vp.replace(".vtt", ".srt")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(c)
    return sp

def get_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 60.0

# ─── CINEMATIC IMAGE PREPROCESSING ──────────────────────────
# Instead of slow zoompan, we use PIL to add cinematic effects
# to each image BEFORE feeding to FFmpeg. This is instant.

def make_cinematic(img_path, out_path, w, h):
    """Add dark overlay + vignette to make image look cinematic. Fast."""
    try:
        img = Image.open(img_path).convert("RGB")
        img = img.resize((w, h), Image.LANCZOS)
        # Darken
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.4)
        # Slight blur for dreamy effect
        img = img.filter(ImageFilter.GaussianBlur(1))
        # Vignette
        vignette = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(vignette)
        for i in range(max(w, h)//2, 0, -3):
            alpha = int(255 * (1 - (i / (max(w, h)//2)) ** 2) * 0.6)
            draw.ellipse([w//2-i, h//2-i, w//2+i, h//2+i], fill=(0, 0, 0))
        img = Image.blend(img, vignette, 0.5)
        img.save(out_path, quality=85)
        return True
    except:
        return False

# ─── FAST VIDEO RENDERING ───────────────────────────────────
# No zoompan! Static cinematic images with fade transitions.
# Renders 20-min video in ~3 minutes instead of timing out.

def render_video(images, audio_path, srt_path, output_path, is_short=False):
    w = SHORT_W if is_short else VIDEO_W
    h = SHORT_H if is_short else VIDEO_H
    duration = get_duration(audio_path)
    n = len(images)
    seg_dur = duration / n
    fps = FPS
    os.makedirs(TEMP, exist_ok=True)

    # Pre-process images for cinematic look
    print(f"    Pre-processing {n} images...")
    proc_imgs = []
    for i, ip in enumerate(images):
        op = os.path.join(TEMP, f"cin_{i:04d}.jpg")
        if not make_cinematic(ip, op, w, h):
            # Fallback: just resize
            try:
                Image.open(ip).convert("RGB").resize((w, h), Image.LANCZOS).save(op, quality=85)
            except:
                Image.new("RGB", (w, h), (10, 10, 18)).save(op, quality=85)
        proc_imgs.append(op)

    # Build concat file with fade transitions using xfade
    print(f"    Building video ({duration:.0f}s total, {n} segments)...")
    
    # Method: create each segment as a short clip, then xfade them together
    # For speed, we create segments in batches and concat
    clip_files = []
    for i, ip in enumerate(proc_imgs):
        cp = os.path.join(TEMP, f"seg_{i:04d}.mp4")
        fade_out = max(0, seg_dur - 0.5)
        vf = f"fade=t=in:st=0:d=0.5,fade=t=out:st={fade_out}:d=0.5,format=yuv420p"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps),
               "-i", ip, "-vf", vf, "-t", str(seg_dur),
               "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
               "-r", str(fps), "-pix_fmt", "yuv420p", cp]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not os.path.exists(cp):
            # Black frame fallback
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                           "-i", f"color=c=black:s={w}x{h}:d={seg_dur}:r={fps}",
                           "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
                           "-pix_fmt", "yuv420p", cp], capture_output=True, timeout=30)
        clip_files.append(cp)
        if (i + 1) % 5 == 0:
            print(f"    Segments: {i+1}/{n}")

    # Concatenate all segments
    cl = os.path.join(TEMP, "concat.txt")
    with open(cl, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")

    merged = os.path.join(TEMP, "merged.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", cl, "-c", "copy", merged],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not os.path.exists(merged):
        merged = clip_files[0]

    # Add audio + burn subtitles
    fs = 16 if is_short else 20
    esc = srt_path.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")
    cmd = [
        "ffmpeg", "-y", "-i", merged, "-i", audio_path,
        "-vf", f"subtitles='{esc}':force_style='FontSize={fs},PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=35'",
        "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"    Sub burn failed, merging without subs")
        subprocess.run(["ffmpeg", "-y", "-i", merged, "-i", audio_path,
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", output_path],
                       capture_output=True, timeout=300)

    if os.path.exists(output_path):
        mb = os.path.getsize(output_path) / (1024*1024)
        print(f"    Video done: {mb:.1f}MB")
    else:
        raise Exception("Video file not created")

# ─── THUMBNAIL ──────────────────────────────────────────────

def create_thumbnail(title, images, output_path, is_short=False):
    w = SHORT_W if is_short else 1280
    h = SHORT_H if is_short else 720
    bg = Image.new("RGB", (w, h), (10, 10, 18))
    if images:
        try:
            b = Image.open(random.choice(images)).convert("RGB").resize((w, h), Image.LANCZOS)
            b = b.filter(ImageFilter.GaussianBlur(12)).point(lambda p: int(p*0.25))
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
            if draw.textlength(test, font=f) <= mw: cur = test
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

# ─── MAIN ───────────────────────────────────────────────────

def process_language(lang_code, is_short=False):
    info = LANGUAGES[lang_code]
    kind = "short" if is_short else "long"
    sp = os.path.join(OUT, "scripts", f"{kind}_{lang_code}.txt")
    if not os.path.exists(sp):
        print(f"  SKIP: no script for {lang_code} {kind}")
        return None

    raw = open(sp, "r", encoding="utf-8").read()
    clean = clean_text(raw)
    if len(re.sub(r'[^\w]', '', clean)) < 20:
        print(f"  SKIP: text too short for {lang_code} {kind}")
        return None

    print(f"Processing {info['name']} {kind} ({len(clean.split())} words)...")

    ap = os.path.join(OUT, f"audio_{kind}_{lang_code}.mp3")
    vp = os.path.join(OUT, f"subs_{kind}_{lang_code}.vtt")

    ok = asyncio.run(generate_tts(clean, lang_code, kind, ap, vp))
    if not ok or not os.path.exists(ap) or os.path.getsize(ap) < 1000:
        print(f"  FAIL: TTS for {lang_code} {kind}")
        return None

    srt = vtt_to_srt(vp)
    all_imgs = sorted([os.path.join(IMGS, f) for f in os.listdir(IMGS) if f.lower().endswith(('.jpg','.jpeg','.png'))])
    if not all_imgs:
        print(f"  FAIL: no images")
        return None
    ni = IMAGES_PER_SHORT if is_short else min(25, IMAGES_PER_VIDEO)
    imgs = random.sample(all_imgs, min(ni, len(all_imgs)))

    vidp = os.path.join(OUT, f"video_{kind}_{lang_code}.mp4")
    try:
        render_video(imgs, ap, srt, vidp, is_short)
    except Exception as e:
        print(f"  FAIL: render - {e}")
        return None
    if not os.path.exists(vidp):
        return None

    thp = os.path.join(OUT, f"thumb_{kind}_{lang_code}.jpg")
    try:
        create_thumbnail(f"{info['name']} Crime Story", imgs, thp, is_short)
    except:
        try:
            fb = Image.new("RGB", (1280 if not is_short else 1080, 720 if not is_short else 1920), (10,10,18))
            ImageDraw.Draw(fb).text((40, 360 if not is_short else 960), "TRUE CRIME", fill=(196,30,58))
            fb.save(thp, quality=95)
        except:
            pass
    return {"video": vidp, "thumbnail": thp, "lang": lang_code, "kind": kind}

def main():
    lc = os.environ.get("LANG_CODE", "en")
    iss = os.environ.get("VIDEO_TYPE", "long") == "short"
    r = process_language(lc, iss)
    if r:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump(r, f)
        print(f"\nDone: {lc} {'short' if iss else 'long'}")
    else:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump({"skip": True}, f)
        print(f"\nSkipped: {lc} {'short' if iss else 'long'}")

if __name__ == "__main__":
    main()
