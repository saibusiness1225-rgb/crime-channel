import os, json, time
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.http
from config import *

def get_access_token():
    data = {
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SEC,
        "refresh_token": YT_REFRESH,
        "grant_type": "refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    import requests
    r = requests.post("https://oauth2.googleapis.com/token", data=data)
    if r.status_code != 200:
        raise Exception(f"Token error: {r.text}")
    return r.json()["access_token"]

def upload_video(video_path, thumb_path, title, description, tags, lang_code, is_short=False):
    token = get_access_token()
    creds = google.oauth2.credentials.Credentials(token)
    yt = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
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

    print(f"  Uploading: {title[:60]}...")
    req = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )

    response = None
    while response is None:
        _, response = req.next_chunk()
        if response:
            print(f"  Upload complete! Video ID: {response['id']}")

            if thumb_path and os.path.exists(thumb_path):
                try:
                    yt.thumbnails().set(videoId=response["id"], media_body=googleapiclient.http.MediaFileUpload(thumb_path)).execute()
                    print(f"  Thumbnail set!")
                except Exception as e:
                    print(f"  Thumbnail failed: {e}")

            return response["id"]
    return None

def main():
    result_file = os.path.join(OUT, "result.json")
    meta_file = os.path.join(OUT, "metadata", "all.json")
    lang_code = os.environ.get("LANG_CODE", "en")
    is_short = os.environ.get("VIDEO_TYPE", "long") == "short"

    with open(result_file) as f:
        result = json.load(f)
    with open(meta_file) as f:
        all_meta = json.load(f)

    meta = all_meta.get(lang_code, {}).get("short" if is_short else "long", {})
    video_id = upload_video(
        result["video"], result["thumbnail"],
        meta.get("title", "True Crime Mystery"),
        meta.get("description", ""),
        meta.get("tags", ["true crime"]),
        lang_code, is_short
    )
    print(f"\nDone! Video ID: {video_id}")

if __name__ == "__main__":
    main()
