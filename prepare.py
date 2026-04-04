import os, json, random, datetime
import google.generativeai as genai
from config import *

def init_gemini():
    genai.configure(api_key=GEMINI_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")

def generate_script(model, case_type):
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

    resp = model.generate_content(prompt)
    return resp.text.strip()

def generate_short_script(model, title):
    prompt = f"""Write a 60-second YouTube Short script about a shocking true crime fact.
The main video is titled "{title}" — derive a compelling short from a specific detail.

REQUIREMENTS:
- 140-170 words exactly
- First 5 words must grab attention immediately
- Deliver one key fact clearly and dramatically
- End with "Follow for the full story."
- Include [PAUSE] markers for pacing
- Narration only
- Dramatic, urgent tone"""

    resp = model.generate_content(prompt)
    return resp.text.strip()

def translate_script(model, script, lang_code, lang_name):
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

    resp = model.generate_content(prompt)
    return resp.text.strip()

def generate_metadata(model, title, lang_code, lang_name, is_short=False):
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

    resp = model.generate_content(prompt)
    text = resp.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())

def extract_title(script):
    for line in script.split("\n"):
        clean = line.replace("[HOOK]", "").strip()
        if clean and len(clean) > 10:
            return clean[:100]
    return "True Crime Mystery"

def main():
    model = init_gemini()
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)

    case_type = random.choice(CASE_CATEGORIES)
    print(f"Selected category: {case_type}")

    print("Generating long script...")
    long_script = generate_script(model, case_type)
    working_title = extract_title(long_script)
    print(f"Working title: {working_title}")
    print(f"Script length: {len(long_script.split())} words")

    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w") as f:
        f.write(long_script)

    print("Generating short script...")
    short_script = generate_short_script(model, working_title)
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w") as f:
        f.write(short_script)

    all_meta = {}
    for code, info in LANGUAGES.items():
        if code == "en":
            long_meta = generate_metadata(model, working_title, code, info["name"], False)
            short_meta = generate_metadata(model, working_title, code, info["name"], True)
            all_meta[code] = {"long": long_meta, "short": short_meta}
            continue

        print(f"Translating to {info['name']}...")
        try:
            long_trans = translate_script(model, long_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w") as f:
                f.write(long_trans)

            short_trans = translate_script(model, short_script, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w") as f:
                f.write(short_trans)

            long_meta = generate_metadata(model, working_title, code, info["name"], False)
            short_meta = generate_metadata(model, working_title, code, info["name"], True)
            all_meta[code] = {"long": long_meta, "short": short_meta}
            print(f"  Done {info['name']}")
        except Exception as e:
            print(f"  Failed {info['name']}: {e}")

    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)

    all_codes = list(LANGUAGES.keys())
    day_num = datetime.date.today().toordinal()
    start = day_num % len(all_codes)
    selected = [all_codes[(start + i) % len(all_codes)] for i in range(LANGS_PER_RUN)]
    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(selected, f)

    print(f"\nDone. Languages this run: {selected}")
    print(f"Metadata for {len(all_meta)} languages saved.")

if __name__ == "__main__":
    main()
