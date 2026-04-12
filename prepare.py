import os, json, random, datetime, time, re, requests
from config import *

# ==========================================
# LLM PROVIDERS
# ==========================================

def _cerebras_call(prompt, key):
    # Updated model name to standard convention
    return requests.post("https://api.cerebras.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "llama3.3-70b", "messages": [{"role": "user", "content": prompt}],
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

def _pollinations_call(prompt):
    # Free fallback (No key required)
    return requests.get(
        "https://text.pollinations.ai/",
        params={"prompt": prompt, "model": "openai", "seed": random.randint(0, 1000000)},
        timeout=180
    )

def _pollinations_parse(r): return r.text.strip()

def build_providers():
    p = []
    
    # 1. Cerebras
    k = os.environ.get("CEREBRAS_API_KEY", "")
    if k: p.append(("Cerebras", lambda pr, key=k: _cerebras_call(pr, key), _cerebras_parse))
    
    # 2. Groq
    k = os.environ.get("GROQ_API_KEY", "")
    if k: p.append(("Groq", lambda pr, key=k: _groq_call(pr, key), _groq_parse))
    
    # 3. Cohere
    k = os.environ.get("COHERE_API_KEY", "")
    if k: p.append(("Cohere", lambda pr, key=k: _cohere_call(pr, key), _cohere_parse))
    
    # 4. Gemini (Using stable models)
    k = os.environ.get("GEMINI_API_KEY", "")
    if k:
        # Using stable models. Removed 2.5-flash as it might be invalid/preview-only
        for m in ["gemini-1.5-flash", "gemini-1.5-pro"]:
            p.append((f"Gemini-{m}", lambda pr, key=k, md=m: _gemini_call(pr, key, md), _gemini_parse))
            
    # 5. Pollinations (DeepSeek/OpenAI free fallback) - Always added as last resort
    p.append(("Pollinations-DeepSeek", lambda pr: _pollinations_call(pr), _pollinations_parse))
    
    return p

def call_llm(prompt, retries=3):
    providers = build_providers()
    print(f"Active Providers: {[p[0] for p in providers]}")
    
    for name, cfn, pfn in providers:
        for a in range(retries):
            try:
                r = cfn(prompt)
                
                # Handle HTTP Status Codes explicitly
                if r.status_code == 429:
                    wait = min(120, 30 * (2 ** a) + random.uniform(0, 10))
                    print(f"    Rate limited ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif r.status_code in [401, 403]:
                    print(f"    ❌ Blocked/Invalid ({name})")
                    break # Don't retry auth errors immediately
                elif r.status_code == 404:
                    print(f"    ⚠️ Unavailable ({name})")
                    break
                elif r.status_code != 200:
                    print(f"    Error {r.status_code} ({name}): {r.text[:100]}")
                    if a < retries - 1: time.sleep(10)
                    continue
                
                # Parse Response
                t = pfn(r)
                if len(t) < 20: 
                    raise Exception("Short response (possible content filter)")
                
                print(f"    ✅ OK ({name})")
                return t
                
            except Exception as e:
                err = str(e).lower()
                # Check for quota/rate limit in exception message (sometimes requests raise this)
                if "429" in err or "quota" in err or "rate limit" in err:
                    wait = min(120, 30 * (2 ** a))
                    print(f"    Rate limited ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif "401" in err or "403" in err or "invalid" in err or "blocked" in err:
                    print(f"    ❌ Blocked/Invalid ({name})")
                    break
                else:
                    # Generic error
                    if a < retries - 1: 
                        print(f"    Retrying ({name})... Error: {str(e)[:50]}")
                        time.sleep(10)
                    else:
                        print(f"    Failed ({name}): {str(e)[:50]}")
                        
    raise Exception("All LLM providers failed")


# ==========================================
# JSON SAFETY
# ==========================================

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


# ==========================================
# SCRIPT GENERATION
# ==========================================

def gen_script(ct):
    return call_llm(f"""You are a YouTube true crime narrator with 10M+ subscribers. Your videos average 85% retention because you master the psychology of attention.

Write a 20-minute true crime narration script about a REAL case from "{ct}".

ENGAGEMENT PSYCHOLOGY RULES (follow every one):
1. OPENING HOOK (first 30 seconds): Start mid-action with the most shocking moment. NOT "On a dark night..." Instead: "The 911 call came in at 3:47 AM. The caller was screaming. But what the police found when they arrived was something no one was prepared for."
2. Every 3-4 minutes, insert an INTERACTIVE QUESTION that makes viewers think: "Ask yourself — would you have opened that door?" / "Here's where most people make a wrong assumption..." / "Stop and guess — who do YOU think did it?"
3. Before EVERY section change, add a RETENTION HOOK: "But what happened next changes everything..." / "And this is where the story takes a turn no one expected..." / "The evidence was pointing one direction — until THIS was discovered..."
4. CURiosity GAPS: Reveal information slowly. Say "What police found next would haunt them forever" then DON'T reveal it immediately — let the tension build.
5. Use SPECIFIC DETAILS: Exact dates, times, addresses, temperatures, distances. "It was 11 degrees below zero on December 14th, 1997, when..." These feel researched and credible.
6. EMOTIONAL ANCHORING: Every 5 minutes, reconnect to the victim as a real person — their hobbies, their family, their last words. This is what separates 1M view videos from 100 view videos.
7. COMMENT BAIT (natural, not forced): "People still argue about this to this day in the comments..." / "I've read hundreds of comments on this case and most people miss one crucial detail..."
8. END with: "If this case unsettled you, wait until you hear next week's case. Subscribe and hit the bell — you won't want to miss it. And tell me in the comments: do you think justice was served?"

STRUCTURE with markers:
[HOOK] [INTRO] [BACKGROUND] [THE CRIME] [INVESTIGATION] [SUSPECTS] [RESOLUTION] [CONCLUSION]
Add [PAUSE] at dramatic moments. Add [SCENE CHANGE] between sections.

3000+ words. Real documented case. Output narration text only.""")

def gen_short(title):
    return call_llm(f"""You write YouTube Shorts that get 5M+ views. The secret? A question so provocative people CAN'T scroll past.

Write a 60-second Short about this true crime case: "{title}"

STRUCTURE:
- First line: A question that makes people stop scrolling. NOT a statement. "Would you trust your neighbor with a key to your house?" not "A neighbor had a key."
- Middle: The one most disturbing fact from the case, delivered with tension
- End: "What do YOU think? Tell me in the comments." (This drives engagement which boosts the algorithm)

140-170 words. [PAUSE] markers. Narration only. Dramatic tone.""")

def translate(script, code, name):
    return call_llm(f"""You are a professional translator who localizes YouTube content for maximum engagement in {name}.

Translate this true crime script. RULES:
- Keep the dramatic, suspenseful tone — don't make it sound like a textbook
- Preserve ALL markers: [HOOK] [INTRO] [BACKGROUND] [THE CRIME] [INVESTIGATION] [SUSPECTS] [RESOLUTION] [CONCLUSION] [PAUSE] [SCENE CHANGE]
- Keep proper nouns (names, places) in original form
- Adapt idioms naturally — don't translate word-for-word
- Keep ALL interactive questions and engagement hooks
- Maintain word count
- Output ONLY the translated text

SCRIPT:
{script}""")

def gen_meta(title, code, name, short=False):
    k = "YouTube Short under 60 seconds" if short else "20-minute true crime documentary"
    r = call_llm(f"""You are a YouTube SEO expert who gets videos to 10M+ views. You understand the algorithm, search ranking, and click psychology deeply.

Generate metadata in {name} for a {k}.
Working title reference: {title}

Output ONLY this JSON (no markdown, no explanation):
{{
  "title": "CURATED TITLE HERE",
  "description": "FULL DESCRIPTION HERE",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"],
  "pinned_comment": "ENGAGEMENT QUESTION HERE"
}}

TITLE RULES (most important for views):
- Under 60 characters for long videos, under 50 for Shorts
- Use a CURIOSITY GAP — make people NEED to click to satisfy their curiosity
- Bad: "The Murder of Jane Doe" (boring, no curiosity)
- Good: "The Clue Everyone Missed in the Jane Doe Case" (creates gap)
- Great: "Why Detectives Still Can't Solve This 30-Year-Old Case" (impossible not to click)
- Include one specific number (year, age, count) — numbers boost CTR by 15%
- NO clickbait — the video must deliver on the title's promise
- For Shorts: Start with a question mark

DESCRIPTION RULES:
- First 150 characters are CRITICAL — they show in YouTube search results. Must contain main keywords naturally
- Structure: Line 1-2 = hook with keywords. Line 3-4 = case summary with date/location. Line 5+ = details. Last 3 lines = hashtags + subscribe CTA
- Include 3-5 relevant hashtags at the end
- For long videos, include chapter timestamps (estimate based on typical structure):
  0:00 - Intro
  1:30 - Background
  4:30 - The Crime
  9:30 - The Investigation
  13:30 - The Suspects
  16:30 - The Resolution
  18:30 - Conclusion

TAGS RULES:
- Exactly 10 tags
- Mix: 3 broad (true crime, mystery, documentary) + 4 specific (case name, location, victim type) + 3 long-tail (phrases people actually search like "unsolved murder cases" "cold case mysteries solved")
- All text in {name} except proper nouns

PINNED COMMENT RULES:
- A question that creates DEBATE — people who disagree comment more than people who agree
- Reference one specific detail from the case to prove you did research
- End with a clear question mark
- Under 200 characters
- Example: "The blood evidence pointed to the husband, but the timeline doesn't work. I think someone else was in that house. What's YOUR theory?"
- All text in {name}""")

    return safe_json(r)

def extract_title(s):
    for l in s.split("\n"):
        c = l.replace("[HOOK]", "").strip()
        if c and len(c) > 10: return c[:100]
    return "True Crime Mystery"


# ==========================================
# MAIN
# ==========================================

def main():
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)

    provs = build_providers()
    # We filter out Pollinations for this check just to see if PAID keys exist, 
    # but the script will run anyway because Pollinations is added as a fallback.
    paid_provs = [p for p in provs if "Pollinations" not in p[0]]
    
    if not paid_provs:
        print("⚠️ WARNING: No PAID API keys found (Cerebras/Groq/Cohere/Gemini).")
        print("   Relying on FREE fallback (Pollinations-DeepSeek). Quality may vary.")

    ct = random.choice(CASE_CATEGORIES)
    print(f"Category: {ct}")

    print("\n[1/2] Generating long script (engagement-optimized)...")
    ls = gen_script(ct)
    wt = extract_title(ls)
    print(f"  Title: {wt}")
    print(f"  Words: {len(ls.split())}")
    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w") as f:
        f.write(ls)

    print("\n[2/2] Generating short script (comment-bait)...")
    ss = gen_short(wt)
    print(f"  Words: {len(ss.split())}")
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w") as f:
        f.write(ss)

    ac = list(LANGUAGES.keys())
    d = datetime.date.today().toordinal()
    sel = [ac[(d + i) % len(ac)] for i in range(LANGS_PER_RUN)]
    if "en" not in sel: sel[0] = "en"
    print(f"\nLanguages this run: {[LANGUAGES[c]['name'] for c in sel]}")

    am = {}
    for code in sel:
        info = LANGUAGES[code]
        print(f"\n--- {info['name']} ({code}) ---")
        if code == "en":
            lm = gen_meta(wt, code, info["name"], False)
            sm = gen_meta(wt, code, info["name"], True)
            am[code] = {"long": lm, "short": sm}
            print(f"  Title: {lm.get('title', '?')}")
            print(f"  Comment: {lm.get('pinned_comment', '?')[:80]}...")
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
            print(f"  Comment: {lm.get('pinned_comment', '?')[:80]}...")
        except Exception as e:
            print(f"  Failed: {e}")
        time.sleep(5)

    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(am, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(sel, f)

    print(f"\n{'=' * 50}")
    print(f"DONE — {len(am)} languages with SEO + engagement")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
