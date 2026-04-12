import os, json, datetime
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.http
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
        raise Exception(f"Token error: {r.status_code}: {r.text}")
    return r.json()["access_token"]


def get_yt_service():
    t = get_token()
    c = google.oauth2.credentials.Credentials(t)
    return googleapiclient.discovery.build("youtube", "v3", credentials=c)


def find_or_create_playlist(yt, lang_code, lang_name, short=False):
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
        print(f"  Playlist search warning: {str(e)[:60]}")
    
    try:
        result = yt.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_title,
                    "description": f"{'Short clips' if short else 'Full documentaries'} in {lang_name}.",
                    "defaultLanguage": LANGUAGES[lang_code]["yt"]
                },
                "status": {"privacyStatus": "public"}
            }
        ).execute()
        print(f"  Created playlist: {playlist_title}")
        return result["id"]
    except Exception as e:
        print(f"  Playlist creation failed: {str(e)[:60]}")
        return None


def add_to_playlist(yt, playlist_id, video_id):
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
        print(f"  Playlist add failed: {str(e)[:60]}")
        return False


def post_comment(yt, video_id, text):
    if not text:
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
        print(f"  >>> POST MANUALLY: {text}")
        return False


def log_upload(video_id, lang_code, video_type, title, title_b=""):
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
        "ab_tested": False,
        "views_at_upload": 0,
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"  Logged: {video_id}")


def upload(vp, tp, title, desc, tags, lc, short=False, pinned_comment="", title_b=""):
    yt = get_yt_service()
    
    ct = title.replace('<', '').replace('>', '').replace('&', 'and')[:100]
    
    # Add timestamps if missing
    full_desc = desc
    if not short and "0:00" not in desc:
        timestamps = """
0:00 - Intro
1:30 - Background  
4:30 - The Crime
9:30 - The Investigation
13:30 - The Suspects
16:30 - The Resolution
18:30 - Conclusion

"""
        full_desc = timestamps + desc
    
    if "#" not in full_desc:
        hashtags = "\n\n#TrueCrime #Mystery #Documentary #Crime #Unsolved"
        if not short:
            hashtags += " #ColdCase #Investigation #TrueCrimeDocumentary"
        full_desc += hashtags
    
    body = {
        "snippet": {
            "title": ct,
            "description": full_desc,
            "tags": tags[:15] if tags else ["true crime", "mystery"],
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
    
    for attempt in range(3):
        try:
            req = yt.videos().insert(
                part="snippet,status",
                body=body,
                media_body=googleapiclient.http.MediaFileUpload(vp, chunksize=-1, resumable=True)
            )
            res = None
            while res is None:
                _, res = req.next_chunk()
            vid = res["id"]
            print(f"  Video ID: {vid}")
            break
        except Exception as e:
            if attempt < 2 and ("quota" in str(e).lower() or "5" in str(e)[:10]):
                print(f"  Retry {attempt + 1}/3...")
                import time
                time.sleep(60)
                yt = get_yt_service()
            else:
                raise

    # Thumbnail
    if tp and os.path.exists(tp):
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=googleapiclient.http.MediaFileUpload(tp)
            ).execute()
            print(f"  Thumbnail set")
        except Exception as e:
            print(f"  Thumbnail warning: {str(e)[:60]}")

    # Playlist
    playlist_id = find_or_create_playlist(yt, lc, LANGUAGES[lc]["name"], short)
    add_to_playlist(yt, playlist_id, vid)

    # Pinned comment
    post_comment(yt, vid, pinned_comment)

    # Log for analytics
    log_upload(vid, lc, "short" if short else "long", ct, title_b)

    return vid


def main():
    rf = os.path.join(OUT, "result.json")
    mf = os.path.join(OUT, "metadata", "all.json")
    lc = os.environ.get("LANG_CODE", "en")
    short = os.environ.get("VIDEO_TYPE", "long") == "short"

    if not os.path.exists(rf):
        print("SKIP: no result file")
        import sys
        sys.exit(0) # <--- CHANGE THIS from raise SystemExit(1)
        
    with open(rf) as f:
        r = json.load(f)
        
    if r.get("skip"):
        print(f"SKIP: {lc} was skipped in build")
        import sys
        sys.exit(0) # <--- CHANGE THIS from raise SystemExit(1)
        
    # ... rest of the upload code ...
        
    with open(mf) as f:
        am = json.load(f)
        
    m = am.get(lc, {}).get("short" if short else "long", {})
    if not m:
        print(f"SKIP: no metadata for {lc}")
        raise SystemExit(1)

    try:
        vid = upload(
            r["video"], r["thumbnail"],
            m.get("title", "True Crime Mystery"),
            m.get("description", ""),
            m.get("tags", ["true crime"]),
            lc, short,
            m.get("pinned_comment", ""),
            m.get("title_b", "")  # For A/B testing
        )
        print(f"\n✅ https://youtube.com/watch?v={vid}")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
