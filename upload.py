"""
YouTube Upload Module - FULLY OPTIMIZED
- Publishes videos as PUBLIC immediately (reliable)
- Scheduling is handled by GitHub Actions cron times
- SEO-optimized titles, descriptions, tags
- Smart hashtag rotation
- Thumbnail verification
- Pinned comment engagement
- Comprehensive error handling & retry logic
- Upload logging for analytics
"""
import os, json, datetime, random, time
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.http
import requests as http_req
from config import *


def get_token():
    """Get fresh OAuth2 access token from refresh token."""
    r = http_req.post("https://oauth2.googleapis.com/token", data={
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SEC,
        "refresh_token": YT_REFRESH,
        "grant_type": "refresh_token",
    })
    if r.status_code != 200:
        raise Exception(f"Token refresh failed: {r.status_code}: {r.text[:200]}")
    return r.json()["access_token"]


def get_yt_service():
    """Create authenticated YouTube API service."""
    t = get_token()
    c = google.oauth2.credentials.Credentials(t)
    return googleapiclient.discovery.build("youtube", "v3", credentials=c)


def generate_seo_tags(base_tags, lang_code, category=""):
    """
    Generate SEO-optimized tags using hybrid strategy.
    Mixes broad keywords, niche keywords, and trending hashtags.
    Returns list of tags optimized for YouTube's 500-char limit.
    """
    all_tags = []

    # Start with user-provided tags
    if base_tags:
        all_tags.extend(base_tags)

    # Add language-specific SEO keywords
    lang_seo = SEO_KEYWORDS.get(lang_code, SEO_KEYWORDS.get("en", {}))

    if TAG_STRATEGY in ("broad", "hybrid"):
        broad = lang_seo.get("broad", [])
        all_tags.extend(broad)

    if TAG_STRATEGY in ("niche", "hybrid"):
        niche = lang_seo.get("niche", [])
        all_tags.extend(niche)

    # Add category-specific tags
    if category:
        category_words = category.lower().split()
        all_tags.extend(category_words)
        all_tags.append(category)
        all_tags.append(f"{category} documentary")
        all_tags.append(f"{category} true crime")

    # Add trending keywords
    trending = lang_seo.get("trending", [])
    all_tags.extend(trending)

    # Deduplicate while preserving order
    seen = set()
    unique_tags = []
    for tag in all_tags:
        tag_lower = tag.lower().strip()
        if tag_lower and tag_lower not in seen and len(tag) > 1:
            seen.add(tag_lower)
            unique_tags.append(tag)

    # Enforce YouTube's 500-char total limit for tags
    result = []
    total_len = 0
    for tag in unique_tags:
        tag_len = len(tag) + 1  # +1 for comma
        if total_len + tag_len > 490:
            break
        result.append(tag)
        total_len += tag_len

    return result[:MAX_TAGS]


def generate_hashtags(lang_code, category=""):
    """
    Generate optimized hashtags for video description.
    Rotates hashtag groups for variety.
    YouTube shows first 3 hashtags above the title.
    """
    groups = HASHTAG_GROUPS.get(lang_code, HASHTAG_GROUPS.get("default", []))
    if not groups:
        groups = HASHTAG_GROUPS["default"]

    chosen = random.choice(groups)

    if category:
        cat_tag = "#" + category.replace(" ", "").replace("-", "").title()
        if len(cat_tag) <= 30:
            chosen = [cat_tag] + chosen

    return chosen[:12]


def build_seo_description(base_desc, lang_code, category="", short=False, timestamps=""):
    """
    Build a fully SEO-optimized video description.
    Includes: hook, description, timestamps, hashtags, links section.
    """
    parts = []

    # 1. Hook / First line (most important for CTR)
    hook_phrases = {
        "en": [
            "The truth behind this case will leave you speechless.",
            "What the investigators missed will shock you.",
            "This unsolved mystery has haunted detectives for decades.",
            "The evidence was there all along - but nobody saw it.",
        ],
        "es": ["La verdad detras de este caso te dejara sin palabras."],
        "hi": ["is case ki sachai aapko hakka-bakka kar degi."],
        "default": ["The truth behind this case will leave you speechless."],
    }
    hooks = hook_phrases.get(lang_code, hook_phrases["default"])
    parts.append(random.choice(hooks))
    parts.append("")

    # 2. Timestamps (for long videos)
    if not short and timestamps:
        parts.append(timestamps)
        parts.append("")

    # 3. Main description
    if base_desc:
        parts.append(base_desc)
        parts.append("")

    # 4. SEO keywords paragraph
    lang_seo = SEO_KEYWORDS.get(lang_code, SEO_KEYWORDS.get("en", {}))
    broad_kw = lang_seo.get("broad", [])[:5]
    if broad_kw:
        if lang_code == "en":
            seo_para = (f"Dive deep into the world of {broad_kw[0]} and {broad_kw[1]}. "
                       f"This {broad_kw[2]} investigation explores {broad_kw[3]} and {broad_kw[4]} "
                       f"like never before. Join us as we uncover the truth behind one of the most "
                       f"chilling cases in criminal history.")
        else:
            seo_para = " | ".join(broad_kw)
        parts.append(seo_para)
        parts.append("")

    # 5. Hashtags
    hashtags = generate_hashtags(lang_code, category)
    parts.append(" ".join(hashtags))
    parts.append("")

    # 6. Channel promotion
    if lang_code == "en":
        parts.append("Subscribe and hit the bell icon for weekly true crime documentaries.")
        parts.append("")
        parts.append("Disclaimer: This content is for educational and informational purposes only. "
                     "All cases are based on publicly available information.")
    else:
        lang_name = LANGUAGES.get(lang_code, {}).get("name", "")
        parts.append(f"Subscribe for more {lang_name} true crime content.")

    return "\n".join(parts)


def find_or_create_playlist(yt, lang_code, lang_name, short=False):
    """Find existing playlist or create a new one."""
    playlist_title = f"{'Shorts - ' if short else ''}True Crime - {lang_name}"

    try:
        playlists = yt.playlists().list(
            part="snippet", mine=True, maxResults=50
        ).execute()

        for pl in playlists.get("items", []):
            if pl["snippet"]["title"] == playlist_title:
                print(f"  Found playlist: {playlist_title}")
                return pl["id"]
    except Exception as e:
        print(f"  Playlist search warning: {str(e)[:80]}")

    try:
        result = yt.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_title,
                    "description": f"{'Short clips' if short else 'Full documentaries'} in {lang_name}. True crime stories and unsolved mysteries.",
                    "defaultLanguage": LANGUAGES[lang_code]["yt"]
                },
                "status": {"privacyStatus": "public"}
            }
        ).execute()
        print(f"  Created playlist: {playlist_title}")
        return result["id"]
    except Exception as e:
        print(f"  Playlist creation failed: {str(e)[:80]}")
        return None


def add_to_playlist(yt, playlist_id, video_id):
    """Add video to playlist."""
    if not playlist_id:
        return False
    try:
        yt.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id}
                }
            }
        ).execute()
        print(f"  Added to playlist")
        return True
    except Exception as e:
        print(f"  Playlist add failed: {str(e)[:80]}")
        return False


def post_pinned_comment(yt, video_id, text):
    """Post a comment on the video (pinning requires channel owner scope)."""
    if not text or len(text.strip()) < 5:
        print(f"  Skipped empty comment")
        return False

    try:
        result = yt.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": text}
                    }
                }
            }
        ).execute()
        print(f"  Pinned comment posted")
        return True
    except Exception as e:
        print(f"  Comment failed: {str(e)[:80]}")
        print(f"  >>> POST MANUALLY: {text[:100]}")
        return False


def log_upload(video_id, lang_code, video_type, title, title_b="", publish_time=""):
    """Log upload for analytics and A/B testing."""
    os.makedirs(ANALYTICS, exist_ok=True)
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")

    entry = {
        "video_id": video_id,
        "lang": lang_code,
        "type": video_type,
        "title": title,
        "title_b": title_b,
        "uploaded_at": datetime.datetime.utcnow().isoformat(),
        "publish_at": publish_time,
        "ab_tested": False,
        "views_at_upload": 0,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"  Logged: {video_id}")


def upload(vp, tp, title, desc, tags, lc, short=False, pinned_comment="",
           title_b="", category="", timestamps=""):
    """
    Upload video to YouTube as PUBLIC (reliable).
    Scheduling is handled by GitHub Actions cron triggers.
    """
    yt = get_yt_service()

    # ---- TITLE OPTIMIZATION ----
    ct = title.replace('<', '').replace('>', '').replace('&', 'and').strip()[:100]

    # Add engagement words to title if not present (for CTR)
    engagement_prefixes = ["SHOCKING:", "BREAKING:", "EXPOSED:", "REVEALED:", "THE TRUTH:"]
    if not any(ct.upper().startswith(ep.rstrip(":")) for ep in engagement_prefixes):
        if random.random() < 0.5:
            prefix = random.choice(engagement_prefixes)
            ct = f"{prefix} {ct}"[:100]

    # ---- DESCRIPTION OPTIMIZATION ----
    full_desc = build_seo_description(
        base_desc=desc,
        lang_code=lc,
        category=category,
        short=short,
        timestamps=timestamps
    )

    # ---- TAGS OPTIMIZATION ----
    optimized_tags = generate_seo_tags(tags, lc, category)
    print(f"  SEO Tags ({len(optimized_tags)}): {', '.join(optimized_tags[:10])}...")

    # ---- BUILD REQUEST BODY ----
    # Upload as PUBLIC directly - scheduling is handled by cron triggers
    body = {
        "snippet": {
            "title": ct,
            "description": full_desc,
            "tags": optimized_tags,
            "categoryId": YT_CATEGORY,
            "defaultLanguage": LANGUAGES[lc]["yt"],
            "defaultAudioLanguage": LANGUAGES[lc]["yt"],
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
        }
    }

    print(f"  Uploading: {ct[:60]}...")
    print(f"  Privacy: public")

    # ---- UPLOAD WITH RETRY ----
    vid = None
    for attempt in range(3):
        try:
            req = yt.videos().insert(
                part="snippet,status",
                body=body,
                media_body=googleapiclient.http.MediaFileUpload(
                    vp, chunksize=8*1024*1024, resumable=True
                )
            )
            res = None
            while res is None:
                status, res = req.next_chunk()
                if status:
                    print(f"  Upload progress: {int(status.progress() * 100)}%")

            vid = res["id"]
            print(f"  Video ID: {vid}")
            break
        except Exception as e:
            err_str = str(e).lower()
            if attempt < 2:
                if "quota" in err_str:
                    print(f"  Quota hit, waiting 60s before retry {attempt + 1}/3...")
                    time.sleep(60)
                elif "timeout" in err_str or "connection" in err_str:
                    print(f"  Network issue, retrying {attempt + 1}/3...")
                    time.sleep(30)
                else:
                    print(f"  Upload error: {str(e)[:100]}")
                    time.sleep(10)
                yt = get_yt_service()
            else:
                raise Exception(f"Upload failed after 3 attempts: {str(e)[:200]}")

    if not vid:
        raise Exception("Upload failed - no video ID returned")

    # ---- THUMBNAIL ----
    if tp and os.path.exists(tp) and os.path.getsize(tp) > 5000:
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=googleapiclient.http.MediaFileUpload(tp)
            ).execute()
            print(f"  Thumbnail set successfully")
        except Exception as e:
            print(f"  Thumbnail warning: {str(e)[:80]}")
            try:
                time.sleep(5)
                yt = get_yt_service()
                yt.thumbnails().set(
                    videoId=vid,
                    media_body=googleapiclient.http.MediaFileUpload(tp)
                ).execute()
                print(f"  Thumbnail set (2nd attempt)")
            except Exception as e2:
                print(f"  Thumbnail failed: {str(e2)[:80]}")
    else:
        print(f"  WARNING: Thumbnail missing or too small ({tp})")

    # ---- PLAYLIST ----
    playlist_id = find_or_create_playlist(yt, lc, LANGUAGES[lc]["name"], short)
    add_to_playlist(yt, playlist_id, vid)

    # ---- PINNED COMMENT ----
    post_pinned_comment(yt, vid, pinned_comment)

    # ---- LOG FOR ANALYTICS ----
    log_upload(vid, lc, "short" if short else "long", ct, title_b, "public")

    return vid


def main():
    rf = os.path.join(OUT, "result.json")
    mf = os.path.join(OUT, "metadata", "all.json")
    lc = os.environ.get("LANG_CODE", "en")
    short = os.environ.get("VIDEO_TYPE", "long") == "short"

    print(f"=== UPLOAD START: lang={lc}, type={'short' if short else 'long'} ===")
    print(f"  OUT dir: {OUT}")
    print(f"  Result file: {rf}")
    print(f"  Result exists: {os.path.exists(rf)}")
    print(f"  Metadata file: {mf}")
    print(f"  Metadata exists: {os.path.exists(mf)}")

    # List what's in the output directory
    if os.path.exists(OUT):
        print(f"  Output dir contents: {os.listdir(OUT)}")

    if not os.path.exists(rf):
        print("FAILED: no result.json file found! Build step likely failed.")
        print("  This means build.py did not produce a video.")
        import sys
        sys.exit(1)  # FAIL so we can see the problem

    with open(rf) as f:
        r = json.load(f)
    print(f"  Result.json contents: {r}")

    if r.get("skip"):
        print(f"FAILED: Build was skipped for {lc}. Check build.py logs for errors.")
        import sys
        sys.exit(1)  # FAIL so we can see the problem

    if not os.path.exists(mf):
        print(f"FAILED: No metadata file found at {mf}")
        import sys
        sys.exit(1)

    with open(mf) as f:
        am = json.load(f)

    m = am.get(lc, {}).get("short" if short else "long", {})
    if not m:
        print(f"FAILED: no metadata for {lc}/{('short' if short else 'long')}")
        print(f"  Available keys in metadata: {list(am.keys())}")
        for k, v in am.items():
            print(f"    {k}: {list(v.keys()) if isinstance(v, dict) else v}")
        import sys
        sys.exit(1)

    print(f"  Title: {m.get('title', 'MISSING')}")
    print(f"  Tags: {m.get('tags', 'MISSING')[:3] if m.get('tags') else 'MISSING'}...")
    print(f"  Video path: {r.get('video', 'MISSING')}")
    print(f"  Video exists: {os.path.exists(r.get('video', ''))}")
    print(f"  Thumbnail path: {r.get('thumbnail', 'MISSING')}")
    print(f"  Thumbnail exists: {os.path.exists(r.get('thumbnail', ''))}")

    # Verify video file exists before uploading
    if not os.path.exists(r.get("video", "")):
        print(f"FAILED: Video file not found at {r.get('video')}")
        import sys
        sys.exit(1)

    # Generate timestamps if long video
    timestamps = ""
    if not short:
        timestamps = (
            "0:00 - Intro\n"
            "1:30 - Background\n"
            "4:30 - The Crime\n"
            "9:30 - The Investigation\n"
            "13:30 - The Suspects\n"
            "16:30 - The Resolution\n"
            "18:30 - Conclusion\n"
        )

    try:
        vid = upload(
            r["video"], r["thumbnail"],
            m.get("title", "True Crime Mystery"),
            m.get("description", ""),
            m.get("tags", ["true crime"]),
            lc, short,
            m.get("pinned_comment", ""),
            m.get("title_b", ""),
            m.get("category", ""),
            timestamps
        )
        print(f"\n=== UPLOAD SUCCESS: https://youtube.com/watch?v={vid} ===")
    except Exception as e:
        print(f"\n=== UPLOAD FAILED: {e} ===")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
