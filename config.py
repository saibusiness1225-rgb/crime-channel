import os
import datetime

LANGUAGES = {
    "en": {"name": "English",    "voice": "en-US-GuyNeural",      "short_voice": "en-US-AriaNeural",      "yt": "en"},
    "es": {"name": "Spanish",    "voice": "es-ES-AlvaroNeural",    "short_voice": "es-ES-ElviraNeural",    "yt": "es"},
    "hi": {"name": "Hindi",      "voice": "hi-IN-MadhurNeural",    "short_voice": "hi-IN-SwaraNeural",    "yt": "hi"},
    "fr": {"name": "French",     "voice": "fr-FR-HenriNeural",     "short_voice": "fr-FR-DeniseNeural",    "yt": "fr"},
    "pt": {"name": "Portuguese", "voice": "pt-BR-AntonioNeural",   "short_voice": "pt-BR-FranciscaNeural", "yt": "pt-BR"},
    "de": {"name": "German",     "voice": "de-DE-ConradNeural",    "short_voice": "de-DE-KatjaNeural",    "yt": "de"},
    "ja": {"name": "Japanese",   "voice": "ja-JP-KeitaNeural",     "short_voice": "ja-JP-NanamiNeural",    "yt": "ja"},
    "ar": {"name": "Arabic",     "voice": "ar-SA-HamedNeural",     "short_voice": "ar-SA-LailaNeural",    "yt": "ar"},
    "ko": {"name": "Korean",     "voice": "ko-KR-InJoonNeural",    "short_voice": "ko-KR-SunHiNeural",    "yt": "ko"},
    "it": {"name": "Italian",    "voice": "it-IT-DiegoNeural",     "short_voice": "it-IT-ElsaNeural",     "yt": "it"},
}

VIDEO_W, VIDEO_H = 1280, 720
SHORT_W, SHORT_H = 1080, 1920
FPS = 24
CODEC = "libx264"
PRESET = "ultrafast"
CRF = 23

PEXELS_QUERIES = [
    "dark city night", "police investigation", "crime scene tape",
    "dark alley", "noir street", "mystery fog", "courthouse",
    "evidence board", "detective", "urban night rain",
    "abandoned building", "prison", "forensic",
    "police car night", "dark forest", "cctv camera",
    "newspaper clippings", "shadow figure", "fingerprint",
    "interrogation room", "police lights", "crime evidence",
    "dark hallway", "wanted poster", "jail cell",
]
IMAGES_PER_VIDEO = 40
IMAGES_PER_SHORT = 5

YT_CATEGORY = "24"

# INCREASED: 6 languages per run for maximum reach
LANGS_PER_RUN = 6

# SHORTS-ONLY DAYS: Run only Shorts on these days (0=Mon, 6=Sun)
# Monday, Wednesday, Friday = Shorts Only for algorithm boost
SHORTS_ONLY_DAYS = [0, 2, 4]

# A/B TESTING: How many hours before testing variant B
AB_TEST_WAIT_HOURS = 6

# COMMENT REPLY: Min hours before replying (look organic)
COMMENT_REPLY_MIN_HOURS = 2

WORK = os.environ.get("GITHUB_WORKSPACE", "/tmp/crime")
OUT  = os.path.join(WORK, "output")
IMGS = os.path.join(WORK, "images")
TEMP = os.path.join(WORK, "temp")
ANALYTICS = os.path.join(WORK, "analytics")

GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "")
YT_CLIENT_ID  = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SEC = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH    = os.environ.get("YT_REFRESH_TOKEN", "")

CASE_CATEGORIES = [
    "unsolved disappearances", "notorious serial killers",
    "mysterious deaths", "famous heists",
    "cold case murders", "infamous kidnappings",
    "bizarre crime mysteries", "historic criminal cases",
    "wrongful convictions", "missing persons mysteries",
    "unsolved murders", "mysterious vanishings",
    "famous fugitives", "crime of passion cases",
    "locked room mysteries", "medical mysteries deaths",
]


def is_shorts_only_day():
    """Check if today should only produce Shorts."""
    return datetime.datetime.utcnow().weekday() in SHORTS_ONLY_DAYS


def get_run_config():
    """Get today's run configuration."""
    shorts_only = is_shorts_only_day()
    day_name = datetime.datetime.utcnow().strftime("%A")
    return {
        "shorts_only": shorts_only,
        "day_name": day_name,
        "types": ["short"] if shorts_only else ["long", "short"],
    }
