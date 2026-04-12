import os, json, random, datetime, time, re, requests
from config import *


# ═══════════════════════════════════════════════════════════════
# LLM PROVIDERS
# ═══════════════════════════════════════════════════════════════

def _cerebras_call(prompt, key):
    return requests.post("https://api.cerebras.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b", "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 8192, "temperature": 0.85}, timeout=180)

def _cerebras_parse(r): return r.json()["choices"][0]["message"]["content"].strip()

def _groq_call(prompt, key):
    return requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 8192, "temperature": 0.85}, timeout=180)

def _groq_parse(r): return r.json()["choices"][0]["message"]["content"].strip()

def _cohere_call(prompt, key):
    return requests.post("https://api.cohere.com/v2/chat",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "command-r", "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 8192, "temperature": 0.85}, timeout=180)

def _cohere_parse(r): return r.json()["message"]["content"][0]["text"].strip()

def _gemini_call(prompt, key, model):
    return requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.85}}, timeout=180)

def _gemini_parse(r): return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def build_providers():
    p = []
    # Cerebras first - free and fast
    k = os.environ.get("CEREBRAS_API_KEY", "")
    if k: p.append(("Cerebras", lambda pr: _cerebras_call(pr, k), _cerebras_parse))
    k = os.environ.get("GROQ_API_KEY", "")
    if k: p.append(("Groq", lambda pr: _groq_call(pr, k), _groq_parse))
    k = os.environ.get("COHERE_API_KEY", "")
    if k: p.append(("Cohere", lambda pr: _cohere_call(pr, k), _cohere_parse))
    k = os.environ.get("GEMINI_API_KEY", "")
    if k:
        # REMOVED: gemini-1.5-flash (deprecated/returns 404)
        # ADDED: gemini-2.0-flash-lite, gemini-1.5-flash-8b
        for m in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-8b"]:
            p.append((f"Gemini-{m}", lambda pr, md=m: _gemini_call(pr, k, md), _gemini_parse))
    return p

def call_llm(prompt, retries=3):
    for name, cfn, pfn in build_providers():
        for a in range(retries):
            try:
                r = cfn(prompt)
                if r.status_code == 429:
                    wait = min(120, 30 * (2 ** a) + random.uniform(0, 10))
                    print(f"    Rate limited ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                t = pfn(r)
                if len(t) < 20: raise Exception("short response")
                print(f"    OK ({name})")
                return t
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower():
                    wait = min(120, 30 * (2 ** a))
                    print(f"    Quota ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif "not found" in err.lower() or "does not exist" in err.lower():
                    print(f"    Unavailable ({name}), skipping")
                    break
                else:
                    # FIX: Actually print the error and properly handle retries!
                    if a < retries - 1:
                        print(f"    Retry {a+1}/{retries} ({name}): {err[:100]}")
                        time.sleep(10)
                        continue
                    else:
                        print(f"    Failed ({name}): {err[:100]}")
                        break
    raise Exception("All LLM providers failed")


# ═══════════════════════════════════════════════════════════════
# JSON SAFETY
# ═══════════════════════════════════════════════════════════════

def safe_json(text):
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0] if "\n" in text else text[3:]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text.strip())
    try: return json.loads(text)
    except: pass
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try: return json.loads(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', m.group()))
        except: pass
    return {"title": "True Crime", "description": "", "tags": ["true crime"], "pinned_comment": ""}


# ═══════════════════════════════════════════════════════════════
# SCRIPT GENERATION
# ═══════════════════════════════════════════════════════════════

def gen_script(ct):
    return call_llm(f"""You are a YouTube true crime narrator with 10M+ subscribers. Your videos average 85% retention.

Write a 20-minute true crime narration script about a REAL case from "{ct}".

ENGAGEMENT RULES:
1. OPENING HOOK: Start mid-action with the most shocking moment. "The 911 call came in at 3:47 AM. The caller was screaming. But what the police found when they arrived was something no one was prepared for."
2. Every 3-4 minutes, insert an INTERACTIVE QUESTION: "Ask yourself — would you have opened that door?" / "Here's where most people make a wrong assumption..."
3. Before EVERY section change, add RETENTION HOOK: "But what happened next changes everything..."
4. CURIOSITY GAPS: "What police found next would haunt them forever" then DON'T reveal immediately
5. SPECIFIC DETAILS: Exact dates, times, addresses. "It was 11 degrees below zero on December 14th, 1997, when..."
6. EMOTIONAL ANCHORING: Every 5 minutes, reconnect to the victim as a real person
7. COMMENT BAIT: "People still argue about this to this day in the comments..."
8. END with subscribe CTA + engagement question

STRUCTURE with markers:
[HOOK] [INTRO] [BACKGROUND] [THE CRIME] [INVESTIGATION] [SUSPECTS] [RESOLUTION] [CONCLUSION]
Add [PAUSE] at dramatic moments. Add [SCENE CHANGE] between sections.

3000+ words. Real documented case. Narration only.""")

def gen_short(title):
    return call_llm(f"""You write YouTube Shorts that get 5M+ views.

Write a 60-second Short about: "{title}"

STRUCTURE:
- First line: A question that makes people stop scrolling
- Middle: The one most disturbing fact
- End: "What do YOU think? Tell me in the comments."

140-170 words. [PAUSE] markers. Dramatic narration only.""")

def translate(script, code, name):
    return call_llm(f"""Translate this true crime script to {name}.
RULES:
- Keep dramatic, suspenseful tone
- Preserve ALL markers: [HOOK] [INTRO] [BACKGROUND] [THE CRIME] [INVESTIGATION] [SUSPECTS] [RESOLUTION] [CONCLUSION] [PAUSE] [SCENE CHANGE]
- Keep proper nouns in original form
- Adapt idioms naturally
- Keep ALL interactive questions
- Maintain word count
- Output ONLY translated text

SCRIPT:
{script}""")

def gen_meta(title, code, name, short=False):
    k = "YouTube Short under 60 seconds" if short else "20-minute true crime documentary"
    r = call_llm(f"""YouTube SEO expert. Generate metadata in {name} for a {k}.
Working title reference: {title}

Output ONLY this JSON:
{{
  "title": "CURATED TITLE (under 60 chars long, 50 for Shorts, curiosity gap, one number)",
  "title_b": "ALTERNATIVE TITLE for A/B testing (different angle, same topic)",
  "description": "FULL DESCRIPTION (first 150 chars critical for search, timestamps for long, hashtags at end)",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"],
  "pinned_comment": "DEBATE QUESTION (under 200 chars, reference case detail)"
}}

TITLE: Curiosity gap + number + no clickbait
SHORT TITLE: Start with question mark
DESCRIPTION: Hook + summary + details + hashtags
TAGS: 3 broad + 4 specific + 3 long-tail
PINNED COMMENT: Create debate""")

    return safe_json(r)

def extract_title(s):
    for l in s.split("\n"):
        c = l.replace("[HOOK]", "").strip()
        if c and len(c) > 10: return c[:100]
    return "True Crime Mystery"


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)

    # Check for forced type
    force_type = os.environ.get("FORCE_TYPE", "both").lower()
    
    # Determine run config
    config = get_run_config()
    if force_type == "short":
        config["types"] = ["short"]
    elif force_type == "long":
        config["types"] = ["long"]
    
    print(f"Day: {config['day_name']}")
    print(f"Shorts only: {config['shorts_only']}")
    print(f"Types: {config['types']}")
    
    # Save run config
    with open(os.path.join(OUT, "run_config.json"), "w") as f:
        json.dump(config["types"], f)

    provs = build_providers()
    print(f"Providers: {[p[0] for p in provs]}")
    if not provs:
        raise SystemExit("No API keys! Add CEREBRAS_API_KEY or GROQ_API_KEY to GitHub Secrets.")

    # Pick category
    ct = random.choice(CASE_CATEGORIES)
    print(f"Category: {ct}")

    print("\n[1/2] Generating long script...")
    ls = gen_script(ct)
    wt = extract_title(ls)
    print(f"  Title: {wt}")
    print(f"  Words: {len(ls.split())}")
    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w") as f:
        f.write(ls)

    print("\n[2/2] Generating short script...")
    ss = gen_short(wt)
    print(f"  Words: {len(ss.split())}")
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w") as f:
        f.write(ss)

    # Select languages
    force_langs = os.environ.get("FORCE_LANGS", "")
    if force_langs:
        sel = [l.strip() for l in force_langs.split(",") if l.strip() in LANGUAGES]
        if not sel:
            sel = ["en"]
    else:
        ac = list(LANGUAGES.keys())
        d = datetime.date.today().toordinal()
        sel = [ac[(d + i) % len(ac)] for i in range(LANGS_PER_RUN)]
        if "en" not in sel: sel[0] = "en"
    
    print(f"\nLanguages: {[LANGUAGES[c]['name'] for c in sel]}")

    am = {}
    for code in sel:
        info = LANGUAGES[code]
        print(f"\n--- {info['name']} ({code}) ---")
        
        if code == "en":
            lm = gen_meta(wt, code, info["name"], False)
            sm = gen_meta(wt, code, info["name"], True)
            am[code] = {"long": lm, "short": sm}
            print(f"  Title: {lm.get('title', '?')}")
            print(f"  Title B: {lm.get('title_b', '?')}")
            continue
        
        try:
            lt = translate(ls, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w") as f:
                f.write(lt)
            st = translate(ss, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w") as f:
                f.write(st)
            lm = gen_meta(wt, code, info["name"], False)
            sm = gen_meta(wt, code, info["name"], True)
            am[code] = {"long": lm, "short": sm}
            print(f"  Title: {lm.get('title', '?')}")
        except Exception as e:
            print(f"  Failed: {e}")
        time.sleep(3)

    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(am, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(sel, f)

    print(f"\n{'=' * 50}")
    print(f"DONE — {len(am)} languages | Types: {config['types']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
