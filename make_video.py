import os, json, random, subprocess, asyncio, re
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import *

# ─── VALIDATED VOICE FALLBACKS ──────────────────────────────
# Each language has multiple fallback voices.
# If the primary voice fails, it tries the next one automatically.
VOICE_FALLBACKS = {
    "en": {
        "long":  ["en-US-GuyNeural", "en-US-DavisNeural", "en-US-JaredNeural", "en-US-AndrewNeural"],
        "short": ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-MichelleNeural"]
    },
    "es": {
        "long":  ["es-ES-AlvaroNeural", "es-ES-SergioNeural", "es-MX-JorgeNeural"],
        "short": ["es-ES-ElviraNeural", "es-ES-LuciaNeural", "es-MX-DaliaNeural"]
    },
    "hi": {
        "long":  ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
        "short": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"]
    },
    "fr": {
        "long":  ["fr-FR-HenriNeural", "fr-FR-BrigitteNeural", "fr-CA-AntoineNeural"],
        "short": ["fr-FR-DeniseNeural", "fr-FR-LucieNeural", "fr-CA-SylvieNeural"]
    },
    "pt": {
        "long":  ["pt-BR-AntonioNeural", "pt-BR-RicardoNeural"],
        "short": ["pt-BR-FranciscaNeural", "pt-BR-LeticiaNeural"]
    },
    "de": {
        "long":  ["de-DE-ConradNeural", "de-DE-AmalaNeural"],
        "short": ["de-DE-KatjaNeural", "de-DE-GiselaNeural"]
    },
    "ja": {
        "long":  ["ja-JP-KeitaNeural", "ja-JP-NaokiNeural"],
        "short": ["ja-JP-NanamiNeural", "ja-JP-MizukiNeural"]
    },
    "ar": {
        "long":  ["ar-SA-NaayfNeural", "ar-SA-HazemNeural", "ar-AE-FatimaNeural"],
        "short": ["ar-SA-LailaNeural", "ar-SA-AmalNeural", "ar-AE-MaryamNeural"]
    },
}

def get_voice(lang_code, kind):
    """Get the first available voice from the fallback list."""
    kind_key = "short" if kind == "short" else "long"
    voices = VOICE_FALLBACKS.get(lang_code, VOICE_FALLBACKS["en"]).get(kind_key, [])
    if not voices:
        voices = VOICE_FALLBACKS["en"][kind_key]
    return voices[0]


# ─── TTS + SUBTITLE GENERATION ──────────────────────────────

async def try_tts_voice(text, voice, audio_path, sub_path):
    """Try a single voice. Returns True on success."""
    comm = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    got_audio = False

    with open(audio_path, "wb") as af:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                af.write(chunk["data"])
                got_audio = True
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub(
                    (chunk["offset"], chunk["duration"]),
                    chunk["text"]
                )

    if got_audio:
        with open(sub_path, "w", encoding="utf-8") as sf:
            sf.write(submaker.generate_subs())
        return True

    # Clean up failed audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)
    return False

async def generate_tts(text, lang_code, kind, audio_path, sub_path):
    """Generate TTS with voice fallback. Tries multiple voices until one works."""
    kind_key = "short" if kind == "short" else "long"
    voices = VOICE_FALLBACKS.get(lang_code, VOICE_FALLBACKS["en"]).get(kind_key, [])

    if not voices:
        print(f"    WARNING: No voices found for {lang_code}/{kind_key}, using English")
        voices = VOICE_FALLBACKS["en"][kind_key]

    for i, voice in enumerate(voices):
        print(f"    Trying voice: {voice}")
        try:
            success = await try_tts_voice(text, voice, audio_path, sub_path)
            if success:
                print(f"    Voice OK: {voice}")
                return True
            else:
                print(f"    No audio from {voice}, trying next...")
        except Exception as e:
            print(f"    Voice {voice} failed: {str(e)[:80]}")
            if os.path.exists(audio_path):
                os.remove(audio_path)

    print(f"    ERROR: All {len(voices)} voices failed for {lang_code}/{kind_key}")
    return False

def clean_tts_text(text):
    """Remove markers from script text, validate it has actual content."""
    clean = re.sub(
        r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]',
        '.', text
    )
    clean = re.sub(r'\s+', ' ', clean).strip()
    # Remove lines that are just dots/punctuation from marker replacement
    clean = re.sub(r'(\.\s*){3,}', '. ', clean)
    clean = clean.strip('. ')
    return clean

def vtt_to_srt(vtt_path):
    """Convert WebVTT to SRT format."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("WEBVTT", "").strip()
    # Fix timestamp format: HH:MM:SS.mmm → HH:MM:SS,mmm
    content = re.sub(
        r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})',
        lambda m: f"{m.group(1)}:{m.group(2)}:{m.group(3)},{m.group(4)}",
        content
    )
    # Remove duplicate timestamps that can appear
    lines = content.split('\n')
    seen = set()
    clean_lines = []
    for line in lines:
        if line.strip() and line.strip() not in seen:
            seen.add(line.strip())
            clean_lines.append(line)
        elif not line.strip():
            clean_lines.append(line)
    content = '\n'.join(clean_lines)
    srt_path = vtt_path.replace(".vtt", ".srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(content)
    return srt_path


# ─── VIDEO RENDERING ────────────────────────────────────────

def get_duration(path):
    """Get audio/video duration in seconds."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except:
        return 60.0  # fallback 60 seconds

def render_video(images, audio_path, srt_path, output_path, is_short=False):
    """
    Render cinematic video with Ken Burns effect, audio, and burned-in subtitles.
    """
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
        zoom_end = random.uniform(1.08, 1.25)
        pan_x = random.uniform(-30, 30)
        pan_y = random.uniform(-30, 30)

        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
            f"zoompan=z='1.0+({zoom_end}-1.0)*on/{frames}'"
            f":x='iw/2-(iw/zoom/2)+{pan_x}*on/{frames}'"
            f":y='ih/2-(ih/zoom/2)+{pan_y}*on/{frames}'"
            f":d={frames}:s={w}x{h}:fps={fps},"
            f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0, seg_dur-0.4)}:d=0.4,"
            f"format=yuv420p"
        )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-vf", vf, "-t", str(seg_dur),
            "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF), clip_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"    WARNING: clip {i} failed: {result.stderr[:100]}")
            # Create a black frame clip as fallback
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"color=c=black:s={w}x{h}:d={seg_dur}:r={fps}",
                "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF), clip_path
            ], capture_output=True, timeout=30)
        clip_files.append(clip_path)
        if (i + 1) % 10 == 0:
            print(f"    Rendered {i+1}/{n} clips")

    # Concatenate all clips
    concat_list = os.path.join(TEMP, "concat.txt")
    with open(concat_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")

    concat_out = os.path.join(TEMP, "merged.mp4")
    result = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", concat_out
    ], capture_output=True, text=True, timeout=60)

    if result.returncode != 0 or not os.path.exists(concat_out):
        # If concat fails, use first clip as the video
        print(f"    WARNING: concat failed, using single clip")
        concat_out = clip_files[0] if clip_files else None
        if not concat_out:
            raise Exception("No video clips generated")

    # Merge audio + burn subtitles
    font_size = 16 if is_short else 20
    # Escape special characters for FFmpeg subtitle filter
    escaped_srt = srt_path.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")

    cmd = [
        "ffmpeg", "-y",
        "-i", concat_out, "-i", audio_path,
        "-vf", f"subtitles='{escaped_srt}':force_style="
               f"'FontSize={font_size},PrimaryColour=&H00FFFFFF,"
               f"OutlineColour=&H80000000,BackColour=&H80000000,"
               f"Outline=2,Shadow=1,MarginV=35'",
        "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF),
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        # Fallback: merge without subtitles if subtitle filter fails
        print(f"    WARNING: subtitle burn failed, merging without subs")
        cmd_no_sub = [
            "ffmpeg", "-y",
            "-i", concat_out, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            output_path
        ]
        subprocess.run(cmd_no_sub, capture_output=True, timeout=300)

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"    Video done: {os.path.basename(output_path)} ({size_mb:.1f} MB)")
    else:
        raise Exception("Video file was not created")


# ─── THUMBNAIL GENERATION ───────────────────────────────────

def create_thumbnail(title, images, output_path, is_short=False):
    """Create cinematic crime thumbnail with dark moody background."""
    w = SHORT_W if is_short else 1280
    h = SHORT_H if is_short else 720

    if images:
        try:
            bg = Image.open(random.choice(images)).convert("RGB")
            bg = bg.resize((w, h), Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(12))
            bg = bg.point(lambda p: int(p * 0.25))
        except:
            bg = Image.new("RGB", (w, h), (10, 10, 18))
    else:
        bg = Image.new("RGB", (w, h), (10, 10, 18))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 140))
    bg_rgba = bg.convert("RGBA")
    bg_rgba = Image.alpha_composite(bg_rgba, overlay)
    img = bg_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Red accent bar
    bar_y = (h // 2 - 3) if not is_short else (h * 2 // 3)
    draw.rectangle([0, bar_y, w, bar_y + 4], fill=(196, 30, 58))

    # Load fonts
    try:
        fs = 52 if not is_short else 48
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_big = ImageFont.load_default()
        font_sm = font_big

    # Text wrapping
    def wrap(text, font, max_w):
        words = text.split()
        lines, cur = [], ""
        for word in words:
            test = cur + " " + word if cur else word
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    max_w = w - 80
    lines = wrap(title, font_big, max_w)
    total_h = len(lines) * 62
    start_y = (bar_y - total_h) // 2 if not is_short else (bar_y - total_h - 40) // 2

    for i, line in enumerate(lines):
        y = start_y + i * 62
        # Text shadow
        for dx, dy, fill in [(-2,-2,(0,0,0)), (2,-2,(0,0,0)), (-2,2,(0,0,0)), (2,2,(0,0,0))]:
            draw.text((40+dx, y+dy), line, font=font_big, fill=fill)
        draw.text((40, y), line, font=font_big, fill=(255, 255, 255))

    draw.text((40, bar_y + 20), "TRUE CRIME", font=font_sm, fill=(196, 30, 58))
    img.save(output_path, quality=95)
    print(f"    Thumbnail done: {os.path.basename(output_path)}")


# ─── MAIN PROCESSOR ─────────────────────────────────────────

def process_language(lang_code, is_short=False):
    info = LANGUAGES[lang_code]
    kind = "short" if is_short else "long"
    script_path = os.path.join(OUT, "scripts", f"{kind}_{lang_code}.txt")

    if not os.path.exists(script_path):
        print(f"  Skipping {lang_code} {kind} — no script file")
        return None

    # Read and validate script
    raw_text = open(script_path, "r", encoding="utf-8").read()
    clean_text = clean_tts_text(raw_text)

    # Check if there's actual speech text left after cleaning
    word_chars = len(re.sub(r'[^\w]', '', clean_text))
    if word_chars < 20:
        print(f"  Skipping {lang_code} {kind} — text too short after cleaning ({word_chars} word chars)")
        return None

    print(f"Processing {info['name']} {kind} ({len(clean_text.split())} words)...")

    # Generate TTS with voice fallback
    audio_path = os.path.join(OUT, f"audio_{kind}_{lang_code}.mp3")
    vtt_path = os.path.join(OUT, f"subs_{kind}_{lang_code}.vtt")

    success = asyncio.run(generate_tts(clean_text, lang_code, kind, audio_path, vtt_path))
    if not success:
        print(f"  FAILED: Could not generate audio for {lang_code} {kind}")
        return None

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
        print(f"  FAILED: Audio file too small or missing for {lang_code} {kind}")
        return None

    # Convert subtitles
    srt_path = vtt_to_srt(vtt_path)

    # Get images
    all_imgs = sorted([
        os.path.join(IMGS, f) for f in os.listdir(IMGS)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
    if not all_imgs:
        print(f"  FAILED: No images found")
        return None

    n_imgs = IMAGES_PER_SHORT if is_short else IMAGES_PER_VIDEO
    imgs = random.sample(all_imgs, min(n_imgs, len(all_imgs)))

    # Render video
    video_path = os.path.join(OUT, f"video_{kind}_{lang_code}.mp4")
    try:
        render_video(imgs, audio_path, srt_path, video_path, is_short)
    except Exception as e:
        print(f"  FAILED: Video render error: {e}")
        return None

    if not os.path.exists(video_path):
        print(f"  FAILED: Video file not created")
        return None

    # Create thumbnail
    thumb_path = os.path.join(OUT, f"thumb_{kind}_{lang_code}.jpg")
    try:
        create_thumbnail(f"{info['name']} Crime Story", imgs, thumb_path, is_short)
    except Exception as e:
        print(f"  WARNING: Thumbnail failed: {e}")
        # Create a simple fallback thumbnail
        try:
            fallback = Image.new("RGB", (1280 if not is_short else 1080, 720 if not is_short else 1920), (10, 10, 18))
            d = ImageDraw.Draw(fallback)
            try:
                fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                fnt = ImageFont.load_default()
            d.text((40, 360 if not is_short else 960), "TRUE CRIME", font=fnt, fill=(196, 30, 58))
            fallback.save(thumb_path, quality=95)
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
        print(f"\nFinished: {lang_code} {'short' if is_short else 'long'}")
    else:
        print(f"\nSkipped: {lang_code} {'short' if is_short else 'short'} — check logs above")
        # Write empty result so upload step knows to skip
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump({"skip": True}, f)

if __name__ == "__main__":
    main()
