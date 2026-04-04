import os, json, random, datetime, time, requests
from config import *

# ─── LLM PROVIDER SYSTEM ─────────────────────────────────────
# Tries Groq first (best free tier), then Cohere, then Gemini
# Each provider tried with exponential backoff on rate limits

def _groq_call(prompt, key):
    return requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.85
        },
        timeout=180
    )

def _groq_parse(resp):
    return resp.json()["choices"][0]["message"]["content"].strip()

def _cohere_call(prompt, key):
    return requests.post(
        "https://api.cohere.com/v2/chat",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "command-r",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.85
        },
        timeout=180
    )

def _cohere_parse(resp):
    return resp.json()["message"]["content"][0]["text"].strip()

def _gemini_call(prompt, key, model):
    return requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.85}
        },
        timeout=180
    )

def _gemini_parse(resp):
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def build_providers():
    """Build list of (name, call_fn, parse_fn) ordered by priority."""
    providers = []

    # 1. Groq — best free tier: 30 RPM, 14400 RPD, no credit card
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        providers.append(("Groq-Llama3.3-70B",
                          lambda p: _groq_call(p, groq_key),
                          _groq_parse))

    # 2. Cohere — good backup: 10 RPM trial, no credit card
    cohere_key = os.environ.get("COHERE_API_KEY", "")
    if cohere_key:
        providers.append(("Cohere-CommandR",
                          lambda p: _cohere_call(p, cohere_key),
                          _cohere_parse))

    # 3. Gemini — last resort (your quota may be drained)
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        for model in ["gemini-2.5-flash-preview-05-20", "gemini-2.0-flash", "gemini-1.5-flash"]:
            providers.append((f"Gemini-{model}",
                              lambda p, m=model: _gemini_call(p, gemini_key, m),
                              _gemini_parse))

    return providers

def call_llm(prompt, retries=4):
    """Try each provider with exponential backoff on rate limits."""
    providers = build_providers()
    if not providers:
        raise Exception(
            "No API keys found! Add at least GROQ_API_KEY to your GitHub Secrets.\n"
            "Get one free at https://console.groq.com (30 seconds, no credit card)"
        )

    for name, call_fn, parse_fn in providers:
        for attempt in range(retries):
            try:
                resp = call_fn(prompt)

                if resp.status_code == 429:
                    wait = min(90, 15 * (2 ** attempt) + random.uniform(0, 5))
                    print(f"    Rate limited ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                text = parse_fn(resp)

                if not text or len(text) < 20:
                    raise Exception("Empty or too-short response")

                print(f"    OK ({name})")
                return text

            except requests.exceptions.Timeout:
                print(f"    Timeout ({name}), retrying...")
                time.sleep(10)
                continue

            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                    wait = min(90, 15 * (2 ** attempt))
                    print(f"    Quota hit ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif "not found" in err.lower() or "does not exist" in err.lower():
                    print(f"    Model unavailable ({name}), trying next provider...")
                    break  # skip to next provider
                else:
                    if attempt < retries - 1:
                        print(f"    Error: {err[:100]}")
                        time.sleep(5)
                    continue

    raise Exception("All LLM providers failed after all retries")


# ─── SCRIPT GENERATION ───────────────────────────────────────

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
    return call_llm(prompt, retries=5)

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
    return call_llm(prompt)

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
    return call_llm(prompt)

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
    result = call_llm(prompt)
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


# ─── MAIN ────────────────────────────────────────────────────

def main():
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)

    # Show which providers are available
    providers = build_providers()
    print(f"Available providers: {[p[0] for p in providers]}")
    if not providers:
        print("FATAL: No API keys configured!")
        print("Add GROQ_API_KEY to GitHub Secrets: https://console.groq.com")
        raise SystemExit(1)

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

    # Pick languages for this run (rotate daily)
    all_codes = list(LANGUAGES.keys())
    day_num = datetime.date.today().toordinal()
    start = day_num % len(all_codes)
    selected = [all_codes[(start + i) % len(all_codes)] for i in range(LANGS_PER_RUN)]
    if "en" not in selected:
        selected[0] = "en"
    print(f"\nLanguages this run: {[LANGUAGES[c]['name'] for c in selected]}")

    # Step 3: Translate selected languages + metadata
    all_meta = {}
    total_tasks = len(selected) * 4
    task_num = 0

    for code in selected:
        info = LANGUAGES[code]
        print(f"\n--- {info['name']} ({code}) ---")

        if code == "en":
            task_num += 1
            print(f"  [{task_num}/{total_tasks}] Long metadata...")
            long_meta = generate_metadata(working_title, code, info["name"], False)
            task_num += 1
            print(f"  [{task_num}/{total_tasks}] Short metadata...")
            short_meta = generate_metadata(working_title, code, info["name"], True)
            all_meta[code] = {"long": long_meta, "short": short_meta}
            continue

        # Translate long
        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Translating long script...")
        try:
            long_trans = translate_script(long_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w") as f:
                f.write(long_trans)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        # Translate short
        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Translating short script...")
        try:
            short_trans = translate_script(short_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w") as f:
                f.write(short_trans)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        # Long metadata
        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Long metadata...")
        try:
            long_meta = generate_metadata(working_title, code, info["name"], False)
        except Exception as e:
            print(f"  FAILED: {e}")
            long_meta = {"title": working_title, "description": "", "tags": ["true crime"]}

        # Short metadata
        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Short metadata...")
        try:
            short_meta = generate_metadata(working_title, code, info["name"], True)
        except Exception as e:
            print(f"  FAILED: {e}")
            short_meta = {"title": working_title, "description": "", "tags": ["true crime", "shorts"]}

        all_meta[code] = {"long": long_meta, "short": short_meta}
        print(f"  Done {info['name']}")

        # Pause between languages to respect rate limits
        if code != selected[-1]:
            print("  Pausing 5s...")
            time.sleep(5)

    # Save everything
    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(selected, f)

    print(f"\n{'='*45}")
    print(f"DONE — {len(all_meta)} languages ready")
    print(f"{'='*45}")

if __name__ == "__main__":
    main()
