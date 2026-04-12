import os, json, random, datetime, time, re, requests
from config import *

# ==========================================
# LLM PROVIDERS
# ==========================================

def _cerebras_call(prompt, key):
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
    return requests.get(
        "https://text.pollinations.ai/",
        params={"prompt": prompt, "model": "openai", "seed": random.randint(0, 1000000)},
        timeout=180
    )

def _pollinations_parse(r): return r.text.strip()

def build_providers():
    p = []
    k = os.environ.get("CEREBRAS_API_KEY", "")
    if k: p.append(("Cerebras", lambda pr, key=k: _cerebras_call(pr, key), _cerebras_parse))
    k = os.environ.get("GROQ_API_KEY", "")
    if k: p.append(("Groq", lambda pr, key=k: _groq_call(pr, key), _groq_parse))
    k = os.environ.get("COHERE_API_KEY", "")
    if k: p.append(("Cohere", lambda pr, key=k: _cohere_call(pr, key), _cohere_parse))
    k = os.environ.get("GEMINI_API_KEY", "")
    if k:
        for m in ["gemini-1.5-flash", "gemini-1.5-pro"]:
            p.append((f"Gemini-{m}", lambda pr, key=k, md=m: _gemini_call(pr, key, md), _gemini_parse))
    p.append(("Pollinations-DeepSeek", lambda pr: _pollinations_call(pr), _pollinations_parse))
    return p

def call_llm(prompt, retries=3):
    providers = build_providers()
    print(f"Active Providers: {[p[0] for p in providers]}")
    
    for name, cfn, pfn in providers:
        for a in range(retries):
            try:
                r = cfn(prompt)
                if r.status_code == 429:
                    wait = min(120, 30 * (2 ** a) + random.uniform(0, 10))
                    print(f"    Rate limited ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif r.status_code in [401, 403]:
                    print(f"    ❌ Blocked/Invalid ({name})")
                    break
                elif r.status_code == 404:
                    print(f"    ⚠️ Unavailable ({name})")
                    break
                elif r.status_code != 200:
                    if a < retries - 1: time.sleep(10)
                    continue
                
                t = pfn(r)
                if len(t) < 20: raise Exception("Short response")
                print(f"    ✅ OK ({name})")
                return t
            except Exception as e:
                err = str(e).lower()
                if "429" in err or "quota" in err or "rate limit" in err:
                    wait = min(120, 30 * (2 ** a))
                    print(f"    Rate limited ({name}), waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                elif "401" in err or "403" in err or "invalid" in err:
                    print(f"    ❌ Blocked/Invalid ({name})")
                    break
                else:
                    if a < retries - 1: time.sleep(10)
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
    return call_llm(f"""You are a YouTube true crime narrator with 10M+ subscribers. Write a 20-minute true crime narration script about a REAL case from "{ct}". Start with a hook.
