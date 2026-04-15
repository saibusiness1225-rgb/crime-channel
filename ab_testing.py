"""
A/B Title Testing - OPTIMIZED
- Tests alternative titles to optimize CTR
- Uses config.ANALYTICS (FIXED - was undefined)
- Uses config.AB_TEST_WAIT_HOURS (FIXED - was undefined)
- Smarter testing logic with engagement metrics
"""
import os, json, datetime, time
import google.oauth2.credentials
import googleapiclient.discovery
import requests as http_req
from config import *


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


def get_video_stats(yt, video_id):
    """Get current video statistics."""
    try:
        result = yt.videos().list(
            part="statistics",
            id=video_id
        ).execute()
        if result.get("items"):
            stats = result["items"][0].get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            return {
                "views": views,
                "likes": likes,
                "ctr": (likes / max(1, views)) * 100,
            }
    except Exception as e:
        print(f"  Stats error: {str(e)[:50]}")
    return None


def update_video_title(yt, video_id, new_title):
    """Update video title for A/B testing."""
    try:
        result = yt.videos().list(
            part="snippet,status",
            id=video_id
        ).execute()

        if not result.get("items"):
            return False

        video = result["items"][0]
        snippet = video["snippet"]
        snippet["title"] = new_title[:100]

        yt.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": snippet,
                "status": video["status"]
            }
        ).execute()

        return True
    except Exception as e:
        print(f"  Title update failed: {str(e)[:60]}")
        return False


def log_ab_test(video_id, original_title, new_title, views_before, result):
    """Log A/B test result."""
    os.makedirs(ANALYTICS, exist_ok=True)
    log_file = os.path.join(ANALYTICS, "ab_tests.jsonl")
    entry = {
        "video_id": video_id,
        "original_title": original_title,
        "new_title": new_title,
        "views_before": views_before,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "result": result,
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_ab_tests(yt):
    """Run A/B tests on videos that have alternative titles."""
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")
    ab_log = os.path.join(ANALYTICS, "ab_tests.jsonl")

    os.makedirs(ANALYTICS, exist_ok=True)

    if not os.path.exists(log_file):
        print("No uploads to test")
        return

    # Load uploads with alternative titles that haven't been tested
    tested_ids = set()
    if os.path.exists(ab_log):
        with open(ab_log, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        tested_ids.add(json.loads(line)["video_id"])
                    except Exception:
                        pass

    uploads = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if u.get("title_b") and u["video_id"] not in tested_ids:
                    uploads.append(u)

    if not uploads:
        print("No videos to A/B test")
        return

    # Check if enough time has passed for testing (using config value)
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=AB_TEST_WAIT_HOURS)

    tests_run = 0

    for upload in uploads:
        vid = upload["video_id"]
        title_a = upload["title"]
        title_b = upload["title_b"]
        uploaded_at_str = upload.get("uploaded_at", "")

        if not uploaded_at_str:
            continue

        try:
            uploaded_at = datetime.datetime.fromisoformat(uploaded_at_str.rstrip("Z"))
        except Exception:
            continue

        # Wait before testing
        if uploaded_at > cutoff:
            print(f"  Skipping {vid[:8]} - too recent (need {AB_TEST_WAIT_HOURS}h)")
            continue

        # Get current stats
        stats = get_video_stats(yt, vid)
        if not stats:
            continue

        views_before = stats["views"]

        # Only test videos with at least some views
        if views_before < 10:
            print(f"  Skipping {vid[:8]} - only {views_before} views")
            continue

        # Only test if title_b is different from current title
        if title_a == title_b:
            continue

        print(f"\n  Testing: {vid[:8]}...")
        print(f"    Title A: {title_a}")
        print(f"    Title B: {title_b}")
        print(f"    Views: {views_before}")

        # Update to title B
        if update_video_title(yt, vid, title_b[:100]):
            log_ab_test(vid, title_a, title_b, views_before, "switched_to_b")
            print(f"    Switched to Title B")
            tests_run += 1
        else:
            log_ab_test(vid, title_a, title_b, views_before, "failed")

        # Rate limit
        time.sleep(5)

        # Max 3 tests per run
        if tests_run >= 3:
            break

    print(f"\nA/B tests run: {tests_run}")


def analyze_ab_results():
    """Analyze past A/B test results."""
    ab_log = os.path.join(ANALYTICS, "ab_tests.jsonl")
    stats_log = os.path.join(ANALYTICS, "stats.jsonl")

    if not os.path.exists(ab_log):
        return

    # Load A/B tests
    tests = []
    with open(ab_log, "r") as f:
        for line in f:
            if line.strip():
                try:
                    tests.append(json.loads(line))
                except Exception:
                    pass

    if not tests:
        return

    # Load stats if available
    all_stats = {}
    if os.path.exists(stats_log):
        with open(stats_log, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        s = json.loads(line)
                        vid = s["video_id"]
                        if vid not in all_stats:
                            all_stats[vid] = []
                        all_stats[vid].append(s)
                    except Exception:
                        pass

    # Analyze results
    results = []
    for test in tests:
        vid = test["video_id"]
        views_before = test["views_before"]

        if vid in all_stats:
            after_stats = [s for s in all_stats[vid]
                          if datetime.datetime.fromisoformat(s["timestamp"].rstrip("Z")) >
                          datetime.datetime.fromisoformat(test["timestamp"].rstrip("Z"))]

            if after_stats:
                views_after = after_stats[-1]["views"]
                view_change = views_after - views_before
                pct_change = (view_change / max(1, views_before)) * 100

                results.append({
                    "video_id": vid,
                    "title_a": test["original_title"],
                    "title_b": test["new_title"],
                    "views_before": views_before,
                    "views_after": views_after,
                    "change": view_change,
                    "pct_change": pct_change,
                    "winner": "B" if pct_change > 5 else ("A" if pct_change < -5 else "tie")
                })

    if results:
        print("\nA/B Test Results:")
        print("-" * 60)
        for r in results:
            print(f"  {r['video_id'][:8]}: {r['pct_change']:+.1f}% -> Winner: {r['winner']}")

        # Save report
        os.makedirs(ANALYTICS, exist_ok=True)
        report_file = os.path.join(ANALYTICS, "ab_results.txt")
        with open(report_file, "w") as f:
            f.write("A/B TEST RESULTS SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            for r in sorted(results, key=lambda x: -x["pct_change"]):
                f.write(f"Video: {r['video_id']}\n")
                f.write(f"  Title A: {r['title_a']}\n")
                f.write(f"  Title B: {r['title_b']}\n")
                f.write(f"  Views Before: {r['views_before']}\n")
                f.write(f"  Views After: {r['views_after']}\n")
                f.write(f"  Change: {r['pct_change']:+.1f}%\n")
                f.write(f"  Winner: {r['winner']}\n\n")


def main():
    print("Running A/B title testing...")
    yt = get_yt_service()

    # Run new tests
    run_ab_tests(yt)

    # Analyze past results
    analyze_ab_results()

    print("\nA/B testing complete")



if __name__ == "__main__":
    main()
