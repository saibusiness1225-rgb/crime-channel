import os, json, random, subprocess, asyncio, re, math
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from config import *

print("DOCUMENTARY_BUILDER_V5")

# ═══════════════════════════════════════════════════════════════
# VOICE FALLBACKS
# ═══════════════════════════════════════════════════════════════
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

SECTION_NAMES = {
    "HOOK": "", "INTRO": "THE STORY BEGINS", "BACKGROUND": "THE BACKGROUND",
    "THE CRIME": "THE CRIME", "INVESTIGATION": "THE INVESTIGATION",
    "SUSPECTS": "THE SUSPECTS", "RESOLUTION": "THE RESOLUTION",
    "CONCLUSION": "THE AFTERMATH",
}

DRAMATIC_WORDS = [
    "never", "vanished", "screaming", "blood", "body", "discovered",
    "horror", "terrified", "dark", "death", "murder", "killer",
    "victim", "scream", "silence", "broken", "cold", "night",
    "alone", "afraid", "feared", "grave", "missing", "found dead",
    "brutal", "chilling", "haunting", "mystery", "evil", "monster",
    "weapon", "witness", "confession", "guilty", "innocent",
]

# ═══════════════════════════════════════════════════════════════
# TTS
# ═══════════════════════════════════════════════════════════════
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
    c = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '. ', text)
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

# ═══════════════════════════════════════════════════════════════
# SCRIPT PARSING — Extract sections, dramatic lines, facts
# ═══════════════════════════════════════════════════════════════
def parse_sections(script):
    markers = ['HOOK','INTRO','BACKGROUND','THE CRIME','INVESTIGATION','SUSPECTS','RESOLUTION','CONCLUSION']
    sections = []
    current = {"name": "INTRO", "text": ""}
    for line in script.split('\n'):
        found = None
        for m in markers:
            if f'[{m}]' in line:
                found = m
                break
        if found:
            if current["text"].strip():
                sections.append(current)
            current = {"name": found, "text": re.sub(r'\[.*?\]', '', line).strip()}
        else:
            clean = re.sub(r'\[(PAUSE|SCENE CHANGE)\]', '', line).strip()
            if clean:
                current["text"] += " " + clean
    if current["text"].strip():
        sections.append(current)
    return [s for s in sections if s["text"].strip()]

def extract_dramatic_lines(text, count=2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    scored = []
    for s in sentences:
        s = s.strip().strip('"').strip()
        if 15 < len(s) < 100:
            score = sum(1 for w in DRAMATIC_WORDS if w in s.lower())
            if score > 0:
                scored.append((s, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:count]]

def extract_facts(text, count=2):
    facts = []
    dates = re.findall(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', text)
    facts.extend(dates)
    years = re.findall(r'\b((?:19|20)\d{2})\b', text)
    for y in years:
        if f"In {y}" not in facts:
            facts.append(f"In {y}")
    return list(set(facts))[:count]

def calc_timings(sections, total_dur):
    tw = sum(len(s["text"].split()) for s in sections)
    if tw == 0:
        return []
    timings = []
    cum = 0
    for s in sections:
        w = len(s["text"].split())
        start = (cum / tw) * total_dur
        dur = (w / tw) * total_dur
        timings.append({"name": s["name"], "start": start, "duration": dur, "text": s["text"]})
        cum += w
    return timings

# ═══════════════════════════════════════════════════════════════
# SLIDE GENERATION — 4 types of documentary-style slides
# ═══════════════════════════════════════════════════════════════
def load_fonts(is_short=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]
    fb_path = fs_path = None
    for p in paths:
        if os.path.exists(p):
            if fb_path is None:
                fb_path = p
            elif fs_path is None:
                fs_path = p
                break
    if not fb_path:
        fb_path = fs_path = ""  # will use default
    if not fs_path:
        fs_path = fb_path
    scale = 1.4 if is_short else 1.0
    try:
        fb = ImageFont.truetype(fb_path, int(48 * scale))
        fs = ImageFont.truetype(fs_path, int(22 * scale))
        fl = ImageFont.truetype(fb_path, int(36 * scale))
        fxl = ImageFont.truetype(fb_path, int(60 * scale))
    except:
        fb = fs = fl = fxl = ImageFont.load_default()
    return fb, fs, fl, fxl

def make_dark_bg(w, h):
    bg = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(bg)
    for y in range(h):
        f = 1.0 - (y / h) * 0.5
        draw.line([(0, y), (w, y)], fill=(int(8*f), int(8*f), int(15*f)))
    return bg

def slide_cinematic(img_path, caption, out_path, w, h, fonts):
    """Darkened photo with red accent line + caption bar at bottom."""
    fb, fs, fl, fxl = fonts
    try:
        img = Image.open(img_path).convert("RGB")
        img = img.resize((w, h), Image.LANCZOS)
        enh = ImageEnhance.Brightness(img)
        img = enh.enhance(0.35)
        img = img.filter(ImageFilter.GaussianBlur(2))
    except:
        img = make_dark_bg(w, h)

    # Dark overlay
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 120))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Red accent line at bottom
    bar_y = h - 80
    draw.rectangle([0, bar_y, w, bar_y + 3], fill=(196, 30, 58))

    # Caption text
    if caption:
        def wrap(t, f, mw):
            lines, cur = [], ""
            for word in t.split():
                test = cur + " " + word if cur else word
                if draw.textlength(test, font=f) <= mw: cur = test
                else:
                    if cur: lines.append(cur)
                    cur = word
            if cur: lines.append(cur)
            return lines[:2]  # max 2 lines
        lines = wrap(caption, fs, w - 60)
        for i, line in enumerate(lines):
            y = bar_y + 12 + i * 26
            draw.text((30, y), line, font=fs, fill=(200, 200, 210))

    img.save(out_path, quality=88)

def slide_section_title(name, out_path, w, h, fonts, bg_img=None):
    """Dark cinematic section title card."""
    fb, fs, fl, fxl = fonts
    if bg_img:
        try:
            bg = Image.open(bg_img).convert("RGB").resize((w, h), Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(15)).point(lambda p: int(p * 0.15))
        except:
            bg = make_dark_bg(w, h)
    else:
        bg = make_dark_bg(w, h)

    ov = Image.new("RGBA", (w, h), (0, 0, 0, 160))
    img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Red line top
    draw.rectangle([0, h//2 - 45, w, h//2 - 42], fill=(196, 30, 58))
    # Title
    draw.text((0, 0), name, font=fxl, fill=(255, 255, 255))
    bb = draw.textbbox((0, 0), name, font=fxl)
    tw = bb[2] - bb[0]
    draw.text(((w - tw) // 2, h // 2 - 35), name, font=fxl, fill=(255, 255, 255))
    # Red line bottom
    draw.rectangle([0, h//2 + 30, w, h//2 + 33], fill=(196, 30, 58))

    img.save(out_path, quality=88)

def slide_dramatic_text(text, out_path, w, h, fonts):
    """Dark background with large dramatic quote."""
    fb, fs, fl, fxl = fonts
    img = make_dark_bg(w, h)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 100))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Red quotation mark
    draw.text((w//2 - 200, h//2 - 120), '"', font=ImageFont.load_default(), fill=(196, 30, 58))
    try:
        qfont = ImageFont.truetype(fonts[0].path if hasattr(fonts[0], 'path') else "", int(40 * (1.4 if h > 1000 else 1.0)))
    except:
        qfont = fl

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

    lines = wrap(text, fl, w - 120)
    total_h = len(lines) * 48
    sy = (h - total_h) // 2
    for i, line in enumerate(lines):
        y = sy + i * 48
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((60+dx, y+dy), line, font=fl, fill=(0, 0, 0))
        draw.text((60, y), line, font=fl, fill=(230, 230, 240))

    img.save(out_path, quality=88)

def slide_info_card(label, value, out_path, w, h, fonts):
    """Clean info display — date, name, location."""
    fb, fs, fl, fxl = fonts
    img = make_dark_bg(w, h)
    draw = ImageDraw.Draw(img)

    # Left red bar
    draw.rectangle([60, h//2 - 60, 63, h//2 + 60], fill=(196, 30, 58))
    # Label (small, muted)
    draw.text((90, h//2 - 45), label.upper(), font=fs, fill=(120, 120, 140))
    # Value (large, white)
    draw.text((90, h//2 - 5), value, font=fb, fill=(255, 255, 255))

    img.save(out_path, quality=88)

def slide_subscribe(out_path, w, h, fonts):
    """End card with subscribe CTA."""
    fb, fs, fl, fxl = fonts
    img = make_dark_bg(w, h)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 140))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, h//2 - 3, w, h//2 + 3], fill=(196, 30, 58))
    txt = "SUBSCRIBE"
    bb = draw.textbbox((0, 0), txt, font=fxl)
    tw = bb[2] - bb[0]
    draw.text(((w - tw) // 2, h//2 + 20), txt, font=fxl, fill=(255, 255, 255))

    sub = "FOR MORE TRUE CRIME STORIES"
    bb2 = draw.textbbox((0, 0), sub, font=fs)
    tw2 = bb2[2] - bb2[0]
    draw.text(((w - tw2) // 2, h//2 + 90), sub, font=fs, fill=(140, 140, 160))

    img.save(out_path, quality=88)

# ═══════════════════════════════════════════════════════════════
# BACKGROUND MUSIC — Dark ambient drone via FFmpeg
# ═══════════════════════════════════════════════════════════════
def generate_music(duration, out_path):
    """Generate dark ambient drone using FFmpeg's sine oscillator."""
    dur = int(duration) + 10
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={dur}",
        "-f", "lavfi", "-i", f"sine=frequency=82.41:duration={dur}",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={dur}",
        "-filter_complex",
        "[0]volume=0.25[a];[1]volume=0.15[b];[2]volume=0.08[c];"
        "[a][b][c]amix=inputs=3:duration=longest,"
        "aecho=0.8:0.88:60:0.4,lowpass=f=250,volume=0.10",
        "-c:a", "aac", "-b:a", "48k", out_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not os.path.exists(out_path):
        print("    Music generation failed, continuing without")
        return False
    print(f"    Music: {os.path.getsize(out_path)/(1024):.0f}KB")
    return True

# ═══════════════════════════════════════════════════════════════
# VIDEO ASSEMBLY — Generate slides + FFmpeg concat + audio
# ═══════════════════════════════════════════════════════════════
def build_slide_sequence(timings, images, audio_dur, is_short):
    """Plan the sequence of slides with their durations."""
    slides = []  # list of (type, data, duration)
    w = SHORT_W if is_short else VIDEO_W
    h = SHORT_H if is_short else VIDEO_H

    # Intro card (3 seconds)
    slides.append(("section", "TRUE CRIME", 3.0))

    img_idx = 0
    for t in timings:
        sec_dur = t["duration"]
        name = t["name"]

        # Section title card (skip for HOOK)
        display = SECTION_NAMES.get(name, "")
        if display:
            slides.append(("section", display, 4.0))
            sec_dur -= 4.0

        if sec_dur <= 0:
            continue

        # Extract content for this section
        dramatic = extract_dramatic_lines(t["text"], 2)
        facts = extract_facts(t["text"], 2)

        # Build slide mix for this section
        slide_dur = 18.0 if not is_short else 8.0
        remaining = sec_dur
        content_added = False

        while remaining > 2:
            if not content_added and img_idx < len(images):
                slides.append(("cinematic", images[img_idx], min(slide_dur, remaining)))
                img_idx += 1
                remaining -= min(slide_dur, remaining)
                content_added = True
            elif dramatic:
                slides.append(("dramatic", dramatic.pop(0), min(15.0 if not is_short else 6.0, remaining)))
                remaining -= min(15.0 if not is_short else 6.0, remaining)
            elif img_idx < len(images):
                slides.append(("cinematic", images[img_idx], min(slide_dur, remaining)))
                img_idx += 1
                remaining -= min(slide_dur, remaining)
            elif facts:
                slides.append(("info", ("KEY DATE", facts.pop(0)), min(10.0 if not is_short else 5.0, remaining)))
                remaining -= min(10.0 if not is_short else 5.0, remaining)
            else:
                slides.append(("cinematic", images[img_idx % len(images)], min(slide_dur, remaining)))
                img_idx += 1
                remaining -= min(slide_dur, remaining)

    # Subscribe end card (4 seconds)
    slides.append(("subscribe", "", 4.0))

    # Adjust total to match audio duration
    total = sum(s[2] for s in slides)
    if total > 0 and abs(total - audio_dur) > 2:
        ratio = audio_dur / total
        slides = [(s[0], s[1], s[2] * ratio) for s in slides]

    return slides

def render_video(images, audio_path, srt_path, output_path, is_short=False):
    w = SHORT_W if is_short else VIDEO_W
    h = SHORT_H if is_short else VIDEO_H
    audio_dur = get_duration(audio_path)
    fonts = load_fonts(is_short)
    os.makedirs(TEMP, exist_ok=True)

    # Read script for section parsing
    lang_code = os.environ.get("LANG_CODE", "en")
    kind = "short" if is_short else "long"
    script_path = os.path.join(OUT, "scripts", f"{kind}_{lang_code}.txt")
    script = ""
    if os.path.exists(script_path):
        script = open(script_path, "r", encoding="utf-8").read()

    # Parse sections and build slide sequence
    if script:
        sections = parse_sections(script)
        timings = calc_timings(sections, audio_dur)
        print(f"    Parsed {len(sections)} sections")
    else:
        timings = [{"name": "MAIN", "start": 0, "duration": audio_dur, "text": ""}]

    slides = build_slide_sequence(timings, images, audio_dur, is_short)
    print(f"    Generated {len(slides)} slide plan")

    # Render each slide to JPEG
    print(f"    Rendering slides...")
    slide_paths = []
    for i, (stype, data, dur) in enumerate(slides):
        sp = os.path.join(TEMP, f"slide_{i:04d}.jpg")
        try:
            if stype == "cinematic":
                caption = ""
                if isinstance(data, str) and os.path.exists(data):
                    fname = os.path.basename(data)
                    caption = fname.replace(".jpg", "").replace("_", " ").title()[:60]
                slide_cinematic(data, caption, sp, w, h, fonts)
            elif stype == "section":
                bg = random.choice(images) if images else None
                slide_section_title(data, sp, w, h, fonts, bg)
            elif stype == "dramatic":
                slide_dramatic_text(str(data), sp, w, h, fonts)
            elif stype == "info":
                label, value = data if isinstance(data, tuple) else ("FACT", str(data))
                slide_info_card(label, value, sp, w, h, fonts)
            elif stype == "subscribe":
                slide_subscribe(sp, w, h, fonts)
            else:
                make_dark_bg(w, h).save(sp, quality=88)
            slide_paths.append(sp)
        except Exception as e:
            print(f"    Slide {i} failed: {str(e)[:50]}")
            make_dark_bg(w, h).save(sp, quality=88)
            slide_paths.append(sp)

    # Write concat file
    cl = os.path.join(TEMP, "slides.txt")
    with open(cl, "w") as f:
        for i, (_, _, dur) in enumerate(slides):
            f.write(f"file '{slide_paths[i]}'\n")
            f.write(f"duration {dur:.3f}\n")
        # Repeat last slide (required by concat demuxer)
        f.write(f"file '{slide_paths[-1]}'\n")

    # Generate background music
    music_path = os.path.join(TEMP, "music.mp3")
    has_music = generate_music(audio_dur, music_path)

    # Build FFmpeg command
    inputs = ["-f", "concat", "-safe", "0", "-i", cl, "-i", audio_path]
    filter_parts = []
    if has_music:
        inputs += ["-i", music_path]
        filter_parts.append(f"[1:a][2:a]amix=inputs=2:duration=first:weights=1 0.3[aout]")
    else:
        filter_parts.append("[1:a]acopy[aout]")

    fs = 18 if is_short else 22
    esc = srt_path.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")
    vf = f"[0:v]fps=8,format=yuv420p,subtitles='{esc}':force_style='FontSize={fs},PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=35'[vout]"

    filter_parts.append(vf)
    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print(f"    Encoding video...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if r.returncode != 0:
        print(f"    Full encode failed, trying without subs...")
        # Fallback: no subtitles, no music
        cmd2 = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", cl, "-i", audio_path,
                "-map", "0:v", "-map", "1:a",
                "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
                output_path]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
        if r2.returncode != 0:
            raise Exception(f"Video encode failed: {r2.stderr[:200]}")

    if os.path.exists(output_path):
        mb = os.path.getsize(output_path) / (1024*1024)
        print(f"    Video done: {mb:.1f}MB ({audio_dur:.0f}s)")
    else:
        raise Exception("Video file not created")

# ═══════════════════════════════════════════════════════════════
# THUMBNAIL
# ═══════════════════════════════════════════════════════════════
def create_thumbnail(title, images, output_path, is_short=False):
    w = SHORT_W if is_short else 1280
    h = SHORT_H if is_short else 720
    bg = make_dark_bg(w, h)
    if images:
        try:
            b = Image.open(random.choice(images)).convert("RGB").resize((w, h), Image.LANCZOS)
            b = b.filter(ImageFilter.GaussianBlur(12)).point(lambda p: int(p*0.2))
            ov = Image.new("RGBA", (w, h), (0, 0, 0, 150))
            bg = Image.alpha_composite(b.convert("RGBA"), ov).convert("RGB")
        except:
            pass
    draw = ImageDraw.Draw(bg)
    by = (h//2 - 3) if not is_short else (h*2//3)
    draw.rectangle([0, by, w, by + 5], fill=(196, 30, 58))
    fonts = load_fonts(is_short)
    fb = fonts[0]
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
    lines = wrap(title, fb, w - 80)
    sy = (by - len(lines) * 64) // 2
    for i, line in enumerate(lines):
        y = sy + i * 64
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((40+dx, y+dy), line, font=fb, fill=(0,0,0))
        draw.text((40, y), line, font=fb, fill=(255,255,255))
    draw.text((40, by + 22), "TRUE CRIME", font=fonts[1], fill=(196, 30, 58))
    bg.save(output_path, quality=95)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def process_language(lang_code, is_short=False):
    info = LANGUAGES[lang_code]
    kind = "short" if is_short else "long"
    sp = os.path.join(OUT, "scripts", f"{kind}_{lang_code}.txt")
    if not os.path.exists(sp):
        print(f"  SKIP: no script")
        return None

    raw = open(sp, "r", encoding="utf-8").read()
    clean = clean_text(raw)
    if len(re.sub(r'[^\w]', '', clean)) < 20:
        print(f"  SKIP: text too short")
        return None

    print(f"Processing {info['name']} {kind} ({len(clean.split())} words)...")

    ap = os.path.join(OUT, f"audio_{kind}_{lang_code}.mp3")
    vp = os.path.join(OUT, f"subs_{kind}_{lang_code}.vtt")

    ok = asyncio.run(generate_tts(clean, lang_code, kind, ap, vp))
    if not ok or not os.path.exists(ap) or os.path.getsize(ap) < 1000:
        print(f"  FAIL: TTS")
        return None

    srt = vtt_to_srt(vp)
    all_imgs = sorted([os.path.join(IMGS, f) for f in os.listdir(IMGS) if f.lower().endswith(('.jpg','.jpeg','.png'))])
    if not all_imgs:
        print(f"  FAIL: no images")
        return None
    ni = IMAGES_PER_SHORT if is_short else min(30, IMAGES_PER_VIDEO)
    imgs = random.sample(all_imgs, min(ni, len(all_imgs)))

    vidp = os.path.join(OUT, f"video_{kind}_{lang_code}.mp4")
    try:
        render_video(imgs, ap, srt, vidp, is_short)
    except Exception as e:
        print(f"  FAIL: {e}")
        return None
    if not os.path.exists(vidp):
        return None

    thp = os.path.join(OUT, f"thumb_{kind}_{lang_code}.jpg")
    try:
        create_thumbnail(f"{info['name']} Crime Story", imgs, thp, is_short)
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
