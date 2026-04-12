import os, json
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.http
import requests as http_req
from config import *


def get_token():
    """Fixed: Removed token_uri from data dict"""
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
    """Get YouTube service with fresh token."""
    t = get_token()
    c = google.oauth2.credentials.Credentials(t)
    return googleapiclient.discovery.build("youtube", "v3", credentials=c)


def find_or_create_playlist(yt, lang_code, lang_name):
    """Find existing playlist for language or create new one."""
    playlist_title = f"True Crime - {lang_name}"
    
    # Search for existing playlist
    try:
        playlists = yt.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        ).execute()
        
        for pl in playlists.get("items", []):
            if pl["snippet"]["title"] == playlist_title:
                print(f"  Found existing playlist: {playlist_title}")
                return pl["id"]
    except Exception as e:
        print(f"  Playlist search warning: {str(e)[:60]}")
    
    # Create new playlist
    try:
        result = yt.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_title,
                    "description": f"True crime documentaries in {lang_name}. New cases added regularly.",
                    "defaultLanguage": LANGUAGES[lang_code]["yt"]
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
        ).execute()
        print(f"  Created playlist: {playlist_title}")
        return result["id"]
    except Exception as e:
        print(f"  Playlist creation failed (non-fatal): {str(e)[:60]}")
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
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        print(f"  Added to playlist")
        return True
    except Exception as e:
        print(f"  Playlist add failed (non-fatal): {str(e)[:60]}")
        return False


def post_comment(yt, video_id, text):
    """Post a pinned comment on the video."""
    if not text:
        return False
    try:
        resource = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": text
                    }
                }
            }
        }
        result = yt.commentThreads().insert(
            part="snippet", body=resource
        ).execute()
        print(f"  Pinned comment posted")
        return True
    except Exception as e:
        err = str(e)
        if "comments" in err.lower() and "disabled" in err.lower():
            print(f"  Comments disabled on video")
        else:
            print(f"  Comment failed (non-fatal): {err[:80]}")
        print(f"  MANUALLY POST THIS COMMENT:")
        print(f"  >>> {text}")
        return False


def upload(vp, tp, title, desc, tags, lc, short=False, pinned_comment=""):
    """Upload video with playlist support."""
    yt = get_yt_service()
    
    # Clean title
    ct = title.replace('<', '').replace('>', '').replace('&', 'and')[:100]
    
    # Build description with timestamps for long videos
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
        full_desc = timestamps + "\n" + desc
    
    # Add hashtags if missing
    if "#" not in full_desc:
        hashtags = "\n\n#TrueCrime #Mystery #Documentary #Crime #Unsolved"
        if not short:
            hashtags += " #ColdCase #Investigation"
        full_desc += hashtags
    
    body = {
        "snippet": {
            "title": ct,
            "description": full_desc,
            "tags": tags[:15] if tags else ["true crime", "mystery", "documentary"],
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
    
    # Upload with retry
    max_retries = 3
    for attempt in range(max_retries):
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
            if attempt < max_retries - 1 and "quota" in str(e).lower():
                print(f"  Upload retry {attempt + 1}/{max_retries}...")
                import time
                time.sleep(60)
                yt = get_yt_service()  # Refresh token
            else:
                raise
    else:
        raise Exception("Upload failed after retries")

    # Set thumbnail
    if tp and os.path.exists(tp):
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=googleapiclient.http.MediaFileUpload(tp)
            ).execute()
            print(f"  Thumbnail set")
        except Exception as e:
            print(f"  Thumbnail failed (non-fatal): {str(e)[:60]}")

    # Add to playlist (for long videos only)
    if not short:
        playlist_id = find_or_create_playlist(yt, lc, LANGUAGES[lc]["name"])
        add_to_playlist(yt, playlist_id, vid)

    # Post pinned comment
    post_comment(yt, vid, pinned_comment)

    return vid


def main():
    rf = os.path.join(OUT, "result.json")
    mf = os.path.join(OUT, "metadata", "all.json")
    lc = os.environ.get("LANG_CODE", "en")
    short = os.environ.get("VIDEO_TYPE", "long") == "short"

    if not os.path.exists(rf):
        print("SKIP: no result file")
        raise SystemExit(1)
        
    with open(rf) as f:
        r = json.load(f)
        
    if r.get("skip"):
        print(f"SKIP: {lc} was skipped in build")
        raise SystemExit(1)
        
    with open(mf) as f:
        am = json.load(f)
        
    m = am.get(lc, {}).get("short" if short else "long", {})
    if not m:
        print(f"SKIP: no metadata for {lc} {'short' if short else 'long'}")
        raise SystemExit(1)

    try:
        vid = upload(
            r["video"], 
            r["thumbnail"],
            m.get("title", "True Crime Mystery"),
            m.get("description", ""),
            m.get("tags", ["true crime"]),
            lc, 
            short,
            m.get("pinned_comment", "")
        )
        print(f"\n✅ SUCCESS: https://youtube.com/watch?v={vid}")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
