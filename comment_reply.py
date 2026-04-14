"""
Comment Reply Automation - FULLY OPTIMIZED
- Gemini AI for contextual, natural replies (not generic templates)
- Engagement-boosting strategies
- Rate limiting and safety
- Multi-language support
- Smart reply timing
"""
import os, json, datetime, time, random
import google.oauth2.credentials
import googleapiclient.discovery
import requests as http_req
from config import *


# Fallback reply templates (used if Gemini is unavailable)
REPLY_TEMPLATES = {
    "en": [
        "That's an interesting theory! Have you looked into the {detail}?",
        "I didn't think about it that way. The {detail} is definitely suspicious.",
        "Great observation! A lot of people miss the {detail}.",
        "This case has so many layers. What do you think about {detail}?",
        "You might be onto something there. The {detail} has always bothered me too.",
        "I covered this in the video, but there's actually more to the {detail}...",
        "Interesting point! The family actually said something similar about {detail}.",
        "The {detail} really is the key to this whole case. Good catch!",
        "Nobody ever talks about the {detail} - thanks for bringing that up!",
        "This is exactly what investigators struggled with regarding {detail}.",
    ],
    "es": [
        "Buena teoria! Has investigado el {detail}?",
        "No lo habia pensado asi. El {detail} es definitivamente sospechoso.",
        "Gran observacion! Mucha gente pasa por alto el {detail}.",
    ],
    "hi": [
        "dilchasp theory! kya aapne {detail} ki jaanch ki?",
        "maine is tarah se nahi socha tha. {detail} nishchit roop se sandigdh hai.",
    ],
    "default": [
        "Interesting theory! What do you think about {detail}?",
        "Great observation! A lot of people miss that detail.",
        "You might be onto something there.",
    ]
}

CASE_DETAILS = [
    "timeline", "evidence", "witness testimony", "motive",
    "alibi", "autopsy report", "police response", "family statements",
    "crime scene photos", "phone records", "surveillance footage",
    "fingerprints", "DNA evidence", "911 call", "neighbor accounts",
]


def get_token():
    """Get fresh OAuth2 access token."""
    r = http_req.post("https://oauth2.googleapis.com/token", data={
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SEC,
        "refresh_token": YT_REFRESH,
        "grant_type": "refresh_token",
    })
    if r.status_code != 200:
        raise Exception(f"Token error: {r.status_code}")
    return r.json()["access_token"]


def get_yt_service():
    """Create authenticated YouTube API service."""
    t = get_token()
    c = google.oauth2.credentials.Credentials(t)
    return googleapiclient.discovery.build("youtube", "v3", credentials=c)


def generate_ai_reply(comment_text, video_title, lang="en"):
    """
    Use Gemini AI to generate a contextual, natural reply.
    Falls back to template-based replies if AI fails.
    """
    if GEMINI_KEY:
        try:
            prompt = f"""You are the host of a true crime YouTube channel called "Archive of Enigmas".
A viewer left this comment on your video "{video_title}":

"{comment_text}"

Write a natural, engaging reply that:
1. Acknowledges their point specifically
2. Adds a small detail or insight they might not know
3. Ends with a question to continue the conversation
4. Sounds human and conversational, NOT robotic
5. Keep it under 200 characters
6. Write in {"English" if lang == "en" else "the language of the comment"}

Reply:"""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 150}
            }
            r = http_req.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                reply = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if len(reply) > 20 and len(reply) <= 250:
                    return reply
        except Exception as e:
            print(f"      AI reply error: {str(e)[:50]}")

    # Fallback to template-based reply
    templates = REPLY_TEMPLATES.get(lang, REPLY_TEMPLATES["default"])
    template = random.choice(templates)
    detail = random.choice(CASE_DETAILS)
    return template.format(detail=detail)


def get_video_comments(yt, video_id, max_results=20):
    """Get comments for a video."""
    try:
        result = yt.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=max_results,
            order="time"
        ).execute()
        return result.get("items", [])
    except Exception as e:
        if "comments" in str(e).lower():
            print(f"    Comments disabled for {video_id[:8]}")
        else:
            print(f"    Comment fetch error: {str(e)[:50]}")
        return []


def should_reply(comment_snippet, replied_file):
    """Check if we should reply to this comment."""
    comment_id = comment_snippet.get("parentId", comment_snippet.get("id", ""))

    if os.path.exists(replied_file):
        with open(replied_file, "r") as f:
            replied = f.read().split("\n")
        if comment_id in replied:
            return False

    # Skip very short comments (likely spam/emoji only)
    text = comment_snippet.get("textOriginal", "")
    if len(text) < 10:
        return False

    # Skip our own comments
    if comment_snippet.get("authorChannelId", {}).get("value") == "channel_owner":
        return False

    # Skip obvious spam patterns
    spam_words = ["subscribe", "sub4sub", "follow me", "check my channel", "free money"]
    if any(word in text.lower() for word in spam_words):
        return False

    return True


def reply_to_comment(yt, comment_id, text):
    """Post a reply to a comment."""
    try:
        result = yt.comments().insert(
            part="snippet",
            body={
                "snippet": {
                    "parentId": comment_id,
                    "textOriginal": text
                }
            }
        ).execute()
        return True
    except Exception as e:
        print(f"      Reply failed: {str(e)[:50]}")
        return False


def process_video_comments(yt, video_id, lang, replied_file, video_title=""):
    """Process comments for a single video."""
    comments = get_video_comments(yt, video_id)

    if not comments:
        return 0

    replied_count = 0

    for thread in comments[:15]:  # Check up to 15 comments
        snippet = thread["snippet"]["topLevelComment"]["snippet"]
        comment_id = thread["snippet"]["topLevelComment"]["id"]

        if not should_reply(snippet, replied_file):
            continue

        # Check comment age (don't reply too fast or too late)
        published = snippet.get("publishedAt", "")
        if published:
            try:
                pub_time = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
                age_hours = (datetime.datetime.utcnow() - pub_time).total_seconds() / 3600
                if age_hours < COMMENT_REPLY_MIN_HOURS:
                    continue
                if age_hours > 168:  # Don't reply to comments older than 7 days
                    continue
            except Exception:
                pass

        # Generate contextual reply
        comment_text = snippet.get("textOriginal", "")
        reply_text = generate_ai_reply(comment_text, video_title, lang)

        # Add personalization
        author = snippet.get("authorDisplayName", "there")
        if "@" not in reply_text and len(author) < 30 and author != "Archive of Enigmas":
            reply_text = f"@{author} {reply_text}"

        # Ensure reply isn't too long for YouTube
        if len(reply_text) > 10000:
            reply_text = reply_text[:9990] + "..."

        if reply_to_comment(yt, comment_id, reply_text):
            replied_count += 1
            print(f"      Replied: {comment_text[:40]}...")

            # Log replied comment
            with open(replied_file, "a") as f:
                f.write(comment_id + "\n")

            time.sleep(COMMENT_REPLY_DELAY_SECONDS)

        # Safety limit
        if replied_count >= MAX_COMMENT_REPLIES_PER_RUN:
            print(f"    Reached max replies per run ({MAX_COMMENT_REPLIES_PER_RUN})")
            break

    return replied_count


def main():
    print("Running comment reply automation...")

    yt = get_yt_service()
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")
    replied_file = os.path.join(ANALYTICS, "replied_comments.txt")

    os.makedirs(ANALYTICS, exist_ok=True)

    if not os.path.exists(log_file):
        print("No uploads to check")
        return

    # Load recent uploads (last 50)
    uploads = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                uploads.append(json.loads(line))

    # Only process uploads from last 7 days
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    recent = [u for u in uploads[-50:] if datetime.datetime.fromisoformat(u["uploaded_at"][:-1]) > cutoff]

    if not recent:
        print("No recent uploads to check")
        return

    total_replied = 0

    for upload in recent:
        vid = upload["video_id"]
        lang = upload["lang"]
        title = upload.get("title", "")
        print(f"  Checking {vid[:8]}... ({lang})")

        count = process_video_comments(yt, vid, lang, replied_file, title)
        total_replied += count

        if count > 0:
            print(f"    Replied to {count} comments")

    print(f"\nReplied to {total_replied} comments total")


if __name__ == "__main__":
    main()
