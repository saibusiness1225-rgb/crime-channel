import os

# ═══════════════════════════════════════════════════════════════
# LANGUAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════
# VIDEO QUALITY
# ═══════════════════════════════════════════════════════════════
VIDEO_W, VIDEO_H = 1920, 1080
SHORT_W, SHORT_H = 1080, 1920
FPS = 30
CODEC = "libx264"
PRESET = "medium"
CRF = 20

# ═══════════════════════════════════════════════════════════════
# IMAGE SETTINGS
# ═══════════════════════════════════════════════════════════════
PEXELS_QUERIES = [
    "dark city night", "police investigation", "crime scene tape",
    "dark alley", "noir street", "mystery fog", "courthouse",
    "evidence board", "detective", "urban night rain",
    "abandoned building", "prison", "forensic",
    "police car night", "dark forest", "cctv camera",
    "newspaper clippings", "shadow figure", "fingerprint",
    "crime investigation dark", "murder mystery dark room",
    "interrogation room", "police badge dark", "blood spatter dark",
    "wanted poster", "cold case evidence", "surveillance monitor",
]
IMAGES_PER_VIDEO = 50
IMAGES_PER_SHORT = 8

# ═══════════════════════════════════════════════════════════════
# YOUTUBE SETTINGS
# ═══════════════════════════════════════════════════════════════
YT_CATEGORY = "24"  # Entertainment
LANGS_PER_RUN = 3

# ═══════════════════════════════════════════════════════════════
# SCHEDULING
# ═══════════════════════════════════════════════════════════════
PUBLISH_SCHEDULE_UTC = ["09:00", "14:00", "18:00", "11:00", "16:00"]
SCHEDULE_MIN_HOURS_AHEAD = 3
AUTO_PUBLISH = True

# ═══════════════════════════════════════════════════════════════
# SEO OPTIMIZATION
# ═══════════════════════════════════════════════════════════════
MAX_TAGS = 30
TAG_STRATEGY = "hybrid"

SEO_KEYWORDS = {
    "en": {
        "broad": ["true crime", "crime documentary", "mystery", "unsolved", "cold case",
                   "crime story", "investigation", "serial killer", "murder mystery", "documentary"],
        "niche": ["unsolved disappearances", "cold case files", "true crime stories",
                  "crime investigation documentary", "unsolved mysteries", "real crime stories",
                  "dark history", "criminal psychology", "forensic investigation", "cold case solved"],
        "trending": ["truecrime", "mysterysolved", "crimedocumentary", "coldcase",
                     "unsolvedmystery", "truecrimecommunity", "darkmystery"],
    },
    "es": {
        "broad": ["crimen real", "documental crimen", "misterio", "sin resolver", "caso frio",
                   "historia criminal", "investigacion", "asesino serial", "misterio asesinato"],
        "niche": ["desapariciones sin resolver", "casos sin resolver", "crimenes reales",
                  "documental investigacion", "misterios sin resolver", "historia oscura"],
        "trending": ["crimenreal", "misterio", "documental", "casofrio"],
    },
    "hi": {
        "broad": ["true crime hindi", "crime documentary hindi", "mystery hindi", "apraadh", "jahed"],
        "niche": ["apraadh ki kahani", "suljhe apraadh", "rahasya", "investigation hindi"],
        "trending": ["truecrime", "mystery", "apraadh"],
    },
}

HASHTAG_GROUPS = {
    "en": [
        ["#TrueCrime", "#Mystery", "#Documentary", "#Crime", "#Unsolved", "#ColdCase", "#Investigation"],
        ["#TrueCrimeCommunity", "#UnsolvedMystery", "#CrimeDocumentary", "#ColdCaseFiles", "#DarkMystery"],
        ["#CriminalPsychology", "#ForensicInvestigation", "#ColdCaseSolved", "#TrueCrimeTube", "#MysterySolved"],
    ],
    "es": [
        ["#CrimenReal", "#Misterio", "#Documental", "#Crimen", "#SinResolver", "#CasoFrio"],
        ["#Crimen", "#MisterioSinResolver", "#DocumentalCrimen", "#HistoriaOscura"],
    ],
    "hi": [
        ["#TrueCrime", "#Mystery", "#Apraadh", "#Rahasya", "#Documentary", "#Crime"],
    ],
    "default": [
        ["#TrueCrime", "#Mystery", "#Documentary", "#Crime", "#Unsolved", "#Investigation"],
    ],
}

# ═══════════════════════════════════════════════════════════════
# THUMBNAIL
# ═══════════════════════════════════════════════════════════════
THUMB_WIDTH = 1280
THUMB_HEIGHT = 720
THUMB_QUALITY = 98
THUMB_STYLE = "cinematic"
THUMB_FONT_COLOR = (255, 255, 0)       # Yellow = highest CTR
THUMB_ACCENT_COLOR = (196, 30, 58)     # Crime red
THUMB_GLOW_EFFECT = True
THUMB_EMOTION_WORDS = ["SHOCKING", "UNSEEN", "EXPOSED", "HIDDEN", "DARK", "CHILLING", "TERRIFYING"]

# ═══════════════════════════════════════════════════════════════
# ENGAGEMENT
# ═══════════════════════════════════════════════════════════════
AB_TEST_WAIT_HOURS = 24
COMMENT_REPLY_MIN_HOURS = 2
MAX_COMMENT_REPLIES_PER_RUN = 20
COMMENT_REPLY_DELAY_SECONDS = 3

# ═══════════════════════════════════════════════════════════════
# GROWTH STRATEGY
# ═══════════════════════════════════════════════════════════════
SHORTS_PER_LONG = 1
SHORT_COMMENT_BAIT = True
CROSS_PROMOTE_SHORTS = True
ADD_END_SCREEN = True
POST_COMMUNITY_POLL = True

# ═══════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════
WORK = os.environ.get("GITHUB_WORKSPACE", "/tmp/crime")
OUT  = os.path.join(WORK, "output")
IMGS = os.path.join(WORK, "images")
TEMP = os.path.join(WORK, "temp")
ANALYTICS = os.path.join(WORK, "analytics")

# ═══════════════════════════════════════════════════════════════
# API KEYS
# ═══════════════════════════════════════════════════════════════
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "")
YT_CLIENT_ID  = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SEC = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH    = os.environ.get("YT_REFRESH_TOKEN", "")

# ═══════════════════════════════════════════════════════════════
# CASE CATEGORIES
# ═══════════════════════════════════════════════════════════════
CASE_CATEGORIES = [
    "unsolved disappearances", "notorious serial killers",
    "mysterious deaths", "famous heists",
    "cold case murders", "infamous kidnappings",
    "bizarre crime mysteries", "historic criminal cases",
    "wrongful convictions", "missing persons mysteries",
    "crime scene investigation failures", "botched investigations",
    "cult crimes", "financial crimes and fraud",
    "political assassinations", "organized crime syndicates",
]

# ═══════════════════════════════════════════════════════════════
# VIDEO ENCODING
# ═══════════════════════════════════════════════════════════════
MIN_SLIDE_DURATION = 3.0
FALLBACK_BG_COLOR = (10, 10, 25)
NEVER_BLANK_SLIDES = True
