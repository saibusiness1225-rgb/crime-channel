# Crime Channel - YouTube Automation (v2)

All-in-one automated true crime YouTube channel. One file does everything.

## Files

| File | Purpose |
|------|---------|
| `agent.py` | ALL automation logic (scripts, images, video, upload, comments, A/B, analytics, cleanup) |
| `config.py` | All configuration (languages, SEO, quality, API keys) |
| `requirements.txt` | Python dependencies |
| `.github/workflows/auto.yml` | GitHub Actions workflow (4 daily runs) |

## Commands

```bash
python agent.py prepare    # Generate scripts + metadata
python agent.py download   # Download images from Pexels
python agent.py build      # Build video (set LANG_CODE + VIDEO_TYPE env)
python agent.py upload     # Upload to YouTube (set LANG_CODE + VIDEO_TYPE env)
python agent.py comment    # Auto-reply to comments
python agent.py abtest     # A/B title testing
python agent.py analytics  # Track video performance
python agent.py cleanup    # Delete bad videos from channel
python agent.py full       # Run full pipeline
```

## Setup

### 1. GitHub Secrets

Add these in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `PEXELS_API_KEY` | Pexels API key |
| `YT_CLIENT_ID` | YouTube OAuth2 client ID |
| `YT_CLIENT_SECRET` | YouTube OAuth2 client secret |
| `YT_REFRESH_TOKEN` | YouTube OAuth2 refresh token |

### 2. YouTube OAuth2 Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable YouTube Data API v3
3. Create OAuth2 credentials (Desktop app)
4. Get refresh token via OAuth2 playground

### 3. Customize

Edit `config.py`:

```python
# Posting schedule (UTC)
PUBLISH_SCHEDULE_UTC = ["09:00", "14:00", "18:00", "11:00"]

# Video quality
FPS = 30; CRF = 20; PRESET = "medium"

# Languages per run
LANGS_PER_RUN = 3
```

### 4. Run

Automatic 4x daily, or manual: **Actions tab → Crime Auto → Run workflow**

## Features

- **30 FPS / 1080p** video with cinematic slides
- **AI scripts** with offline template fallback
- **Multi-language** support (8 languages)
- **Shorts pipeline** for algorithmic push
- **SEO-optimized** titles, tags, descriptions, hashtags
- **CTR-optimized** thumbnails with glow effects
- **Auto comment replies** with Gemini AI
- **A/B title testing** for view optimization
- **Analytics tracking** with performance reports
- **Channel cleanup** for bad videos
- **No black screens** - rich dark backgrounds always
