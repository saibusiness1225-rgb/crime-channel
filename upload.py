import os, json
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
        "token_uri": "https://oauth2.googleapis.com/token"
    })
    if r.status_code != 200:
        raise Exception(f"Token error: {r.text}")
    return r.json()["access_token"]


def post_comment(yt, video_id, text):
    """Post a comment on the video."""
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
        print(f"  Comment posted: {text[:60]}...")
        return True
    except Exception as e:
        print(f"  Comment failed (non-fatal): {str(e)[:80]}")
        print(f"  MANUALLY POST THIS COMMENT:")
        print(f"  >>> {text}")
        return False


def upload(vp, tp, title, desc, tags, lc, short=False, pinned_comment=""):
    t = get_token()
    c = google.oauth2.credentials.Credentials(t)
    yt = googleapiclient.discovery.build("youtube", "v3", credentials=c)

    ct = title.replace('<', '').replace('>', '').replace('&', 'and')[:100]

    body = {
        "snippet": {
            "title": ct,
            "description": desc,
            "tags": tags[:15],
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
    req = yt.videos().insert(
        part="snippet,status", body=body,
        media_body=googleapiclient.http.MediaFileUpload(vp, chunksize=-1, resumable=True))
    res = None
    while res is None:
        _, res = req.next_chunk()
    vid = res["id"]
    print(f"  Video ID: {vid}")

    if tp and os.path.exists(tp):
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=googleapiclient.http.MediaFileUpload(tp)).execute()
            print(f"  Thumbnail set")
        except Exception:
            pass

    # Post pinned comment
    if pinned_comment:
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
        print("SKIP: no metadata")
        raise SystemExit(1)

    try:
        vid = upload(
            r["video"], r["thumbnail"],
            m.get("title", "True Crime"),
            m.get("description", ""),
            m.get("tags", ["true crime"]),
            lc, short,
            m.get("pinned_comment", "")
        )
        print(f"\nDone: {vid}")
    except Exception as e:
        print(f"\nUpload failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
