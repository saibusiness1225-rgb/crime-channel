import os, json, random, subprocess, asyncio, re
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import *

async def generate_tts(text, voice, audio_path, sub_path):
    clean = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '.', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    comm = edge_tts.Communicate(clean, voice)
    submaker = edge_tts.SubMaker()
    with open(audio_path, "wb") as af:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                af.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    with open(sub_path, "w", encoding="utf-8") as sf:
        sf.write(submaker.generate_subs())

def vtt_to_srt(vtt_path):
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("WEBVTT", "").strip()
    content = re.sub(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})',
                     lambda m: f"{m.group(1)}:{m.group(2)}:{m.group(3)},{m.group(4)}", content)
    srt_path = vtt_path.replace(".vtt", ".srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(content)
    return srt_path

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())

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

        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img_path,
               "-vf", vf, "-t", str(seg_dur),
               "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF), clip_path]
        subprocess.run(cmd, capture_output=True, check=True)
        clip_files.append(clip_path)
        if (i + 1) % 10 == 0:
            print(f"  Rendered {i+1}/{n} clips")

    concat_list = os.path.join(TEMP, "concat.txt")
    with open(concat_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")

    concat_out = os.path.join(TEMP, "merged.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", concat_list, "-c", "copy", concat_out],
                   capture_output=True, check=True)

    font_size = 14 if is_short else 18
    escaped_srt = srt_path.replace("'", "'\\''").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", concat_out, "-i", audio_path,
        "-vf", f"subtitles='{escaped_srt}':force_style="
               f"'FontSize={font_size},PrimaryColour=&H00FFFFFF,"
               f"OutlineColour=&H40000000,BackColour=&H40000000,"
               f"Outline=2,Shadow=1,MarginV=30'",
        "-c:v", CODEC, "-preset", PRESET, "-crf", str(CRF),
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  Video done: {os.path.basename(output_path)}")

def create_thumbnail(title, images, output_path, is_short=False):
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

    bar_y = (h // 2 - 3) if not is_short else (h * 2 // 3)
    draw.rectangle([0, bar_y, w, bar_y + 4], fill=(196, 30, 58))

    try:
        fs = 52 if not is_short else 48
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_big = ImageFont.load_default()
        font_sm = font_big

    def wrap(text, font, max_w):
        words = text.split()
        lines, cur = [], ""
        for word in words:
            test = cur + " " + word if cur else word
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = word
        if cur: lines.append(cur)
        return lines

    max_w = w - 80
    lines = wrap(title, font_big, max_w)
    total_h = len(lines) * 60
    start_y = (bar_y - total_h) // 2 if not is_short else (bar_y - total_h - 40) // 2

    for i, line in enumerate(lines):
        y = start_y + i * 60
        for dx, dy, fill in [(-2,-2,(0,0,0)), (2,-2,(0,0,0)), (-2,2,(0,0,0)), (2,2,(0,0,0))]:
            draw.text((40+dx, y+dy), line, font=font_big, fill=fill)
        draw.text((40, y), line, font=font_big, fill=(255, 255, 255))

    draw.text((40, bar_y + 20), "TRUE CRIME", font=font_sm, fill=(196, 30, 58))
    img.save(output_path, quality=95)
    print(f"  Thumbnail done: {os.path.basename(output_path)}")

def process_language(lang_code, is_short=False):
    info = LANGUAGES[lang_code]
    kind = "short" if is_short else "long"
    script_path = os.path.join(OUT, "scripts", f"{kind}_{lang_code}.txt")

    if not os.path.exists(script_path):
        print(f"  Skipping {lang_code} {kind} — no script")
        return None

    print(f"Processing {info['name']} {kind}...")
    voice = info["short_voice"] if is_short else info["voice"]

    audio_path = os.path.join(OUT, f"audio_{kind}_{lang_code}.mp3")
    vtt_path = os.path.join(OUT, f"subs_{kind}_{lang_code}.vtt")

    asyncio.run(generate_tts(open(script_path).read(), voice, audio_path, vtt_path))
    srt_path = vtt_to_srt(vtt_path)

    all_imgs = sorted([os.path.join(IMGS, f) for f in os.listdir(IMGS) if f.endswith(('.jpg','.png'))])
    n_imgs = IMAGES_PER_SHORT if is_short else IMAGES_PER_VIDEO
    imgs = random.sample(all_imgs, min(n_imgs, len(all_imgs)))

    video_path = os.path.join(OUT, f"video_{kind}_{lang_code}.mp4")
    render_video(imgs, audio_path, srt_path, video_path, is_short)

    thumb_path = os.path.join(OUT, f"thumb_{kind}_{lang_code}.jpg")
    create_thumbnail(f"{info['name']} Crime", imgs, thumb_path, is_short)

    return {"video": video_path, "thumbnail": thumb_path, "lang": lang_code, "kind": kind}

def main():
    lang_code = os.environ.get("LANG_CODE", "en")
    is_short = os.environ.get("VIDEO_TYPE", "long") == "short"
    result = process_language(lang_code, is_short)
    if result:
        with open(os.path.join(OUT, "result.json"), "w") as f:
            json.dump(result, f)
        print(f"\nFinished: {lang_code} {'short' if is_short else 'long'}")

if __name__ == "__main__":
    main()
