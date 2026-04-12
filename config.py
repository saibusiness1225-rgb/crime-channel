import os

LANGUAGES = {
    "en": {"name": "English",    "voice": "en-US-GuyNeural",      "short_voice": "en-US-AriaNeural",      "yt": "en"},
    "es": {"name": "Spanish",    "voice": "es-ES-AlvaroNeural",    "short_voice": "es-ES-ElviraNeural",    "yt": "es"},
    "hi": {"name": "Hindi",      "voice": "hi-IN-MadhurNeural",    "short_voice": "hi-IN-SwaraNeural",    "yt": "hi"},
    "fr": {"name": "French",     "voice": "fr-FR-HenriNeural",     "short_voice": "fr-FR-DeniseNeural",    "yt": "fr"},
    "pt": {"name": "Portuguese", "voice": "pt-BR-AntonioNeural",   "short_voice": "pt-BR-FranciscaNeural", "yt": "pt-BR"},
    "de": {"name": "German",     "voice": "de-DE-ConradNeural",    "short_voice": "de-DE-KatjaNeural",    "yt": "de"},
    "ja": {"name": "Japanese",   "voice": "ja-JP-KeitaNeural",     "short_voice": "ja-JP-NanamiNeural",    "yt": "ja"},
    "ar": {"name": "Arabic",     "voice": "ar-SA-HamedNeural",     "short_voice": "ar-SA-LailaNeural",    "yt": "ar"},
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
]
IMAGES_PER_VIDEO = 40
IMAGES_PER_SHORT = 5

YT_CATEGORY = "24"
LANGS_PER_RUN = 3

WORK = os.environ.get("GITHUB_WORKSPACE", "/tmp/crime")
OUT  = os.path.join(WORK, "output")
IMGS = os.path.join(WORK, "images")
TEMP = os.path.join(WORK, "temp")


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
]
