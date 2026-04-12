"""
Comment Reply Automation - Engages with viewers to boost algorithm
"""
import os, json, datetime, time, random
import google.oauth2.credentials
import googleapiclient.discovery
import requests as http_req
from config import *


# Engagement-boosting reply templates
REPLY_TEMPLATES = {
    "en": [
        "That's an interesting theory! Have you looked into the {detail}?",
        "I didn't think about it that way. The {detail} is definitely suspicious.",
        "Great observation! A lot of people miss the {detail}.",
        "This case has so many layers. What do you think about {detail}?",
        "You might be onto something there. The {detail} has always bothered me too.",
        "I covered this in the video, but there's actually more to the {detail}...",
        "Interesting point! The family actually said something similar about {detail}.",
    ],
    "es": [
        "¡Buena teoría! ¿Has investigado el {detail}?",
        "No lo había pensado así. El {detail} es definitivamente sospechoso.",
        "¡Gran observación! Mucha gente pasa por alto el {detail}.",
    ],
    "hi": [
        "दिलचस्प थ्योरी! क्या आपने {detail} की जांच की?",
        "मैंने इस तरह से नहीं सोचा था। {detail} निश्चित रूप से संदिग्ध है।",
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
]


def get_token():
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
    t = get_token()
    c = google.oauth2.credentials.Credentials(t)
    return googleapiclient.discovery.build("youtube", "v3", credentials=c)


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


def get_reply_text(lang):
    """Generate a contextual reply."""
    templates = REPLY_TEMPLATES.get(lang, REPLY_TEMPLATES["default"])
    template = random.choice(templates)
    detail = random.choice(CASE_DETAILS)
    return template.format(detail=detail)


def should_reply(comment_snippet, replied_file):
    """Check if we should reply to this comment."""
    # Skip if we already replied to this comment
    comment_id = comment_snippet["parentId"] if "parentId" in comment_snippet else comment_snippet.get("id", "")
    
    if os.path.exists(replied_file):
        with open(replied_file, "r") as f:
            replied = f.read().split("\n")
        if comment_id in replied:
            return False
    
    # Skip very short comments (likely spam)
    text = comment_snippet.get("textOriginal", "")
    if len(text) < 10:
        return False
    
    # Skip if it's from the channel owner
    if comment_snippet.get("authorChannelId", {}).get("value") == "channel_owner":
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


def process_video_comments(yt, video_id, lang, replied_file):
    """Process comments for a single video."""
    comments = get_video_comments(yt, video_id)
    
    if not comments:
        return 0
    
    replied_count = 0
    
    for thread in comments[:10]:  # Max 10 replies per video per run
        snippet = thread["snippet"]["topLevelComment"]["snippet"]
        comment_id = thread["snippet"]["topLevelComment"]["id"]
        
        if not should_reply(snippet, replied_file):
            continue
        
        # Check comment age (don't reply too fast)
        published = snippet.get("publishedAt", "")
        if published:
            try:
                pub_time = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
                age_hours = (datetime.datetime.utcnow() - pub_time).total_seconds() / 3600
                if age_hours < COMMENT_REPLY_MIN_HOURS:
                    continue
            except:
                pass
        
        # Generate and post reply
        reply_text = get_reply_text(lang)
        
        # Add commenter's name for personalization
        author = snippet.get("authorDisplayName", "there")
        if "@" not in reply_text and len(author) < 30:
            reply_text = f"@{author} {reply_text}"
        
        if reply_to_comment(yt, comment_id, reply_text):
            replied_count += 1
            print(f"      Replied: {snippet['textOriginal'][:40]}...")
            
            # Log replied comment
            with open(replied_file, "a") as f:
                f.write(comment_id + "\n")
            
            time.sleep(2)  # Rate limit
    
    return replied_count


def main():
    print("💬 Running comment reply automation...")
    
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
        print(f"  Checking {vid[:8]}... ({lang})")
        
        count = process_video_comments(yt, vid, lang, replied_file)
        total_replied += count
        
        if count > 0:
            print(f"    Replied to {count} comments")
    
    print(f"\n✅ Replied to {total_replied} comments total")


if __name__ == "__main__":
    main()
