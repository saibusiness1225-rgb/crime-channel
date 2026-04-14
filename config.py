import os

# ============================================================
# LANGUAGE CONFIGURATION
# ============================================================
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

# ============================================================
# VIDEO QUALITY SETTINGS (OPTIMIZED)
# ============================================================
VIDEO_W, VIDEO_H = 1920, 1080        # UPGRADED: 720p -> 1080p
SHORT_W, SHORT_H = 1080, 1920
FPS = 30                               # UPGRADED: 8fps -> 30fps (no choppiness)
CODEC = "libx264"
PRESET = "medium"                      # UPGRADED: ultrafast -> medium (better quality)
CRF = 20                               # UPGRADED: 23 -> 20 (higher visual quality)

# ============================================================
# IMAGE SETTINGS
# ============================================================
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
IMAGES_PER_VIDEO = 50                  # UPGRADED: 40 -> 50 (more visual variety)
IMAGES_PER_SHORT = 8                   # UPGRADED: 5 -> 8

# ============================================================
# YOUTUBE SETTINGS
# ============================================================
YT_CATEGORY = "24"                     # Entertainment
LANGS_PER_RUN = 3

# ============================================================
# SCHEDULING SETTINGS (NEW - AUTO POST TIMING)
# ============================================================
# Videos will be scheduled to publish at these times (UTC)
# The system picks the NEXT available slot from this list
PUBLISH_SCHEDULE_UTC = [
    "09:00",   # 9 AM UTC = 2:30 PM IST (India afternoon)
    "14:00",   # 2 PM UTC = 7:30 PM IST (India prime time)
    "18:00",   # 6 PM UTC = 11:30 PM IST (India late night)
    "11:00",   # 11 AM UTC = 4:30 PM IST
    "16:00",   # 4 PM UTC = 9:30 PM IST
]

# Minimum hours from now to schedule a video (YouTube requires at least 2hrs in advance)
SCHEDULE_MIN_HOURS_AHEAD = 3

# Auto-publish: If True, videos are scheduled automatically. If False, uploaded as private.
AUTO_PUBLISH = True

# ============================================================
# SEO OPTIMIZATION SETTINGS (NEW)
# ============================================================
# Maximum tags YouTube allows is 500 chars total. We use 30 max for optimal CTR.
MAX_TAGS = 30
TAG_STRATEGY = "hybrid"  # "broad" | "niche" | "hybrid" (broad + niche mix)

# SEO keyword templates per language
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
        "niche":":["apraadh ki kahani", "suljhe apraadh", "rahasya", "investigation hindi"],
        "trending": ["truecrime", "mystery", "apraadh"],
    },
}

# Hashtag groups for descriptions (rotated per video for freshness)
HASHTAG_GROUPS = {
    "en": [
        ["#TrueCrime", "#Mystery", "#Documentary", "#Crime", "#Unsolved", "#ColdCase", "#Investigation", "#TrueCrimeDocumentary", "#DarkHistory", "#CrimeStory"],
        ["#TrueCrimeCommunity", "#UnsolvedMystery", "#CrimeDocumentary", "#ColdCaseFiles", "#DarkMystery", "#MurderMystery", "#TrueCrimeStories", "#RealCrime"],
        ["#CriminalPsychology", "#ForensicInvestigation", "#ColdCaseSolved", "#TrueCrimeTube", "#MysterySolved", "#CrimeInvestigation", "#DarkDocumentary"],
    ],
    "es": [
        ["#CrimenReal", "#Misterio", "#Documental", "#Crimen", "#SinResolver", "#CasoFrio", "#Investigacion"],
        ["#Crimen", "#MisterioSinResolver", "#DocumentalCrimen", "#HistoriaOscura", "#AsesinoSerial"],
    ],
    "hi": [
        ["#TrueCrime", "#Mystery", "#Apraadh", "#Rahasya", "#Documentary", "#Crime", "#Investigation"],
    ],
    "default": [
        ["#TrueCrime", "#Mystery", "#Documentary", "#Crime", "#Unsolved", "#Investigation"],
    ],
}

# ============================================================
# THUMBNAIL OPTIMIZATION (NEW)
# ============================================================
THUMB_WIDTH = 1280
THUMB_HEIGHT = 720
THUMB_QUALITY = 98                     # UPGRADED: 88 -> 98
THUMB_STYLE = "cinematic"              # "cinematic" | "dramatic" | "minimal"
THUMB_FONT_COLOR = (255, 255, 0)       # Yellow for maximum CTR
THUMB_ACCENT_COLOR = (196, 30, 58)     # Crime red
THUMB_GLOW_EFFECT = True               # Add text glow for thumbnails
THUMB_EMOTION_WORDS = ["SHOCKING", "UNSEEN", "EXPOSED", "HIDDEN", "DARK", "CHILLING", "TERRIFYING"]

# ============================================================
# ENGAGEMENT SETTINGS
# ============================================================
AB_TEST_WAIT_HOURS = 24                 # Wait 24hrs before A/B testing titles
COMMENT_REPLY_MIN_HOURS = 2             # Wait 2hrs before replying to comments
MAX_COMMENT_REPLIES_PER_RUN = 20        # Safety limit
COMMENT_REPLY_DELAY_SECONDS = 3         # Rate limit between replies

# ============================================================
# PATH CONFIGURATION
# ============================================================
WORK = os.environ.get("GITHUB_WORKSPACE", "/tmp/crime")
OUT  = os.path.join(WORK, "output")
IMGS = os.path.join(WORK, "images")
TEMP = os.path.join(WORK, "temp")
ANALYTICS = os.path.join(WORK, "analytics")   # FIX: Previously undefined!

# ============================================================
# API KEYS
# ============================================================
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "")
YT_CLIENT_ID  = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SEC = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH    = os.environ.get("YT_REFRESH_TOKEN", "")

# ============================================================
# CASE CATEGORIES
# ============================================================
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

# ============================================================
# VIDEO ENCODING QUALITY (NO BLACK SCREENS)
# ============================================================
# Minimum acceptable slide duration (prevents flickering/black frames)
MIN_SLIDE_DURATION = 3.0               # UPGRADED: was 2.0
# Fallback image color (dark navy, NOT pure black)
FALLBACK_BG_COLOR = (10, 10, 25)       # UPGRADED: was (8,8,15) nearly black
# Ensure every slide has visual content - never blank
NEVER_BLANK_SLIDES = True
