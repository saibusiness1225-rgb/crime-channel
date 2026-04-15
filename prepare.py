"""
Script Preparation - OPTIMIZED with SEO, Hashtags, and Engagement
- Gemini AI for high-quality true crime scripts
- SEO-optimized metadata (titles, descriptions, tags)
- Engagement-optimized pinned comments
- Smart hashtag generation
- A/B test title variants
- Multi-language support with proper translations
"""
import os, json, random, time, datetime, re
import requests
from config import *


def build_providers():
    """Build list of AI providers with fallbacks."""
    providers = []
    if GEMINI_KEY:
        providers.append(("Gemini", call_gemini))
    # Pollinations as free fallback
    providers.append(("Pollinations", call_pollinations))
    return providers


def call_gemini(prompt, max_retries=2):
    """Call Gemini API for script generation."""
    for attempt in range(max_retries):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 4096,
                    "topP": 0.95,
                }
            }
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                if len(text) > 200:
                    return text
            print(f"  Gemini attempt {attempt+1} failed: {r.status_code}")
        except Exception as e:
            print(f"  Gemini error: {str(e)[:60]}")
        time.sleep(3)
    return None


def call_pollinations(prompt):
    """Call Pollinations as free fallback."""
    try:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "openai",
            "seed": random.randint(1, 99999),
        }
        r = requests.post(url, json=payload, timeout=120)
        if r.status_code == 200:
            text = r.text
            if len(text) > 200:
                return text
    except Exception as e:
        print(f"  Pollinations error: {str(e)[:60]}")
    return None


def gen_script(category):
    """Generate long-form true crime script with engagement hooks."""
    prompt = f"""Write a compelling, factual true crime documentary script about: {category}

REQUIREMENTS:
- 2000-2500 words for a 15-20 minute video
- Use EXACTLY these section markers: [HOOK] [INTRO] [BACKGROUND] [THE CRIME] [INVESTIGATION] [SUSPECTS] [RESOLUTION] [CONCLUSION]
- [HOOK]: Start with a shocking fact or question that grabs attention in the first 10 seconds
- [INTRO]: Introduce the case and setting
- [BACKGROUND]: Provide historical and personal context
- [THE CRIME]: Describe what happened in dramatic detail
- [INVESTIGATION]: Detail the police investigation and evidence
- [SUSPECTS]: Present the suspects and their motives
- [RESOLUTION]: Explain how the case was resolved (or why it remains unsolved)
- [CONCLUSION]: Reflect on the case's impact and lingering questions
- Use [PAUSE] for dramatic pauses and [SCENE CHANGE] for visual transitions
- Write in a documentary narration style - dramatic but factual
- Include specific dates, locations, and names for authenticity
- End each section with a hook that makes viewers want to keep watching

The script should be engaging enough that viewers watch until the end."""
    return gen_with_fallback(prompt)


def gen_short(working_title):
    """Generate short-form (YouTube Shorts) script optimized for comments."""
    prompt = f"""Write a SHORT true crime script (60-90 seconds) based on: {working_title}

REQUIREMENTS:
- 150-200 words
- Start with a SHOCKING hook in the first 3 seconds
- Use [HOOK] [THE CRIME] [CONCLUSION] section markers
- End with a question that forces viewers to comment (comment bait)
- Example ending: "What would YOU have done? Tell me in the comments."
- Keep sentences short and punchy for TTS
- Use dramatic pauses with [PAUSE]"""
    return gen_with_fallback(prompt)


def gen_with_fallback(prompt):
    """Try each AI provider with fallback."""
    providers = build_providers()
    for name, fn in providers:
        print(f"  Trying {name}...")
        result = fn(prompt)
        if result and len(result) > 100:
            # Validate it's not an error message
            if not result.strip().startswith("Error:"):
                return result
            print(f"  {name} returned error message, trying next...")
    return None  # Return None instead of error string


def extract_title(script):
    """Extract or generate a compelling video title from the script."""
    # Try to get a better title using AI
    prompt = f"""Based on this true crime script, create a compelling YouTube video title.

REQUIREMENTS:
- Maximum 70 characters (for YouTube search optimization)
- Use power words: SHOCKING, UNSEEN, HIDDEN, DARK, CHILLING, TERRIFYING
- Include the case type (murder, disappearance, heist, etc.)
- Make viewers WANT to click (but not clickbait)
- Do NOT use quotes around the title
- Just the title, nothing else

Script excerpt:
{script[:800]}"""
    title = gen_with_fallback(prompt)
    if title:
        title = title.strip().strip('"').strip("'").strip()
        # Validate: title should NOT contain error messages
        if title.startswith("Error:") or len(title) < 5:
            title = None
    
    # Fallback: Generate title from script content without AI
    if not title:
        print("  AI title generation failed, generating from script content...")
        title = generate_title_from_script(script)
    
    if len(title) > 100:
        title = title[:100]
    return title


def generate_title_from_script(script):
    """Generate a title from script content without AI. NEVER returns error string."""
    prefixes = ["SHOCKING", "DARK", "HIDDEN", "CHILLING", "UNSEEN", "TERRIFYING"]
    cases = ["Murder", "Disappearance", "Cold Case", "Mystery", "Crime", "Investigation",
             "Kidnapping", "Heist", "Serial Killer", "Cold Case Murder", "Conspiracy"]
    suffixes = ["That Haunts Detectives", "Nobody Talks About", "Still Unsolved",
                "That Shocked the World", "Youve Never Heard Of", "With a Dark Secret",
                "That Changed Everything", "With No End", "That Remains a Mystery"]
    
    # Try to extract real names/places from script for authenticity
    words = script.split()
    names = []
    for w in words:
        if w[0].isupper() and len(w) > 2 and w not in ('The', 'This', 'That', 'And', 'But',
            'For', 'Was', 'Were', 'Has', 'Had', 'His', 'Her', 'They', 'Their', 'When',
            'Where', 'What', 'Which', 'Who', 'How', 'Why', 'Not', 'All', 'From', 'Into',
            'HOOK', 'INTRO', 'BACKGROUND', 'CRIME', 'INVESTIGATION', 'SUSPECTS',
            'RESOLUTION', 'CONCLUSION', 'PAUSE', 'SCENE', 'CHANGE'):
            names.append(w)
            if len(names) >= 3:
                break
    
    prefix = random.choice(prefixes)
    case = random.choice(cases)
    
    if names:
        title = f"{prefix} {case}: The {names[0]} {random.choice(suffixes)}"
    else:
        title = f"{prefix} {case} {random.choice(suffixes)}"
    
    return title[:70]


def gen_meta(working_title, lang_code, lang_name, is_short):
    """Generate SEO-optimized metadata for a video."""
    # Ensure working_title is NEVER an error message
    safe_title = working_title
    if safe_title.startswith("Error:") or len(safe_title) < 5:
        safe_title = generate_title_from_script(working_title)
    
    kind = "Short" if is_short else "Long"
    duration = "60-90 seconds" if is_short else "15-20 minutes"

    prompt = f"""Generate YouTube video metadata for a true crime video in {lang_name}.

Title: {safe_title}
Video type: {kind} ({duration})
Language: {lang_name} ({lang_code})

Generate EXACTLY this JSON format (no markdown, no extra text):
{{
  "title": "SEO-optimized title under 70 chars with power words",
  "title_b": "Alternative title for A/B testing (different angle)",
  "description": "200-300 word description that includes keywords naturally. Start with a hook sentence. Include a brief summary. End with a call to action.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13", "tag14", "tag15", "tag16", "tag17", "tag18", "tag19", "tag20"],
  "pinned_comment": "An engaging comment to pin that asks viewers a question and encourages discussion. Keep under 200 chars.",
  "category": "{random.choice(CASE_CATEGORIES)}"
}}

Requirements:
- Title must use power words for CTR (SHOCKING, DARK, HIDDEN, etc.)
- title_b should test a different emotional angle
- Description should naturally include keywords for SEO
- Tags: mix of broad (true crime, mystery) and specific (case-specific) tags
- Pinned comment should drive engagement (questions work best)
- Write EVERYTHING in {lang_name}, not English"""

    result = gen_with_fallback(prompt)
    try:
        if result is None:
            raise Exception("AI returned None")
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
        if json_match:
            meta = json.loads(json_match.group())
        else:
            meta = json.loads(result)

        # Validate and fill missing fields
        if "title" not in meta or not meta["title"] or meta["title"].startswith("Error:"):
            meta["title"] = safe_title[:70]
        if "title_b" not in meta or not meta["title_b"] or meta["title_b"].startswith("Error:"):
            meta["title_b"] = meta.get("title", safe_title)[:70]
        if "description" not in meta or not meta["description"]:
            meta["description"] = ""
        if "tags" not in meta or not meta["tags"]:
            meta["tags"] = ["true crime", "mystery", "documentary"]
        if "pinned_comment" not in meta or not meta["pinned_comment"]:
            meta["pinned_comment"] = ""
        if "category" not in meta or not meta["category"]:
            meta["category"] = random.choice(CASE_CATEGORIES)

        return meta
    except Exception as e:
        print(f"  Meta parse error: {str(e)[:60]}")
        return {
            "title": safe_title[:70],
            "title_b": safe_title[:70],
            "description": f"True crime documentary: {safe_title}",
            "tags": ["true crime", "mystery", "documentary", "crime", "unsolved"],
            "pinned_comment": f"What do you think really happened? Let us know in the comments.",
            "category": random.choice(CASE_CATEGORIES),
        }


def translate(text, lang_code, lang_name):
    """Translate script to target language using AI."""
    prompt = f"""Translate the following true crime script to {lang_name} ({lang_code}).

IMPORTANT:
- Keep all section markers like [HOOK], [INTRO], [BACKGROUND], etc. unchanged
- Keep [PAUSE] and [SCENE CHANGE] markers unchanged
- Translate naturally, not word-for-word
- Maintain the dramatic documentary tone
- Use natural-sounding {lang_name} expressions

Script to translate:
{text[:3000]}"""

    result = gen_with_fallback(prompt)
    if result and len(result) > 50:
        return result
    return text  # Return original if translation fails


def main():
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)
    os.makedirs(ANALYTICS, exist_ok=True)

    provs = build_providers()
    paid_provs = [p for p in provs if "Pollinations" not in p[0]]

    if not paid_provs:
        print("WARNING: No PAID API keys found. Using FREE fallback (Pollinations).")
        print("   Note: Translations may fail due to text length limits.")

    ct = random.choice(CASE_CATEGORIES)
    print(f"Category: {ct}")

    print("\n[1/2] Generating long script (engagement-optimized)...")
    ls = gen_script(ct)
    wt = extract_title(ls)
    print(f"  Title: {wt}")
    print(f"  Words: {len(ls.split())}")
    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w", encoding="utf-8") as f:
        f.write(ls)

    print("\n[2/2] Generating short script (comment-bait)...")
    ss = gen_short(wt)
    print(f"  Words: {len(ss.split())}")
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w", encoding="utf-8") as f:
        f.write(ss)

    # Select languages for this run
    ac = list(LANGUAGES.keys())
    d = datetime.date.today().toordinal()
    sel = [ac[(d + i) % len(ac)] for i in range(LANGS_PER_RUN)]
    if "en" not in sel:
        sel[0] = "en"
    print(f"\nLanguages this run: {[LANGUAGES[c]['name'] for c in sel]}")

    am = {}
    successful_langs = []

    for code in sel:
        info = LANGUAGES[code]
        print(f"\n--- {info['name']} ({code}) ---")

        # Always process English (it's the source)
        if code == "en":
            lm = gen_meta(wt, code, info["name"], False)
            sm = gen_meta(wt, code, info["name"], True)
            am[code] = {"long": lm, "short": sm}
            successful_langs.append(code)
            print(f"  Title: {lm.get('title', '?')}")
            print(f"  Comment: {lm.get('pinned_comment', '?')[:80]}...")
            continue

        # Process Translations (with resilient fallback)
        long_ok = False
        short_ok = False

        # Try translating long script (3 attempts)
        for attempt in range(3):
            try:
                lt = translate(ls, code, info["name"])
                if lt and len(lt) > 100:
                    with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w", encoding="utf-8") as f:
                        f.write(lt)
                    long_ok = True
                    break
            except Exception as e:
                print(f"  Long translation attempt {attempt+1} failed: {str(e)[:50]}")
            time.sleep(2)

        # Fallback: use English script if translation failed
        if not long_ok:
            print(f"  Translation failed for {code}, using English script with {info['name']} metadata")
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w", encoding="utf-8") as f:
                f.write(ls)  # Use English script as fallback
            long_ok = True

        # Try translating short script (3 attempts)
        for attempt in range(3):
            try:
                st = translate(ss, code, info["name"])
                if st and len(st) > 50:
                    with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w", encoding="utf-8") as f:
                        f.write(st)
                    short_ok = True
                    break
            except Exception as e:
                print(f"  Short translation attempt {attempt+1} failed: {str(e)[:50]}")
            time.sleep(2)

        # Fallback: use English short script
        if not short_ok:
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w", encoding="utf-8") as f:
                f.write(ss)

        # Always generate metadata (even if translation failed)
        try:
            lm = gen_meta(wt, code, info["name"], False)
            sm = gen_meta(wt, code, info["name"], True)
        except Exception as e:
            print(f"  Metadata generation failed: {str(e)[:50]}, using defaults")
            lm = {
                "title": f"True Crime - {info['name']} | {wt[:40]}",
                "title_b": f"{wt[:70]}",
                "description": f"True crime documentary in {info['name']}. {wt}",
                "tags": ["true crime", "mystery", "documentary", "crime"],
                "pinned_comment": "What do you think happened? Comment below!",
                "category": random.choice(CASE_CATEGORIES),
            }
            sm = lm.copy()

        am[code] = {"long": lm, "short": sm}
        successful_langs.append(code)
        print(f"  Title: {lm.get('title', '?')}")
        print(f"  Comment: {lm.get('pinned_comment', '?')[:80]}...")
        time.sleep(1)

    with open(os.path.join(OUT, "metadata", "all.json"), "w", encoding="utf-8") as f:
        json.dump(am, f, ensure_ascii=False, indent=2)

    # Ensure at least English is in the list
    if not successful_langs:
        successful_langs = ["en"]

    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(successful_langs, f)

    print(f"\n{'=' * 50}")
    print(f"DONE - {len(am)} languages with SEO + engagement")
    print(f"Final Build List: {successful_langs}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
