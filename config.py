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
# VIDEO LENGTH TARGETS
# ═══════════════════════════════════════════════════════════════
TARGET_LONG_WORDS = 3800
MIN_LONG_WORDS = 2500
MAX_LONG_WORDS = 5000

# ═══════════════════════════════════════════════════════════════
# VIDEO QUALITY
# ═══════════════════════════════════════════════════════════════
VIDEO_W, VIDEO_H = 1920, 1080
SHORT_W, SHORT_H = 1080, 1920
FPS = 24
CODEC = "libx264"
PRESET = "ultrafast"
CRF = 28

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
YT_CATEGORY = "24"
LANGS_PER_RUN = 8                    # CHANGED: all 8 languages
BUILD_LANGS = ["en","es","hi","fr","pt","de","ja","ar"]  # CHANGED: all 8

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
                   "historia criminal", "investigacion", "asesino serial", "misterio asesinato", "documental"],
        "niche": ["desapariciones sin resolver", "casos sin resolver", "crimenes reales",
                  "documental investigacion", "misterios sin resolver", "historia oscura",
                  "psicologia criminal", "investigacion forense", "caso resuelto", "archivos criminales"],
        "trending": ["crimenreal", "misterio", "documental", "casofrio", "crimen", "resuelto"],
    },
    "hi": {
        "broad": ["true crime hindi", "crime documentary hindi", "mystery hindi", "apraadh", "jahed",
                   "apraadh ki kahani", "rahasya", "jaanch", "serial killer hindi", "documentary hindi"],
        "niche": ["apraadh ki kahani", "suljhe apraadh", "rahasya", "investigation hindi",
                  "andhe apraadh", "apraadh纪录片", "sachchi apraadh kahani", "forensic jaanch"],
        "trending": ["truecrime", "mystery", "apraadh", "rahasya", "jahed"],
    },
    "fr": {
        "broad": ["true crime francais", "documentaire crime", "mystere", "non resolu", "affaire classée",
                   "histoire criminelle", "enquete", "tueur en serie", "mystere meurtre", "documentaire"],
        "niche": ["disparitions non resolues", "affaires classées", "crimes reels",
                  "documentaire enquete", "mysteres non resolus", "histoire sombre",
                  "psychologie criminelle", "investigation forensique", "affaire resolue", "froids"],
        "trending": ["truecrime", "mystere", "documentaire", "affaireclassée", "crime", "enquete"],
    },
    "pt": {
        "broad": ["true crime portugues", "documentario crime", "misterio", "nao resolvido", "caso frio",
                   "historia criminal", "investigacao", "serial killer", "misterio assassinato", "documentario"],
        "niche": ["desaparecimentos nao resolvidos", "casos nao resolvidos", "crimes reais",
                  "documentario investigacao", "misterios nao resolvidos", "historia sombra",
                  "psicologia criminal", "investigacao forense", "caso resolvido", "arquivos criminais"],
        "trending": ["truecrime", "misterio", "documentario", "casofrio", "crime", "investigacao"],
    },
    "de": {
        "broad": ["true crime deutsch", "verbrechen dokumentation", "mysterium", "ungelöst", "kalt case",
                   "verbrechensgeschichte", "ermittlung", "serienmörder", "mord mysterium", "dokumentation"],
        "niche": ["ungelöste verschwinden", "kalt cases", "wahre verbrechen",
                  "ermittlung dokumentation", "ungelöste mysterien", "dunkle geschichte",
                  "kriminalpsychologie", "forensische untersuchung", "fall gelöst", "verbrechen archiv"],
        "trending": ["truecrime", "mysterium", "dokumentation", "kaltcase", "verbrechen", "ermittlung"],
    },
    "ja": {
        "broad": ["true crime 日本語", "犯罪ドキュメンタリー", "ミステリー", "未解決", "冷たい事件",
                   "犯罪史", "捜査", "連続殺人", "殺人ミステリー", "ドキュメンタリー"],
        "niche": ["未解決失踪", "冷たい事件ファイル", "リアル犯罪",
                  "捜査ドキュメンタリー", "未解決ミステリー", "暗い歴史",
                  "犯罪心理学", "法医学捜査", "解決事件", "犯罪アーカイブ"],
        "trending": ["truecrime", "ミステリー", "ドキュメンタリー", "未解決", "犯罪", "捜査"],
    },
    "ar": {
        "broad": ["true crime عربي", "وثائقي جريمة", "لغز", "غير محلول", "قضية باردة",
                   "قصة جنائية", "تحقيق", "قاتل متسلسل", "لغز جريمة قتل", "وثائقي"],
        "niche": ["اختفاءات غير محلولة", "قضايا باردة", "جرائم حقيقية",
                  "وثائقي تحقيق", "الغاز غير محلولة", "تاريخ مظلم",
                  "علم النفس الجنائي", "التحقيق الجنائي", "قضية محلولة", "ارشيف جنائي"],
        "trending": ["truecrime", "لغز", "وثائقي", "قضيةباردة", "جريمة", "تحقيق"],
    },
}

HASHTAG_GROUPS = {
    "en": [
        ["#TrueCrime", "#Mystery", "#Documentary", "#Crime", "#Unsolved", "#ColdCase", "#Investigation"],
        ["#TrueCrimeCommunity", "#UnsolvedMystery", "#CrimeDocumentary", "#ColdCaseFiles", "#DarkMystery"],
    ],
    "es": [
        ["#CrimenReal", "#Misterio", "#Documental", "#Crimen", "#SinResolver", "#CasoFrio"],
        ["#Crimen", "#MisterioSinResolver", "#DocumentalCrimen", "#HistoriaOscura"],
    ],
    "hi": [
        ["#TrueCrime", "#Mystery", "#Apraadh", "#Rahasya", "#Documentary", "#Crime"],
    ],
    "fr": [
        ["#TrueCrime", "#Mystere", "#Documentaire", "#Crime", "#NonResolu", "#AffaireClassée"],
        ["#Crime", "#MystereNonResolu", "#DocumentaireCrime", "#HistoireSombre"],
    ],
    "pt": [
        ["#TrueCrime", "#Misterio", "#Documentario", "#Crime", "#NaoResolvido", "#CasoFrio"],
        ["#Crime", "#MisterioNaoResolvido", "#DocumentarioCrime", "#HistoriaSombria"],
    ],
    "de": [
        ["#TrueCrime", "#Mysterium", "#Dokumentation", "#Verbrechen", "#Ungeloest", "#KaltCase"],
        ["#Verbrechen", "#MysteriumUngeloest", "#VerbrechenDokumentation", "#DunkleGeschichte"],
    ],
    "ja": [
        ["#TrueCrime", "#ミステリー", "#ドキュメンタリー", "#犯罪", "#未解決", "#捜査"],
    ],
    "ar": [
        ["#TrueCrime", "#لغز", "#وثائقي", "#جريمة", "#غيرمحلول", "#قضيةباردة"],
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
THUMB_FONT_COLOR = (255, 255, 0)
THUMB_ACCENT_COLOR = (196, 30, 58)
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
IMGS = os.path.join(OUT, "images")
TEMP = os.path.join(OUT, "temp")
ANALYTICS = os.path.join(OUT, "analytics")

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
