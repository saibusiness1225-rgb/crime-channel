import os, json, random, datetime, time, re, requests
from config import *

# ─── LLM PROVIDER SYSTEM ─────────────────────────────────────

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
    providers = []
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        providers.append(("Groq-Llama3.3-70B",
                          lambda p: _groq_call(p, groq_key),
                          _groq_parse))
    cohere_key = os.environ.get("COHERE_API_KEY", "")
    if cohere_key:
        providers.append(("Cohere-CommandR",
                          lambda p: _cohere_call(p, cohere_key),
                          _cohere_parse))
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        for model in ["gemini-2.5-flash-preview-05-20", "gemini-2.0-flash", "gemini-1.5-flash"]:
            providers.append((f"Gemini-{model}",
                              lambda p, m=model: _gemini_call(p, gemini_key, m),
                              _gemini_parse))
    return providers

def call_llm(prompt, retries=4):
    providers = build_providers()
    if not providers:
        raise Exception(
            "No API keys found! Add GROQ_API_KEY to GitHub Secrets.\n"
            "Free at https://console.groq.com"
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
                    print(f"    Model unavailable ({name}), trying next...")
                    break
                else:
                    if attempt < retries - 1:
                        print(f"    Error: {err[:100]}")
                        time.sleep(5)
                    continue
    raise Exception("All LLM providers failed")


# ─── SAFE JSON PARSER ────────────────────────────────────────

def safe_json_parse(text):
    """Parse JSON from LLM output, handling control characters and code fences."""
    # Strip code fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # Remove control characters that break JSON (keep \n, \t, \r)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from surrounding text
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            inner = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', match.group())
            return json.loads(inner)
        except json.JSONDecodeError:
            pass

    # Last resort: fix common issues
    try:
        # Replace unescaped newlines inside strings
        fixed = re.sub(r'(?<=": ")(.*?)(?="[,}])',
                       lambda m: m.group(0).replace('\n', ' ').replace('\r', ''),
                       cleaned)
        return json.loads(fixed)
    except json.JSONDecodeError:
        raise Exception(f"Could not parse JSON from LLM output. First 200 chars: {text[:200]}")


# ─── SCRIPT GENERATION ───────────────────────────────────────

def generate_script(case_type):
    prompt = f"""You are an expert true crime scriptwriter for YouTube.
Write a detailed narration script for a 20-minute video about a REAL criminal case in the category of "{case_type}".

REQUIREMENTS:
1. Script MUST be at least 3000 words. Count your words. If under 3000, keep writing more details. This is NON-NEGOTIABLE.
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
4. Use vivid, cinematic language — describe scenes, weather, emotions, locations in detail
5. Include specific dates, locations, names from real public records
6. Add [PAUSE] markers at natural dramatic pauses
7. Add [SCENE CHANGE] between each major section
8. Output ONLY the narration text, no stage directions
9. Pick a specific, real, well-documented case. NOT fictional.
10. Choose a case NOT extremely overcovered on YouTube
11. To reach 3000+ words, elaborate extensively on each section — describe the location, the people involved, the timeline in extreme detail"""

    for attempt in range(3):
        text = call_llm(prompt, retries=5)
        word_count = len(text.split())
        if word_count >= 2500:
            return text
        print(f"    Script only {word_count} words, regenerating (attempt {attempt+2})...")
        prompt += f"\n\nIMPORTANT: Your previous attempt was only {word_count} words. You MUST write at least 3000 words. Be much more detailed. Expand every section significantly."

    return text  # return even if short, better than crashing

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

Output ONLY valid JSON with this exact structure, nothing else:
{{"title": "clickworthy title under 70 chars", "description": "SEO description 2-3 paragraphs with hashtags at end", "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]}}

Rules:
- Title must be clickworthy but not clickbait, under 70 characters
- Description should include relevant keywords naturally, 2-3 paragraphs, hashtags at the end
- Tags: exactly 5-15 tags mixing broad (true crime) and specific (case names, locations)
- All text in {lang_name}
- Output ONLY the JSON object, no markdown, no explanation, no code fences"""

    for attempt in range(3):
        result = call_llm(prompt)
        try:
            return safe_json_parse(result)
        except Exception as e:
            print(f"    JSON parse failed (attempt {attempt+1}): {str(e)[:80]}")
            if attempt < 2:
                time.sleep(2)

    # Hardcoded fallback so the pipeline never crashes
    return {
        "title": title[:65] if len(title) > 65 else title,
        "description": f"A shocking true crime case that will leave you speechless.\\n\\nSubscribe for more true crime content.\\n\\n#truecrime #mystery #crime",
        "tags": ["true crime", "mystery", "crime", "documentary", "unsolved"]
    }

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

    providers = build_providers()
    print(f"Available providers: {[p[0] for p in providers]}")
    if not providers:
        print("FATAL: No API keys configured!")
        print("Add GROQ_API_KEY to GitHub Secrets: https://console.groq.com")
        raise SystemExit(1)

    case_type = random.choice(CASE_CATEGORIES)
    print(f"Selected category: {case_type}")

    # Step 1: English long script
    print("\n[1/2] Generating long script...")
    long_script = generate_script(case_type)
    working_title = extract_title(long_script)
    wc = len(long_script.split())
    print(f"  Title: {working_title}")
    print(f"  Words: {wc}")
    if wc < 2000:
        print(f"  WARNING: Script is under 2000 words. Video will be shorter than target.")
    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w") as f:
        f.write(long_script)

    # Step 2: English short script
    print("\n[2/2] Generating short script...")
    short_script = generate_short_script(working_title)
    print(f"  Words: {len(short_script.split())}")
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w") as f:
        f.write(short_script)

    # Pick languages for this run
    all_codes = list(LANGUAGES.keys())
    day_num = datetime.date.today().toordinal()
    start = day_num % len(all_codes)
    selected = [all_codes[(start + i) % len(all_codes)] for i in range(LANGS_PER_RUN)]
    if "en" not in selected:
        selected[0] = "en"
    print(f"\nLanguages this run: {[LANGUAGES[c]['name'] for c in selected]}")

    # Step 3: Translate + metadata
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

        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Translating long script...")
        try:
            long_trans = translate_script(long_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w") as f:
                f.write(long_trans)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Translating short script...")
        try:
            short_trans = translate_script(short_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w") as f:
                f.write(short_trans)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Long metadata...")
        try:
            long_meta = generate_metadata(working_title, code, info["name"], False)
        except Exception as e:
            print(f"  FAILED: {e}")
            long_meta = {"title": working_title, "description": "", "tags": ["true crime"]}

        task_num += 1
        print(f"  [{task_num}/{total_tasks}] Short metadata...")
        try:
            short_meta = generate_metadata(working_title, code, info["name"], True)
        except Exception as e:
            print(f"  FAILED: {e}")
            short_meta = {"title": working_title, "description": "", "tags": ["true crime", "shorts"]}

        all_meta[code] = {"long": long_meta, "short": short_meta}
        print(f"  Done {info['name']}")

        if code != selected[-1]:
            print("  Pausing 5s...")
            time.sleep(5)

    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(selected, f)

    print(f"\n{'='*45}")
    print(f"DONE — {len(all_meta)} languages ready")
    print(f"{'='*45}")

if __name__ == "__main__":
    main()
