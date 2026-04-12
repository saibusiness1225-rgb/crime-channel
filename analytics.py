"""
Analytics Tracker - Logs video performance for optimization
"""
import os, json, datetime, time
import google.oauth2.credentials
import googleapiclient.discovery
import requests as http_req
from config import *


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


def get_video_stats(yt, video_id):
    """Get statistics for a video."""
    try:
        result = yt.videos().list(
            part="statistics,snippet",
            id=video_id
        ).execute()
        
        if result.get("items"):
            item = result["items"][0]
            stats = item.get("statistics", {})
            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "title": item["snippet"].get("title", ""),
            }
    except Exception as e:
        print(f"  Stats error for {video_id}: {str(e)[:50]}")
    return None


def update_analytics(yt):
    """Update analytics for all tracked videos."""
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")
    stats_file = os.path.join(ANALYTICS, "stats.jsonl")
    
    if not os.path.exists(log_file):
        print("No uploads to track")
        return
    
    os.makedirs(ANALYTICS, exist_ok=True)
    
    # Load existing uploads
    uploads = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                uploads.append(json.loads(line))
    
    if not uploads:
        print("No uploads to track")
        return
    
    # Get stats for each video
    now = datetime.datetime.utcnow().isoformat()
    new_stats = []
    
    for upload in uploads:
        vid = upload["video_id"]
        stats = get_video_stats(yt, vid)
        
        if stats:
            entry = {
                "video_id": vid,
                "timestamp": now,
                "views": stats["views"],
                "likes": stats["likes"],
                "comments": stats["comments"],
                "title": stats["title"],
                "lang": upload["lang"],
                "type": upload["type"],
            }
            new_stats.append(entry)
            print(f"  {vid[:8]}... {stats['views']:>6} views | {stats['likes']:>4} likes | {upload['lang']}")
    
    # Append to stats log
    if new_stats:
        with open(stats_file, "a") as f:
            for entry in new_stats:
                f.write(json.dumps(entry) + "\n")
    
    # Generate summary report
    generate_report(new_stats)


def generate_report(stats):
    """Generate a summary report."""
    report_file = os.path.join(ANALYTICS, "report.txt")
    
    if not stats:
        return
    
    total_views = sum(s["views"] for s in stats)
    total_likes = sum(s["likes"] for s in stats)
    avg_views = total_views / len(stats)
    
    # Views by language
    lang_views = {}
    for s in stats:
        lang = s["lang"]
        lang_views[lang] = lang_views.get(lang, 0) + s["views"]
    
    # Views by type
    type_views = {"long": 0, "short": 0}
    type_count = {"long": 0, "short": 0}
    for s in stats:
        type_views[s["type"]] = type_views.get(s["type"], 0) + s["views"]
        type_count[s["type"]] = type_count.get(s["type"], 0) + 1
    
    with open(report_file, "w") as f:
        f.write(f"YOUTUBE ANALYTICS REPORT\n")
        f.write(f"Generated: {datetime.datetime.utcnow().isoformat()}\n")
        f.write(f"{'=' * 50}\n\n")
        
        f.write(f"TOTALS:\n")
        f.write(f"  Videos tracked: {len(stats)}\n")
        f.write(f"  Total views: {total_views:,}\n")
        f.write(f"  Total likes: {total_likes:,}\n")
        f.write(f"  Avg views/video: {avg_views:,.1f}\n\n")
        
        f.write(f"BY TYPE:\n")
        for t in ["long", "short"]:
            avg = type_views[t] / max(1, type_count[t])
            f.write(f"  {t}: {type_views[t]:,} views ({type_count[t]} videos, {avg:,.0f} avg)\n")
        f.write("\n")
        
        f.write(f"BY LANGUAGE:\n")
        for lang, views in sorted(lang_views.items(), key=lambda x: -x[1]):
            f.write(f"  {lang}: {views:,} views\n")
    
    print(f"\n📊 Report saved to analytics/report.txt")


def main():
    print("📊 Running analytics...")
    yt = get_yt_service()
    update_analytics(yt)
    print("Analytics complete")


if __name__ == "__main__":
    main()
