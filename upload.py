import os, json
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.http
import requests as http_requests
from config import *

def get_access_token():
    data = {
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SEC,
        "refresh_token": YT_REFRESH,
        "grant_type": "refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    r = http_requests.post("https://oauth2.googleapis.com/token", data=data)
    if r.status_code != 200:
        raise Exception(f"Token error: {r.text}")
    return r.json()["access_token"]

def upload_video(video_path, thumb_path, title, description, tags, lang_code, is_short=False):
    token = get_access_token()
    creds = google.oauth2.credentials.Credentials(token)
    yt = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    # Clean title — remove any characters YouTube rejects
    clean_title = title.replace('<', '').replace('>', '').replace('&', 'and')
    if len(clean_title) > 100:
        clean_title = clean_title[:97] + "..."

    body = {
        "snippet": {
            "title": clean_title,
            "description": description,
            "tags": tags[:15],  # YouTube max 15 tags
            "categoryId": YT_CATEGORY,
            "defaultLanguage": LANGUAGES[lang_code]["yt"],
            "defaultAudioLanguage": LANGUAGES[lang_code]["yt"],
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
        }
    }

    print(f"  Uploading: {clean_title[:60]}...")
    req = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )

    response = None
    while response is None:
        _, response = req.next_chunk()

    video_id = response["id"]
    print(f"  Uploaded! Video ID: {video_id}")

    if thumb_path and os.path.exists(thumb_path):
        try:
            yt.thumbnails().set(
                videoId=video_id,
                media_body=googleapiclient.http.MediaFileUpload(thumb_path)
            ).execute()
            print(f"  Thumbnail set!")
        except Exception as e:
            print(f"  Thumbnail failed (non-fatal): {str(e)[:80]}")

    return video_id

def main():
    result_file = os.path.join(OUT, "result.json")
    meta_file = os.path.join(OUT, "metadata", "all.json")
    lang_code = os.environ.get("LANG_CODE", "en")
    is_short = os.environ.get("VIDEO_TYPE", "long") == "short"

    # Check if this video was skipped
    if not os.path.exists(result_file):
        print("SKIP: No result file found")
        return
    with open(result_file) as f:
        result = json.load(f)
    if result.get("skip"):
        print(f"SKIP: {lang_code} {'short' if is_short else 'long'} was skipped in build step")
        return

    # Load metadata
    with open(meta_file) as f:
        all_meta = json.load(f)

    meta = all_meta.get(lang_code, {}).get("short" if is_short else "long", {})
    if not meta:
        print(f"SKIP: No metadata for {lang_code} {'short' if is_short else 'long'}")
        return

    try:
        video_id = upload_video(
            result["video"], result["thumbnail"],
            meta.get("title", "True Crime Mystery"),
            meta.get("description", ""),
            meta.get("tags", ["true crime"]),
            lang_code, is_short
        )
        print(f"\nDone! Video ID: {video_id}")
    except Exception as e:
        print(f"\nUpload failed: {e}")
        print("This is non-fatal — other language uploads will continue.")

if __name__ == "__main__":
    main()
