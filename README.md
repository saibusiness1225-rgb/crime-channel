Crime Channel - YouTube Automation (OPTIMIZED)
Automated True Crime YouTube channel with AI-generated scripts, scheduled publishing, SEO optimization, and engagement automation.

What's Fixed & Improved
Critical Bug Fixes
ANALYTICS directory undefined - Was crashing upload.py, ab_testing.py, analytics.py, comment_reply.py
AB_TEST_WAIT_HOURS undefined - Was crashing ab_testing.py
COMMENT_REPLY_MIN_HOURS undefined - Was crashing comment_reply.py
Videos not publishing - Added proper scheduled publishing with publishAt
Comment reply & A/B testing not integrated - Were just echo commands in workflow
Video Quality Improvements
FPS: 8 → 30 - No more choppy video
Resolution: 720p → 1080p - Full HD
CRF: 23 → 20 - Better visual quality
Preset: ultrafast → medium - Better compression
NO black screens - Rich dark backgrounds with visible content, never pure black
Atmospheric music - Multi-layered dark ambient (was just sine wave beeps)
Film grain texture - Prevents YouTube compression banding
Publishing & Scheduling
4 daily posting times - 6AM, 12PM, 5PM, 10PM UTC
Automatic scheduled publishing - Uses publishAt for optimal timing
Smart time slot selection - Picks next available slot automatically
SEO Optimization
Hybrid tag strategy - Mix of broad + niche + trending keywords
30 tags max (was 15) - More discovery opportunities
Smart hashtag rotation - Different hashtag groups per video
SEO-optimized descriptions - Hook line, timestamps, keyword paragraph, hashtags
Engagement title prefixes - "SHOCKING:", "REVEALED:", etc. for CTR
Thumbnail Improvements
CTR-optimized - Emotion words (SHOCKING, UNSEEN, etc.)
Yellow text - Highest CTR color on YouTube
Glow effects - Text stands out on small screens
High quality (98%) - Was 88%
NEVER black - Always has visible content
Engagement
AI-powered comment replies - Gemini generates contextual replies
Smart reply timing - Waits 2hrs, skips spam, limits per run
A/B title testing - Tests alternative titles after 24hrs
Pinned comments - Engagement-optimized questions
Setup Instructions
1. GitHub Repository Secrets
Add these secrets in your repo: Settings → Secrets and variables → Actions

Secret
Description
GEMINI_API_KEY	Google Gemini API key for script generation
PEXELS_API_KEY	Pexels API key for stock images
YT_CLIENT_ID	YouTube OAuth2 client ID
YT_CLIENT_SECRET	YouTube OAuth2 client secret
YT_REFRESH_TOKEN	YouTube OAuth2 refresh token

2. Getting YouTube OAuth2 Credentials
Go to Google Cloud Console
Create a new project
Enable YouTube Data API v3
Create OAuth2 credentials (Desktop app)
Get your refresh token using the OAuth2 playground
3. Customize Settings
Edit config.py to customize:

python

# Posting schedule (UTC times)
PUBLISH_SCHEDULE_UTC = ["09:00", "14:00", "18:00", "11:00", "16:00"]

# Video quality
FPS = 30           # Frames per second
CRF = 20           # Quality (lower = better, 15-28 range)
PRESET = "medium"  # Encoding speed vs quality

# Languages per run
LANGS_PER_RUN = 3  # Number of languages to process each run
4. Trigger the Workflow
The workflow runs automatically 4 times daily. You can also trigger it manually:

Go to Actions tab → Crime Auto → Run workflow
5. Publishing Schedule
Videos are automatically scheduled for the next available time slot:

Videos need at least 3 hours lead time for YouTube scheduling
If all today's slots are passed, it schedules for tomorrow
If scheduling fails, video is published immediately as fallback
File Structure
text

crime-channel/
├── .github/workflows/
│   └── auto.yml           # GitHub Actions workflow (4 daily runs)
├── config.py              # All configuration (NEW: scheduling, SEO, etc.)
├── prepare.py             # AI script generation + SEO metadata
├── downloadimages.py      # Pexels image download + fallback generation
├── build.py               # Video rendering (30 FPS, 1080p, no black screens)
├── upload.py              # YouTube upload with scheduled publishing
├── comment_reply.py       # AI-powered comment reply automation
├── ab_testing.py          # A/B title testing for CTR optimization
├── analytics.py           # Video performance tracking
├── requirements.txt       # Python dependencies
└── README.md              # This file
Key Differences from Original
Feature
Original
Optimized
FPS	8	30
Resolution	720p	1080p
Black screens	Common	NEVER
Music	Sine wave beeps	Multi-layered ambient
Publishing	Immediate only	Scheduled at optimal times
Daily runs	1 (midnight)	4 (6AM, 12PM, 5PM, 10PM UTC)
Tags	15 max	30 max (hybrid strategy)
Hashtags	Static	Rotated per video
Thumbnails	Basic text overlay	CTR-optimized with glow
Comment replies	Not integrated	AI-powered contextual replies
A/B testing	Echo commands only	Fully integrated
SEO	Basic	Full optimization
ANALYTICS path	UNDEFINED (crash!)	Properly configured
