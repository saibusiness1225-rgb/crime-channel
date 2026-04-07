import os, json, random, subprocess, asyncio, re
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from config import *

print("CRIME_BOT_V7")

VOICES = {
    "en": {"long": ["en-US-GuyNeural", "en-US-AndrewNeural", "en-US-BrianNeural"], "short": ["en-US-AriaNeural", "en-US-JennyNeural"]},
    "es": {"long": ["es-ES-AlvaroNeural", "es-ES-SergioNeural"], "short": ["es-ES-ElviraNeural", "es-ES-LuciaNeural"]},
    "hi": {"long": ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"], "short": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"]},
    "fr": {"long": ["fr-FR-HenriNeural", "fr-FR-BrigitteNeural"], "short": ["fr-FR-DeniseNeural", "fr-FR-LucieNeural"]},
    "pt": {"long": ["pt-BR-AntonioNeural", "pt-BR-RicardoNeural"], "short": ["pt-BR-FranciscaNeural", "pt-BR-LeticiaNeural"]},
    "de": {"long": ["de-DE-ConradNeural", "de-DE-AmalaNeural"], "short": ["de-DE-KatjaNeural", "de-DE-GiselaNeural"]},
    "ja": {"long": ["ja-JP-KeitaNeural", "ja-JP-NaokiNeural"], "short": ["ja-JP-NanamiNeural", "ja-JP-MizukiNeural"]},
    "ar": {"long": ["ar-SA-NaayfNeural", "ar-AE-FatimaNeural"], "short": ["ar-SA-LailaNeural", "ar-AE-MaryamNeural"]},
}

SEC_TITLES = {
    "HOOK": "", "INTRO": "THE STORY BEGINS", "BACKGROUND": "THE BACKGROUND",
    "THE CRIME": "THE CRIME", "INVESTIGATION": "THE INVESTIGATION",
    "SUSPECTS": "THE SUSPECTS", "RESOLUTION": "THE RESOLUTION",
    "CONCLUSION": "THE AFTERMATH",
}


async def try_voice(text, voice, ap, sp):
    comm = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    got = False
    with open(ap, "wb") as af:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                af.write(chunk["data"])
                got = True
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    if got:
        subs = ""
        try:
            subs = submaker.generate_subs()
        except AttributeError:
            try:
                subs = submaker.generate_subtitles()
            except AttributeError:
                subs = str(submaker)
        with open(sp, "w", encoding="utf-8") as sf:
            sf.write(subs)
        return True
    if os.path.exists(ap):
        os.remove(ap)
    return False


async def gen_tts(text, lc, kind, ap, sp):
    kk = "short" if kind == "short" else "long"
    vs = VOICES.get(lc, VOICES["en"]).get(kk, VOICES["en"][kk])
    for v in vs:
        print(f"    Voice: {v}")
        try:
            if await try_voice(text, v, ap, sp):
                print(f"    OK: {v}")
                return True
            print(f"    No audio: {v}")
        except Exception as e:
            print(f"    Err: {str(e)[:60]}")
            if os.path.exists(ap):
                os.remove(ap)
    return False


def clean_text(t):
    c = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '.', t)
    return re.sub(r'(\.\s*){3,}', '. ', re.sub(r'\s+', ' ', c).strip()).strip('. ')


def vtt_to_srt(vp):
    with open(vp, "r", encoding="utf-8") as f:
        c = f.read()
    c = re.sub(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})',
               lambda m: f"{m.group(1)}:{m.group(2)}:{m.group(3)},{m.group(4)}",
               c.replace("WEBVTT", "").strip())
    sp = vp.replace(".vtt", ".srt")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(c)
    return sp


def get_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", p],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 60.0


def parse_sections(s):
    ms = ['HOOK', 'INTRO', 'BACKGROUND', 'THE CRIME', 'INVESTIGATION', 'SUSPECTS', 'RESOLUTION', 'CONCLUSION']
    secs = []
    cur = {"name": "INTRO", "text": ""}
    for l in s.split('\n'):
        fd = None
        for m in ms:
            if f'[{m}]' in l:
                fd = m
                break
        if fd:
            if cur["text"].strip():
                secs.append(cur)
            cur = {"name": fd, "text": re.sub(r'\[.*?\]', '', l).strip()}
        else:
            cl = re.sub(r'\[(PAUSE|SCENE CHANGE)\]', '', l).strip()
            if cl:
                cur["text"] += " " + cl
    if cur["text"].strip():
        secs.append(cur)
    return [s for s in secs if s["text"].strip()]


def calc_times(secs, dur):
    tw = sum(len(s["text"].split()) for s in secs)
    if tw == 0:
        return []
    ts = []
    c = 0
    for s in secs:
        w = len(s["text"].split())
        ts.append({"name": s["name"], "start": (c / tw) * dur, "duration": (w / tw) * dur, "text": s["text"]})
        c += w
    return ts


def load_fonts(short=False):
    sc = 1.4 if short else 1.0
    try:
        fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(48 * sc))
    except Exception:
        fb = ImageFont.load_default()
    try:
        fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(22 * sc))
    except Exception:
        fs = fb
    try:
        fl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36 * sc))
    except Exception:
        fl = fb
    try:
        fxl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(60 * sc))
    except Exception:
        fxl = fb
    return fb, fs, fl, fxl


def dark_bg(w, h):
    bg = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        f = 1.0 - (y / h) * 0.5
        d.line([(0, y), (w, y)], fill=(int(8 * f), int(8 * f), int(15 * f)))
    return bg


def slide_cinematic(ip, cap, op, w, h, fonts):
    fb, fs, fl, fxl = fonts
    try:
        img = Image.open(ip).convert("RGB").resize((w, h), Image.LANCZOS)
        img = ImageEnhance.Brightness(img).enhance(0.35).filter(ImageFilter.GaussianBlur(2))
    except Exception:
        img = dark_bg(w, h)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 120))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    by = h - 80
    d.rectangle([0, by, w, by + 3], fill=(196, 30, 58))
    if cap:
        lines, cur = [], ""
        for word in cap.split():
            t = cur + " " + word if cur else word
            if d.textlength(t, font=fs) <= w - 60:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        for i, l in enumerate(lines[:2]):
            d.text((30, by + 12 + i * 26), l, font=fs, fill=(200, 200, 210))
    img.save(op, quality=88)


def slide_section(name, op, w, h, fonts, bg_img=None):
    fb, fs, fl, fxl = fonts
    if bg_img:
        try:
            bg = Image.open(bg_img).convert("RGB").resize((w, h), Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(15)).point(lambda p: int(p * 0.15))
        except Exception:
            bg = dark_bg(w, h)
    else:
        bg = dark_bg(w, h)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 160))
    img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0, h // 2 - 45, w, h // 2 - 42], fill=(196, 30, 58))
    bb = d.textbbox((0, 0), name, font=fxl)
    tw = bb[2] - bb[0]
    d.text(((w - tw) // 2, h // 2 - 35), name, font=fxl, fill=(255, 255, 255))
    d.rectangle([0, h // 2 + 30, w, h // 2 + 33], fill=(196, 30, 58))
    img.save(op, quality=88)


def slide_dramatic(text, op, w, h, fonts):
    fb, fs, fl, fxl = fonts
    img = dark_bg(w, h)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 100))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    lines, cur = [], ""
    for word in text.split():
        t = cur + " " + word if cur else word
        if d.textlength(t, font=fl) <= w - 120:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    sy = (h - len(lines) * 48) // 2
    for i, l in enumerate(lines):
        y = sy + i * 48
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            d.text((60 + dx, y + dy), l, font=fl, fill=(0, 0, 0))
        d.text((60, y), l, font=fl, fill=(230, 230, 240))
    img.save(op, quality=88)


def slide_sub(op, w, h, fonts):
    fb, fs, fl, fxl = fonts
    img = dark_bg(w, h)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 140))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0, h // 2 - 3, w, h // 2 + 3], fill=(196, 30, 58))
    t = "SUBSCRIBE"
    bb = d.textbbox((0, 0), t, font=fxl)
    tw = bb[2] - bb[0]
    d.text(((w - tw) // 2, h // 2 + 20), t, font=fxl, fill=(255, 255, 255))
    s = "FOR MORE TRUE CRIME STORIES"
    bb2 = d.textbbox((0, 0), s, font=fs)
    tw2 = bb2[2] - bb2[0]
    d.text(((w - tw2) // 2, h // 2 + 90), s, font=fs, fill=(140, 140, 160))
    img.save(op, quality=88)


def gen_music(dur, op):
    d = int(dur) + 10
    r = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={d}",
        "-f", "lavfi", "-i", f"sine=frequency=82.41:duration={d}",
        "-filter_complex",
        "[0]volume=0.25[a];[1]volume=0.15[b];"
        "[a][b]amix=inputs=2:duration=longest,"
        "aecho=0.8:0.88:60:0.4,lowpass=f=250,volume=0.10",
        "-c:a", "aac", "-b:a", "48k", op
    ], capture_output=True, text=True, timeout=60)
    return os.path.exists(op)


def build_slides(timings, imgs, adur, short):
    slides = []
    w = SHORT_W if short else VIDEO_W
    h = SHORT_H if short else VIDEO_H
    slen = 18.0 if not short else 8.0
    slides.append(("section", "TRUE CRIME", 3.0))
    ii = 0
    for t in timings:
        sd = t["duration"]
        dn = SEC_TITLES.get(t["name"], "")
        if dn:
            slides.append(("section", dn, 4.0))
            sd -= 4.0
        if sd <= 0:
            continue
        rem = sd
        while rem > 2:
            if ii < len(imgs):
                slides.append(("cin", imgs[ii], min(slen, rem)))
                ii += 1
                rem -= min(slen, rem)
            else:
                slides.append(("cin", imgs[ii % max(1, len(imgs))], min(slen, rem)))
                ii += 1
                rem -= min(slen, rem)
    slides.append(("sub", "", 4.0))
    total = sum(s[2] for s in slides)
    if total > 0 and abs(total - adur) > 2:
        ratio = adur / total
        slides = [(s[0], s[1], s[2] * ratio) for s in slides]
    return slides


def render_video(imgs, ap, srt, op, short=False):
    w = SHORT_W if short else VIDEO_W
    h = SHORT_H if short else VIDEO_H
    adur = get_dur(ap)
    fonts = load_fonts(short)
    os.makedirs(TEMP, exist_ok=True)
    lc = os.environ.get("LANG_CODE", "en")
    kind = "short" if short else "long"
    sp = os.path.join(OUT, "scripts", f"{kind}_{lc}.txt")
    script = open(sp, "r", encoding="utf-8").read() if os.path.exists(sp) else ""
    if script:
        secs = parse_sections(script)
        timings = calc_times(secs, adur)
        print(f"    {len(secs)} sections")
    else:
        timings = [{"name": "MAIN", "start": 0, "duration": adur, "text": ""}]
    slides = build_slides(timings, imgs, adur, short)
    print(f"    {len(slides)} slides")
    print(f"    Rendering slides...")
    spaths = []
    for i, (st, data, dur) in enumerate(slides):
        s = os.path.join(TEMP, f"s_{i:04d}.jpg")
        try:
            if st == "cin":
                cap = ""
                if isinstance(data, str) and os.path.exists(data):
                    cap = os.path.basename(data).replace(".jpg", "").replace("_", " ").title()[:60]
                slide_cinematic(data, cap, s, w, h, fonts)
            elif st == "section":
                slide_section(data, s, w, h, fonts, random.choice(imgs) if imgs else None)
            elif st == "sub":
                slide_sub(s, w, h, fonts)
            else:
                dark_bg(w, h).save(s, quality=88)
            spaths.append(s)
        except Exception:
            dark_bg(w, h).save(s, quality=88)
            spaths.append(s)
    cl = os.path.join(TEMP, "slides.txt")
    with open(cl, "w") as f:
        for i, (_, _, dur) in enumerate(slides):
            f.write(f"file '{spaths[i]}'\nduration {dur:.3f}\n")
        f.write(f"file '{spaths[-1]}'\n")
    mp = os.path.join(TEMP, "music.mp3")
    hm = gen_music(adur, mp)
    inputs = ["-f", "concat", "-safe", "0", "-i", cl, "-i", ap]
    if hm:
        inputs += ["-i", mp]
    fs = 18 if short else 22
    esc = srt.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")
    if hm:
        fc = (f"[0:v]fps=8,format=yuv420p,subtitles='{esc}':force_style="
              f"'FontSize={fs},PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
              f"BackColour=&H80000000,Outline=2,Shadow=1,MarginV=35'[v];"
              f"[1:a][2:a]amix=inputs=2:duration=first:weights=1 0.3[a]")
    else:
        fc = (f"[0:v]fps=8,format=yuv420p,subtitles='{esc}':force_style="
              f"'FontSize={fs},PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
              f"BackColour=&H80000000,Outline=2,Shadow=1,MarginV=35'[v];"
              f"[1:a]acopy[a]")
    cmd = (["ffmpeg", "-y"] + inputs +
           ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", "-pix_fmt", "yuv420p", op])
    print(f"    Encoding...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"    Subtitle burn failed, trying without subs...")
        cmd2 = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", cl, "-i", ap,
                 "-map", "0:v", "-map", "1:a",
                 "-c:v", CODEC, "-preset", "ultrafast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "192k",
                 "-shortest", "-movflags", "+faststart", "-pix_fmt", "yuv420p", op]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
        if r2.returncode != 0:
            raise Exception(f"Encode failed: {r2.stderr[:200]}")
    if os.path.exists(op):
        print(f"    Video: {os.path.getsize(op) / (1024 * 1024):.1f}MB ({adur:.0f}s)")
    else:
        raise Exception("No video file created")


def make_thumb(title, imgs, op, short=False):
    w = SHORT_W if short else 1280
    h = SHORT_H if short else 720
    bg = dark_bg(w, h)
    if imgs:
        try:
            b = Image.open(random.choice(imgs)).convert("RGB").resize((w, h), Image.LANCZOS)
            b = b.filter(ImageFilter.GaussianBlur(12)).point(lambda p: int(p * 0.2))
            ov = Image.new("RGBA", (w, h), (0, 0, 0, 150))
            bg = Image.alpha_composite(b.convert("RGBA"), ov).convert("RGB")
        except Exception:
            pass
    d = ImageDraw.Draw(bg)
    by = (h // 2 - 3) if not short else (h * 2 // 3)
    d.rectangle([0, by, w, by + 5], fill=(196, 30, 58))
    fonts = load_fonts(short)
    fb = fonts[0]
    lines, cur = [], ""
    for word in title.split():
        t = cur + " " + word if cur else word
        if d.textlength(t, font=fb) <= w - 80:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    sy = (by - len(lines) * 64) // 2
    for i, l in enumerate(lines):
        y = sy + i * 64
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            d.text((40 + dx, y + dy), l, font=fb, fill=(0, 0, 0))
        d.text((40, y), l, font=fb, fill=(255, 255, 255))
    d.text((40, by + 22), "TRUE CRIME", font=fonts[1], fill=(196, 30, 58))
    bg.save(op, quality=95)


def process(lc, short=False):
    info = LANGUAGES[lc]
    kind = "short" if short else "long"
    sp = os.path.join(OUT, "scripts", f"{kind}_{lc}.txt")
    if not os.path.exists(sp):
        print("  SKIP: no script")
        return None
    raw = open(sp, "r", encoding="utf-8").read()
    clean = clean_text(raw)
    if len(re.sub(r'[^\w]', '', clean)) < 20:
        print("  SKIP: text too short")
        return None
    print(f"Processing {info['name']} {kind} ({len(clean.split())} words)...")
    ap = os.path.join(OUT, f"audio_{kind}_{lc}.mp3")
    vp = os.path.join(OUT, f"subs_{kind}_{lc}.vtt")
    ok = asyncio.run(gen_tts(clean, lc, kind, ap, vp))
    if not ok or not os.path.exists(ap) or os.path.getsize(ap) < 1000:
        print("  FAIL: TTS")
        return None
    srt = vtt_to_srt(vp)
    ai = sorted([os.path.join(IMGS, f) for f in os.listdir(IMGS) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    if not ai:
        print("  FAIL: no images")
        return None
    ni = IMAGES_PER_SHORT if short else min(30, IMAGES_PER_VIDEO)
    imgs = random.sample(ai, min(ni, len(ai)))
    vp2 = os.path.join(OUT, f"video_{kind}_{lc}.mp4")
    try:
        render_video(imgs, ap, srt, vp2, short)
    except Exception as e:
        print(f"  FAIL: {e}")
        return None
    if not os.path.exists(vp2):
        return None
    tp = os.path.join(OUT, f"thumb_{kind}_{lc}.jpg")
    try:
        make_thumb(f"{info['name']} Crime Story", imgs, tp, short)
    except Exception:
        pass
    return {"video": vp2, "thumbnail": tp, "lang": lc, "kind": kind}


def main():
    lc = os.environ.get("LANG_CODE", "en")
    iss = os.environ.get("VIDEO_TYPE", "long") == "short"
    r = process(lc, iss)
    if r:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump(r, f)
        print(f"\nDone: {lc} {'short' if iss else 'long'}")
    else:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump({"skip": True}, f)
        print(f"\nSkipped: {lc} {'short' if iss else 'long'}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
