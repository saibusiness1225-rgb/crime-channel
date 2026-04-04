import os, json, random, datetime, time
from google import genai
from google.genai import types
from config import *

# Model fallback chain — tries each until one works
MODELS = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

def call_gemini(prompt, retries=5):
    """Call Gemini with model fallback + exponential backoff."""
    for model_name in MODELS:
        for attempt in range(retries):
            try:
                client = genai.Client(api_key=GEMINI_KEY)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                text = response.text.strip()
                if not text:
                    raise Exception("Empty response")
                print(f"    OK ({model_name}, attempt {attempt+1})")
                return text
            except Exception as e:
                err = str(e)
                if "RESOURCE_EXHAUSTED" in err or "429" in err or "quota" in err.lower():
                    wait = min(60, 10 * (2 ** attempt) + random.uniform(0, 5))
                    print(f"    Quota hit ({model_name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif "not found" in err.lower() or "does not exist" in err.lower():
                    print(f"    Model {model_name} not available, trying next...")
                    break
                else:
                    wait = 5 * (attempt + 1)
                    print(f"    Error: {err[:80]}... retrying in {wait}s")
                    time.sleep(wait)
                    continue
    raise Exception("All models failed after all retries")

def generate_script(case_type):
    prompt = f"""You are an expert true crime scriptwriter for YouTube.
Write a detailed narration script for a 20-minute video about a REAL criminal case in the category of "{case_type}".

REQUIREMENTS:
1. Script must be 2800-3800 words (about 20 minutes at natural pace)
2. Dramatic, suspenseful documentary tone like a Netflix true crime narrator
3. Structure with these EXACT section markers:
   [HOOK] — 30 seconds, shocking opening line or question
   [INTRO] — 90 seconds, set the scene and introduce the case
   [BACKGROUND] — 3 min, victim profile, location, circumstances
   [THE CRIME] — 5 min, detailed account of events
   [INVESTIGATION] — 4 min, how authorities investigated, key evidence
   [SUSPECTS] — 3 min, persons of interest and their stories
   [RESOLUTION] — 2 min, trial/verdict or current status of the case
   [CONCLUSION] — 1 min, aftermath, lasting impact, subscribe CTA
4. Use vivid, cinematic language
5. Include specific dates, locations, names from real public records
6. Add [PAUSE] markers at natural dramatic pauses
7. Add [SCENE CHANGE] between each major section
8. Output ONLY the narration text, no stage directions
9. Pick a specific, real, well-documented case. NOT fictional.
10. Choose a case NOT extremely overcovered on YouTube."""

    return call_gemini(prompt)

def generate_short_script(title):
    prompt = f"""Write a 60-second YouTube Short script about a shocking true crime fact.
The main video is titled "{title}" — derive a compelling short from a specific detail.

REQUIREMENTS:
- 140-170 words exactly
- First 5 words must grab attention immediately
- Deliver one key fact clearly and dramatically
- End with "Follow for the full story."
- Include [PAUSE] markers for pacing
- Narration only, dramatic urgent tone"""

    return call_gemini(prompt)

def translate_script(script, lang_code, lang_name):
    prompt = f"""Translate the following YouTube true crime narration script to {lang_name}.
RULES:
- Keep dramatic, suspenseful documentary tone
- Preserve ALL markers exactly: [HOOK], [INTRO], [BACKGROUND], [THE CRIME], [INVESTIGATION], [SUSPECTS], [RESOLUTION], [CONCLUSION], [PAUSE], [SCENE CHANGE]
- Keep proper nouns in original form unless a well-known local version exists
- Adapt idioms naturally, do NOT translate word-for-word
- Maintain approximate word count
- Output ONLY the translated narration text

SCRIPT:
{script}"""

    return call_gemini(prompt)

def generate_metadata(title, lang_code, lang_name, is_short=False):
    kind = "YouTube Short" if is_short else "20-minute YouTube documentary"
    prompt = f"""Generate YouTube SEO metadata in {lang_name} for a true crime {kind}.
Working title: {title}

Output EXACTLY this JSON format (no other text):
{{
  "title": "clickworthy title under 70 chars",
  "description": "SEO description with keywords, 2-3 paragraphs, include hashtags at end",
  "tags": ["tag1", "tag2", "...up to 15 tags"]
}}

Rules:
- Title must be clickworthy but not clickbait
- Description should include relevant keywords naturally
- Tags mix broad and specific
- All text in {lang_name}"""

    result = call_gemini(prompt)
    # Strip markdown code fences if present
    if result.startswith("```"):
        result = result.split("\n", 1)[1] if "\n" in result else result[3:]
        result = result.rsplit("```", 1)[0]
    return json.loads(result.strip())

def extract_title(script):
    for line in script.split("\n"):
        clean = line.replace("[HOOK]", "").strip()
        if clean and len(clean) > 10:
            return clean[:100]
    return "True Crime Mystery"

def main():
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)

    # Pick case category
    case_type = random.choice(CASE_CATEGORIES)
    print(f"Selected category: {case_type}")

    # Step 1: English long script
    print("\n[1/2] Generating long script...")
    long_script = generate_script(case_type)
    working_title = extract_title(long_script)
    print(f"  Title: {working_title}")
    print(f"  Words: {len(long_script.split())}")
    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w") as f:
        f.write(long_script)

    # Step 2: English short script
    print("\n[2/2] Generating short script...")
    short_script = generate_short_script(working_title)
    print(f"  Words: {len(short_script.split())}")
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w") as f:
        f.write(short_script)

    # Determine which languages to process this run
    all_codes = list(LANGUAGES.keys())
    day_num = datetime.date.today().toordinal()
    start = day_num % len(all_codes)
    selected = [all_codes[(start + i) % len(all_codes)] for i in range(LANGS_PER_RUN)]
    # Always include English
    if "en" not in selected:
        selected[0] = "en"

    print(f"\nSelected languages for this run: {[LANGUAGES[c]['name'] for c in selected]}")

    # Step 3: Translate ONLY selected languages + generate metadata
    all_meta = {}
    total_calls = len(selected) * 4  # 2 translations + 2 metadata per lang
    call_num = 0

    for code in selected:
        info = LANGUAGES[code]
        print(f"\n--- {info['name']} ({code}) ---")

        if code == "en":
            # English: just metadata, no translation needed
            call_num += 1
            print(f"  [{call_num}/{total_calls}] Long metadata...")
            long_meta = generate_metadata(working_title, code, info["name"], False)
            call_num += 1
            print(f"  [{call_num}/{total_calls}] Short metadata...")
            short_meta = generate_metadata(working_title, code, info["name"], True)
            all_meta[code] = {"long": long_meta, "short": short_meta}
            continue

        # Translate long script
        call_num += 1
        print(f"  [{call_num}/{total_calls}] Translating long script...")
        try:
            long_trans = translate_script(long_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w") as f:
                f.write(long_trans)
        except Exception as e:
            print(f"  FAILED long translation: {e}")
            continue

        # Translate short script
        call_num += 1
        print(f"  [{call_num}/{total_calls}] Translating short script...")
        try:
            short_trans = translate_script(short_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w") as f:
                f.write(short_trans)
        except Exception as e:
            print(f"  FAILED short translation: {e}")
            continue

        # Long metadata
        call_num += 1
        print(f"  [{call_num}/{total_calls}] Long metadata...")
        try:
            long_meta = generate_metadata(working_title, code, info["name"], False)
        except Exception as e:
            print(f"  FAILED long metadata: {e}")
            long_meta = {"title": working_title, "description": "", "tags": ["true crime"]}

        # Short metadata
        call_num += 1
        print(f"  [{call_num}/{total_calls}] Short metadata...")
        try:
            short_meta = generate_metadata(working_title, code, info["name"], True)
        except Exception as e:
            print(f"  FAILED short metadata: {e}")
            short_meta = {"title": working_title, "description": "", "tags": ["true crime", "shorts"]}

        all_meta[code] = {"long": long_meta, "short": short_meta}
        print(f"  Done {info['name']}")

        # Pause between languages to avoid hitting rate limits
        if code != selected[-1]:
            print("  Pausing 8s between languages...")
            time.sleep(8)

    # Save all metadata
    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)

    # Save selected languages
    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(selected, f)

    print(f"\n========================================")
    print(f"COMPLETE — {len(all_meta)} languages ready")
    print(f"Selected: {[LANGUAGES[c]['name'] for c in selected]}")
    print(f"========================================")

if __name__ == "__main__":
    main()
