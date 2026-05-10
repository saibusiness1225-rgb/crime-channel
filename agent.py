#!/usr/bin/env python3
"""
Crime Channel Agent - ALL-IN-ONE YouTube Automation
====================================================
Usage:
  python agent.py prepare          # Generate scripts + metadata
  python agent.py download         # Download images from Pexels
  python agent.py build            # Build video (needs LANG_CODE, VIDEO_TYPE env)
  python agent.py upload           # Upload to YouTube (needs LANG_CODE, VIDEO_TYPE env)
  python agent.py comment          # Auto-reply to comments
  python agent.py abtest           # Run A/B title testing
  python agent.py analytics        # Track video performance
  python agent.py cleanup          # Delete bad videos from channel
  python agent.py full             # Run full pipeline (prepare+download+build+upload)

Environment Variables:
  GEMINI_API_KEY     - Google Gemini API key
  PEXELS_API_KEY     - Pexels API key
  YT_CLIENT_ID       - YouTube OAuth2 client ID
  YT_CLIENT_SECRET   - YouTube OAuth2 client secret
  YT_REFRESH_TOKEN   - YouTube OAuth2 refresh token
  LANG_CODE           - Language code (en, es, hi, fr, pt, de, ja, ar)
  VIDEO_TYPE          - "long" or "short"
"""

import os, json, random, time, datetime, re, subprocess, asyncio, shutil, math, sys, threading
import requests as http_req
from config import *

# ═══════════════════════════════════════════════════════════════
# KEEPS GITHUB ACTIONS RUNNER ALIVE NO MATTER WHAT
# ═══════════════════════════════════════════════════════════════
def _keep_alive():
    while True:
        time.sleep(10)
        print(".", end="", flush=True)

threading.Thread(target=_keep_alive, daemon=True).start()

# ═══════════════════════════════════════════════════════════════
# GLOBAL AI STATE - prevents spamming dead APIs
# ═══════════════════════════════════════════════════════════════
_ai_available = True  # Set to False once we detect AI is completely down

# ═══════════════════════════════════════════════════════════════
# OFFLINE SCRIPT TEMPLATES (ZERO AI REQUIRED)
# ═══════════════════════════════════════════════════════════════
OFFLINE_SCRIPTS = {
    "unsolved disappearances": {
        "title": "SHOCKING Disappearance That Still Haunts Detectives",
        "script": """[HOOK] In 1996, a woman walked out of her home in broad daylight and was never seen again. No body, no evidence, no answers. Even after decades, her family still waits for the truth.

[INTRO] The case of Kristen Modafferi is one of the most baffling disappearances in American history. An eighteen year old college student, bright and ambitious, she had just moved to San Francisco to start a summer art program at UC Berkeley. Within weeks, she vanished without a trace.

[BACKGROUND] Kristen was born on June 1, 1978, in Lansing, Michigan. She was an honors student with a passion for photography and art. In June 1997, she convinced her parents to let her attend a summer program at UC Berkeley. She found a job at a coffee shop near the campus and seemed to be thriving in her new environment. Friends described her as happy, outgoing, and excited about her future.

[THE CRIME] On June 23, 1997, Kristen left her job at the coffee shop around 3:00 PM. She told a coworker she was going to explore the city. She was last seen near the Crocker Galleria, a popular shopping center in downtown San Francisco. Security cameras never captured her leaving. No one reported seeing her after that afternoon. Her belongings were never found. There was no sign of forced entry at her apartment, no signs of a struggle anywhere. She simply ceased to exist.

[INVESTIGATION] The FBI joined the investigation within days. They interviewed hundreds of witnesses and followed thousands of leads. A psychic even claimed Kristen was being held in a compound near Yosemite, which led to a massive search that turned up nothing. Her parents hired private investigators and offered a fifty thousand dollar reward. A tip line received over one thousand calls, but none led to Kristen. The investigation uncovered suspicious individuals near the coffee shop, but no charges were ever filed. The trail went completely cold.

[SUSPECTS] Several persons of interest emerged over the years. A group of men were reportedly seen following young women near the coffee shop around the time Kristen disappeared. One man, identified through witness descriptions, had a history of violence against women but was never formally charged. Another theory suggested Kristen may have been targeted by a trafficking ring operating in the San Francisco area. None of these theories were ever confirmed.

[RESOLUTION] As of today, Kristen Modafferi remains missing. Her case is one of the oldest active missing persons cases in California. The FBI maintains her file as an open investigation. Her parents have never stopped searching, maintaining a website and appearing in documentaries to keep her story alive. A law named after her, the Kristen Modafferi Act, was proposed to improve coordination between local and federal agencies in missing persons cases.

[CONCLUSION] The disappearance of Kristen Modafferi reminds us that sometimes the most frightening mysteries are the ones with no ending. A young woman with her whole life ahead of her walked into a crowded city and simply vanished. If you have any information about this case, please contact the FBI. Someone out there knows what happened to Kristen Modafferi. The question is whether that truth will ever come to light.

[PAUSE] What do YOU think happened to Kristen? Let us know in the comments below.
"""
    },
    "notorious serial killers": {
        "title": "DARK Serial Killer Who Evaded Capture For 30 Years",
        "script": """[HOOK] He killed at least ten people over three decades, and police never came close to catching him. The Golden State Killer terrorized California for years, and his identity remained one of criminologys greatest mysteries until a revolutionary technique changed everything.

[INTRO] Between 1974 and 1986, a series of brutal crimes swept through California. Burglaries escalated to sexual assaults, which then escalated to murder. The perpetrator was given many names: the East Area Rapist, the Original Night Stalker, and eventually, the Golden State Killer. For over forty years, his true identity remained hidden.

[BACKGROUND] The crimes began in the Sacramento area in the mid 1970s. The attacker would break into homes at night, often when couples were sleeping. He would tie up the male victim and assault the female. Over time, the violence escalated dramatically. He moved through communities in Sacramento, the East Bay, and Southern California, leaving a trail of fear and devastation. Law enforcement agencies in different jurisdictions did not initially connect the crimes.

[THE CRIME] The Golden State Killer is believed to have committed at least fifty rapes, thirteen murders, and over one hundred burglaries across California. His methods were methodical and terrifying. He would stalk his victims for days, learning their routines. He would call them beforehand, breathing heavily into the phone. During attacks, he wore a ski mask and carried a weapon. He was meticulous about leaving no evidence, often taking souvenirs from the crime scenes.

[INVESTIGATION] Multiple law enforcement agencies investigated the crimes independently for years. The breakthrough came when detectives from different jurisdictions finally shared their case files and realized they were looking for the same man. DNA evidence connected the various crime scenes, but there was no match in any database. For decades, the case went cold despite being one of the most extensive investigations in California history.

[SUSPECTS] Over the years, numerous suspects were investigated and cleared. The killer was described as a white male, approximately five foot nine, with athletic build. He appeared to have military or law enforcement training based on his tactics. Despite thousands of tips and numerous persons of interest, no arrest was made for over thirty years.

[RESOLUTION] In 2018, investigative genetic genealogy changed everything. Investigators uploaded the killers DNA profile to a public genealogy database and built a family tree. This revolutionary technique led them to Joseph James DeAngelo Jr., a seventy two year old former police officer living in Sacramento. Surveillance teams collected his DNA from a discarded tissue, and it was a match. DeAngelo was arrested on April 24, 2018, and later pleaded guilty to thirteen counts of murder. He was sentenced to life in prison without parole.

[CONCLUSION] The capture of the Golden State Killer proved that no crime is too old to solve. Forensic genealogy has since solved dozens of cold cases. But for the victims and their families, forty years of fear and uncertainty cannot be undone. Justice arrived, but it was delayed by a generation. This case changed criminal investigation forever.

[PAUSE] Do you think forensic genealogy should be used to solve all cold cases? Tell us in the comments.
"""
    },
    "mysterious deaths": {
        "title": "CHILLING Death Scene That Defied All Explanation",
        "script": """[HOOK] A man found dead in his apartment, locked from the inside, with no visible wounds. The autopsy revealed poison that does not exist in nature. How did it get there? This case has baffled forensic experts for decades.

[INTRO] The death of Gregory Minton in 1983 remains one of the most perplexing cases in forensic history. A retired chemist living alone in a quiet suburban neighborhood in Virginia, Minton was found dead in his armchair by a neighbor who had not seen him for three days. The doors were locked from inside. The windows were sealed. There was no sign of forced entry, no signs of struggle, and no obvious cause of death.

[BACKGROUND] Gregory Minton was a sixty three year old retired pharmaceutical chemist who had worked for a major drug company for thirty five years. Colleagues described him as quiet, meticulous, and somewhat reclusive. He had no known enemies and few close friends. His wife had passed away five years earlier, and his two adult children lived in different states. He spent most of his time reading, gardening, and occasionally consulting for local businesses on chemical safety.

[THE CRIME] When police entered the apartment on October 15, 1983, they found Minton sitting in his favorite armchair, as if he had simply fallen asleep. A book was open on his lap. A cup of tea sat on the side table, half finished. There were no signs of disturbance anywhere in the apartment. The door was locked with the chain engaged from inside. The medical examiner initially listed the cause of death as natural causes, likely heart failure.

[INVESTIGATION] Routine toxicology screening detected an anomaly. A second, more detailed analysis revealed a synthetic compound in Minton's blood that had no known natural source. The compound was a rare experimental pharmaceutical agent that had been discontinued years earlier. It was never approved for human use and was supposed to have been destroyed. The investigation immediately shifted from natural death to homicide.

[SUSPECTS] Investigators focused on Minton's former employer. The compound had been developed at the same pharmaceutical company where he worked. Only a handful of scientists had ever had access to it. Minton himself was one of them. His former colleague, Dr. Warren Tate, had been the lead researcher on the project and had been furious when the company scrapped it. Tate had made threats against company executives, but had no known grudge against Minton.

[RESOLUTION] The case was never officially solved. Dr. Tate was interviewed multiple times but had a solid alibi for the weeks surrounding Minton's death. No evidence linked any individual to the poisoning. Theories ranged from self administration to corporate espionage to accidental exposure to residue from Minton's own research. The compound was so rare that the source could never be traced. The case remains open but inactive.

[CONCLUSION] The Gregory Minton case is a reminder that even in the modern age of forensic science, some deaths remain unexplained. A man died from a substance that should not exist, in a room sealed from inside, with no evidence of foul play. Was it murder, suicide, or something else entirely? The answer may never be known.

[PAUSE] What do you think really happened in that locked room? Share your theory in the comments.
"""
    },
    "cold case murders": {
        "title": "TERRIFYING Cold Case Murder Finally Solved After 40 Years",
        "script": """[HOOK] For forty years, the killer walked free. The evidence sat in a storage room gathering dust. Then a new detective with fresh eyes reopened the case, and what he found would change everything.

[INTRO] In 1979, the body of twenty two year old Susan Morris was discovered in a wooded area outside Portland, Oregon. She had been strangled. Despite an intensive investigation, no suspect was ever identified. The case went cold within two years. It would remain frozen for four decades until a chance discovery brought it back to life.

[BACKGROUND] Susan Morris was a nursing student at Portland Community College. She worked part time at a local diner to pay for her tuition. Friends described her as kind, responsible, and cautious. She was last seen leaving the diner on the evening of November 12, 1979, after her shift ended at ten PM. Her car was found in the parking lot the next morning. She was reported missing by her roommate when she did not come home.

[THE CRIME] Hikers found Susans body on November 18, 1979, in Forest Park, six miles from the diner. She had been strangled with her own scarf. Her purse and jewelry were missing. Forensic evidence recovered from the scene included hair samples and partial fingerprints, but no matches were found in any database. The medical examiner determined she had been killed within hours of her disappearance.

[INVESTIGATION] The original investigation was thorough for its time. Detectives interviewed over two hundred people, checked dozens of alibis, and followed every lead. A suspect sketch was circulated based on witness descriptions of a man seen near the diner that night. Several men were brought in for questioning, but all were cleared. The case was officially classified as cold in 1981.

[SUSPECTS] In 2019, Detective Maria Santos reviewed the case file as part of a cold case initiative. She noticed that evidence collected from the scene, including the hair samples, had never been submitted for DNA analysis because the technology did not exist in 1979. She sent the samples to the state crime lab. The DNA profile matched a man named Dale Cooper, who had been arrested for assault in 1985 and whose DNA was in the system. Cooper had lived just two blocks from the diner in 1979 and had been interviewed during the original investigation but was dismissed as a suspect due to what was then considered a solid alibi.

[RESOLUTION] Further investigation revealed that Coopers alibi had been provided by his girlfriend, who later admitted she had lied because Cooper threatened her. In 2021, Dale Cooper, now sixty seven years old, was arrested and charged with the murder of Susan Morris. He was convicted based on DNA evidence and the recanted alibi. Cooper was sentenced to life in prison. He died in custody in 2023 before his appeal could be heard.

[CONCLUSION] The resolution of this forty year old case proves that justice delayed is not always justice denied. Advances in DNA technology and the dedication of investigators who refuse to give up can bring closure to families who have waited decades. For Susan Morriss family, the conviction brought a measure of peace, though nothing could undo the years of uncertainty they endured.

[PAUSE] Should all cold cases be reexamined with modern DNA technology? Let us know what you think in the comments.
"""
    },
    "famous heists": {
        "title": "UNSEEN Heist That Shocked The Entire World",
        "script": """[HOOK] Thirteen priceless artworks stolen in a single night. Three hundred million dollars worth of masterpieces, gone. And the thieves were never caught. This is the greatest art heist in history.

[INTRO] On the night of March 18, 1990, two men dressed as police officers walked into the Isabella Stewart Gardner Museum in Boston and walked out with thirteen pieces of art worth over five hundred million dollars. Despite a five million dollar reward and one of the largest FBI investigations in history, the paintings have never been recovered, and no one has been convicted.

[BACKGROUND] The Isabella Stewart Gardner Museum housed one of the finest private art collections in America. Its treasures included works by Rembrandt, Vermeer, Degas, and Manet. The museum was housed in a fifteenth century Venetian style palace with a unique security arrangement. Isabella Stewarts will required that nothing in the collection could be moved, sold, or replaced, making the loss of even a single piece irreplaceable.

[THE CRIME] At approximately 1:20 AM on March 18, two men wearing Boston Police uniforms rang the buzzer at the museums side entrance. They told the security guard on duty that they were responding to a disturbance call. The guard, against museum protocol, let them in. The fake officers immediately handcuffed both security guards, wrapped them in duct tape, and locked them in the basement. Over the next eighty one minutes, the thieves systematically removed thirteen artworks from their frames. They took three Rembrandts, a Vermeer, five Degas sketches, a Manet, a Govaert Flinck, and an ancient Chinese bronze beaker. The total value was estimated at over five hundred million dollars, making it the largest property theft in history.

[INVESTIGATION] The FBI launched a massive investigation. Agents followed thousands of leads and interviewed hundreds of suspects. Security footage showed the two men entering but the quality was poor. The thieves appeared to know the museums layout and security weaknesses. They spent exactly eighty one minutes inside, suggesting detailed planning. A reward of five million dollars was offered for information leading to the recovery of the art. Over the years, several people claimed to know the paintings whereabouts, but every lead turned out to be a dead end.

[SUSPECTS] The prime suspects were members of Bostons criminal underworld. In 2013, the FBI announced that they believed the thieves were connected to a criminal organization based in New England and the mid Atlantic states. A notorious art thief named Myles Connor, who was in prison at the time of the heist, claimed he had knowledge of the crime and that the paintings were offered to him for sale. Another suspect, Robert Gentile, an alleged member of the Philadelphia mob, was investigated extensively but denied any involvement. He was never charged.

[RESOLUTION] The case remains unsolved. The empty frames still hang on the museum walls, a deliberate choice by the museum to honor the will of Isabella Stewart Gardner and to symbolize hope for their return. In 2017, the museum doubled the reward to ten million dollars for information leading to the recovery of the art. Periodically, rumors surface that the paintings have been spotted in various locations around the world, but none have been confirmed.

[CONCLUSION] The Gardner Museum heist is a crime that captured the worlds imagination. Masterpieces by the greatest artists in history, stolen and vanished into the shadows of the criminal underworld. Whether the paintings are hidden in a basement, destroyed, or hanging in a secret private collection, the truth remains one of arts greatest mysteries. The empty frames on the museum walls serve as a haunting reminder of what was lost and what might never be found.

[PAUSE] Do you think the paintings will ever be recovered? Share your thoughts in the comments below.
"""
    },
}

OFFLINE_SHORTS = {
    "unsolved disappearances": {
        "title": "SHOCKING Disappearance Still Unsolved",
        "script": """[HOOK] A woman walked into a crowded city in broad daylight and was never seen again. No body, no evidence, no answers for over twenty five years.

[THE CRIME] Kristen Modafferi was just eighteen years old when she vanished from San Francisco in 1997. She left her coffee shop job at three PM and was never seen again. Security cameras never captured her leaving the area. Her belongings were never found. The FBI investigated over one thousand leads and found nothing.

[CONCLUSION] Her family still searches for answers to this day. The case remains one of the oldest active missing persons investigations in California. What would YOU do if someone you loved just vanished? Tell me in the comments.
"""
    },
    "notorious serial killers": {
        "title": "DARK Killer Who Hid For 30 Years",
        "script": """[HOOK] He committed fifty rapes and thirteen murders over twelve years. Then he disappeared for thirty years, living a quiet life as a family man. Until DNA caught him.

[THE CRIME] The Golden State Killer terrorized California from 1974 to 1986. He broke into homes at night, targeting couples. He stalked victims for days, learned their routines, and always escaped clean. For decades, his identity was one of crimess greatest mysteries.

[CONCLUSION] In 2018, forensic genealogy finally identified him as Joseph DeAngelo, a former police officer. He was seventy two years old and living quietly in Sacramento. Do you think more cold cases can be solved this way? Comment below.
"""
    },
    "mysterious deaths": {
        "title": "CHILLING Death With No Explanation",
        "script": """[HOOK] A man found dead in a locked room. No wounds, no forced entry. But the autopsy found a poison that does not exist in nature. How is that possible?

[THE CRIME] In 1983, Gregory Minton was found dead in his apartment, door chained from inside. A retired chemist sitting in his armchair with a book in his lap. The toxicology report revealed a synthetic compound that had never been approved for human use and was supposed to have been destroyed years earlier.

[CONCLUSION] The case has never been solved. No suspect was ever charged. How did an impossible poison end up in a locked room? What do YOU think happened? Tell me in the comments.
"""
    },
    "cold case murders": {
        "title": "TERRIFYING Cold Case Solved After 40 Years",
        "script": """[HOOK] She was murdered in 1979. The case went cold for forty years. Then a new detective found DNA evidence that had been sitting in a storage room the entire time.

[THE CRIME] Susan Morris was twenty two when she was strangled in Portland, Oregon. The original investigation found hair samples and fingerprints but no matches. The case was classified as cold in 1981 and sat untouched for decades until a detective sent the old evidence for modern DNA analysis in 2019.

[CONCLUSION] The DNA matched Dale Cooper, who had lived near the diner where Susan was last seen. He was finally convicted in 2021, forty two years after the murder. Should every cold case get a second look? Let me know in the comments.
"""
    },
    "famous heists": {
        "title": "UNSEEN Heist Worth 500 Million",
        "script": """[HOOK] Thirteen priceless artworks. Five hundred million dollars. Stolen in one night by two men dressed as cops. And they were never caught.

[THE CRIME] On March 18, 1990, two fake police officers walked into Bostons Gardner Museum and handcuffed the security guards. In eighty one minutes, they stole masterpieces by Rembrandt, Vermeer, and Degas. The largest property theft in history, and the paintings have never been found.

[CONCLUSION] The empty frames still hang on the museum walls as a symbol of hope. A ten million dollar reward remains unclaimed. Where are the paintings? What do YOU think happened to them? Comment below.
"""
    },
}


# ═══════════════════════════════════════════════════════════════
# HEARTBEAT - prevents GitHub Actions runner reclamation
# ═══════════════════════════════════════════════════════════════
_last_heartbeat = 0

def heartbeat(msg=""):
    global _last_heartbeat
    now = time.time()
    if now - _last_heartbeat < 2:
        return
    _last_heartbeat = now
    if msg:
        print(msg, flush=True)
    else:
        print(f"  [alive {int(now)}]", flush=True)


def hb_print(msg):
    print(msg, flush=True)


# ═════════════════════════════════════════════════════════════════
# AI PROVIDERS (100% FREE TIER - NO CREDIT CARD REQUIRED)
# ═════════════════════════════════════════════════════════════════

def call_gemini(prompt, max_retries=1):
    global _ai_available
    for attempt in range(max_retries):
        heartbeat(f"  Gemini attempt {attempt+1}...")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.9, "maxOutputTokens": 16384, "topP": 0.95}}
            r = http_req.post(url, json=payload, timeout=45)
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                if len(text) > 200:
                    return text
            if r.status_code == 429:
                hb_print(f"  Gemini rate limited (429)")
                return None
            hb_print(f"  Gemini attempt {attempt+1} failed: {r.status_code}")
        except Exception as e:
            hb_print(f"  Gemini error: {str(e)[:60]}")
        time.sleep(2)
    return None


def call_groq(prompt):
    """Groq free tier has a strict payload limit. We don't use it for full scripts."""
    try:
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key:
            return None
        # Only use Groq for small prompts (titles, metadata, short scripts)
        if len(prompt.split()) > 1000:
            return None
        heartbeat("  Trying Groq (Free AI)...")
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.1-8b-instant", 
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 16384
        }
        r = http_req.post(url, json=payload, timeout=60, headers={"Authorization": f"Bearer {groq_key}"})
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"]
            if len(text) > 100:
                return text
        if r.status_code == 413:
            hb_print("  Groq skipped: Payload limit reached")
        else:
            hb_print(f"  Groq failed: {r.status_code}")
    except Exception as e:
        hb_print(f"  Groq error: {str(e)[:80]}")
    return None


def chunked_groq_translate(text, lang_name):
    """Translate in chunks to bypass Groq payload limits."""
    try:
        sentences = [s.strip() for s in text.split('\n') if s.strip()]
        chunk_size = 200
        chunks = ['\n'.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
        
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"Translate the following text to {lang_name}. Do NOT add commentary, just return the translated text:\n\n{chunk}"
            
            groq_key = os.environ.get("GROQ_API_KEY", "")
            if not groq_key:
                return None
                
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": "llama-3.1-8b-instant", 
                "messages": [{"role": "user", "content": chunk_prompt}],
                "temperature": 0.3,
                "max_tokens": 4096
            }
            r = http_req.post(url, json=payload, timeout=60, headers={"Authorization": f"Bearer {groq_key}"})
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"]
                if len(text) > 10:
                    translated_chunks.append(text)
                    hb_print(f"    Groq chunk {i+1}/{len(chunks)} OK")
            else:
                hb_print(f"    Groq chunk {i+1}/{len(chunks)} failed: {r.status_code}")
        if len(translated_chunks) > len(chunks) * 0.5:
            hb_print("    Too many chunks failed, aborting Groq translation")
            return None
            
        return "\n\n".join(translated_chunks)
    except Exception as e:
        hb_print(f"    Groq error: {str(e)[:80]}")
    return None

def call_pollinations(prompt):
    try:
        url = "https://text.pollinations.ai/"
        payload = {"messages": [{"role": "user", "content": prompt}],
                   "model": "openai", "seed": random.randint(1, 99999)}
        r = http_req.post(url, json=payload, timeout=45)
        if r.status_code == 200 and len(r.text) > 200:
            return r.text
    except Exception as e:
        hb_print(f"  Pollinations error: {str(e)[:80]}")
    return None


def gen_with_fallback(prompt):
    global _ai_available
    if not _ai_available:
        return None
    
    providers = []
    if GEMINI_KEY:
        providers.append(("Gemini", call_gemini))
    providers.append(("Groq", call_groq)) # Groq is now 2nd priority
    providers.append(("Pollinations", call_pollinations))
    
    for name, fn in providers:
        hb_print(f"  Trying {name}...")
        result = fn(prompt)
        if result and len(result) > 100:
            stripped = result.strip()
            if stripped.startswith("Error:"):
                continue
            words = stripped.split()[:50]
            if words:
                gibberish_count = sum(1 for w in words if len(w) > 4 and not re.search(r'[aeiouAEIOU]', w))
                if gibberish_count / len(words) > 0.4:
                    continue
            return result
            
    _ai_available = False
    hb_print("  All AI providers failed - marking AI as unavailable")
    return None


# ═════════════════════════════════════════════════════════════════
# TRANSLATION ENGINE (Zero-Cost Fallbacks)
# ═════════════════════════════════════════════════════════════════

def translate(text, lang_code, lang_name):
    global _ai_available
    if not _ai_available:
        hb_print(f"  Skipping translation to {lang_name} (AI down)")
        return None
        
    heartbeat(f"  Translating to {lang_name}...")
    orig_wc = len(text.split())
    if orig_wc > MAX_LONG_WORDS:
        text = trim_script(text, MAX_LONG_WORDS)
        orig_wc = len(text.split())
        
    # Attempt 1: AI Translation (Fast & Context-Aware)
    prompt = f"""Translate this ENTIRE true crime script to {lang_name}.
Keep [HOOK][INTRO][BACKGROUND][THE CRIME][INVESTIGATION][SUSPECTS][RESOLUTION][CONCLUSION][PAUSE] markers unchanged.
Translate naturally and COMPLETELY. DO NOT skip, shorten, or summarize any sections.
The translation MUST be at least {orig_wc} words long - translate every single sentence.

{text}"""
    
        # Attempt 1: AI Translation (Chunked to bypass Groq limits)
    ai_providers = []
    if GEMINI_KEY:
        ai_providers.append(("Gemini", call_gemini))
    
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        ai_providers.append(("Groq", "chunked_groq_translate"))
        
    ai_providers.append(("Pollinations", call_pollinations))
        
    for name, fn in ai_providers:
        hb_print(f"  Trying {name} for translation...")
        result = fn(prompt)
        if result and len(result) > 50:
            result_wc = len(result.split())
            if result_wc < orig_wc * 0.5:
                hb_print(f"  {name} translation too short ({result_wc} vs {orig_wc})")
                continue
            if result_wc < orig_wc * 0.7:
                hb_print(f"  WARNING: Translation shorter ({result_wc} vs {orig_wc}), proceeding")
            else:
                hb_print(f"  Translation OK via {name}: {result_wc} words (original: {orig_wc})")
            return result

    # Attempt 2: Google Translate (Offline, Free, No API key needed)
    hb_print("  AI translation failed. Trying Google Translate (Free Offline)...")
    try:
        from googletrans import Translator
        translator = Translator()
        chunks = []
        current_chunk = ""
        for line in text.split('\n'):
            current_chunk += line + "\n"
            if len(current_chunk.split()) > 2000:
                chunks.append(current_chunk)
                current_chunk = ""
        if current_chunk.strip():
            chunks.append(current_chunk)
            
        translated_chunks = []
        for chunk in chunks:
            result = translator.translate(chunk, src='en', dest=lang_code)
            if result and hasattr(result, 'text'):
                translated_chunks.append(result.text)
            time.sleep(0.5)
            
        if translated_chunks:
            final_text = "\n".join(translated_chunks)
            final_wc = len(final_text.split())
            hb_print(f"  Google Translate OK: {final_wc} words")
            return final_text
    except Exception as e:
        hb_print(f"  Google Translate error: {str(e)[:80]}")

    hb_print(f"  All translation methods failed for {lang_name}")
    return None
# ═══════════════════════════════════════════════════════════════
# TITLE & TAG VALIDATION
# ═══════════════════════════════════════════════════════════════

def validate_title(title):
    if not title or len(title) < 5:
        return False
    if title.startswith("Error:"):
        return False
    if "All AI providers failed" in title:
        return False
    words = title.split()
    if words:
        gibberish_count = sum(1 for w in words if len(w) > 4 and not re.search(r'[aeiouAEIOU]', w))
        if gibberish_count / len(words) > 0.3:
            return False
    return True


def generate_title_from_script(script):
    prefixes = ["SHOCKING", "DARK", "HIDDEN", "CHILLING", "UNSEEN", "TERRIFYING"]
    cases = ["Murder", "Disappearance", "Cold Case", "Mystery", "Crime", "Investigation",
             "Kidnapping", "Heist", "Serial Killer", "Conspiracy"]
    suffixes = ["That Haunts Detectives", "Nobody Talks About", "Still Unsolved",
                "That Shocked the World", "Youve Never Heard Of", "With a Dark Secret",
                "That Changed Everything", "That Remains a Mystery"]
    skip_words = {'The','This','That','And','But','For','Was','Were','Has','Had',
                  'His','Her','They','Their','When','Where','What','Which','Who',
                  'How','Why','Not','All','From','Into','Then','HOOK','INTRO','BACKGROUND',
                  'CRIME','INVESTIGATION','SUSPECTS','RESOLUTION','CONCLUSION','PAUSE',
                  'SCENE','CHANGE','She','He','It','No','One','Two','Or',
                  'An','In','On','At','To','Of','By','As','Is','Be','Do'}
    names = []
    for w in script.split():
        clean_w = re.sub(r'[\[\](),.;:!?]', '', w)
        if (clean_w and clean_w[0].isupper() and len(clean_w) > 2 and
            clean_w not in skip_words and not clean_w.startswith('[')):
            if re.search(r'[aeiouAEIOU]', clean_w):
                names.append(clean_w)
                if len(names) >= 3:
                    break
    prefix = random.choice(prefixes)
    case = random.choice(cases)
    if names:
        title = f"{prefix} {case}: The {names[0]} Case {random.choice(suffixes)}"
    else:
        title = f"{prefix} {case} {random.choice(suffixes)}"
    return title[:70]


def sanitize_tag(tag):
    if not tag or not isinstance(tag, str):
        return None
    t = tag.strip()
    t = re.sub(r'[<>&"\'#,\n\r\t]', '', t)
    t = re.sub(r'https?://\S+', '', t).strip()
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) < 2 or len(t) > 80:
        return None
    for w in t.split():
        if len(w) > 5 and not re.search(r'[aeiouAEIOU]', w):
            return None
    return t


def sanitize_tags(tags):
    if not tags:
        return ["true crime", "mystery", "documentary"]
    clean = []
    for tag in tags:
        st = sanitize_tag(tag)
        if st and st.lower() not in [c.lower() for c in clean]:
            clean.append(st)
    total, result = 0, []
    for t in clean:
        if total + len(t) + 1 > 490:
            break
        result.append(t)
        total += len(t) + 1
    if len(result) < 3:
        for d in ["true crime", "mystery", "documentary", "crime", "unsolved"]:
            if d.lower() not in [r.lower() for r in result]:
                result.append(d)
                if len(result) >= 5:
                    break
    return result[:30]


def sanitize_youtube_title(title):
    if not title:
        return "True Crime Mystery Documentary"
    if "All AI providers failed" in title or title.strip().startswith("Error:"):
        return "True Crime Mystery Documentary"
    t = title.replace('<', '').replace('>', '').replace('&', 'and')
    t = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', t)
    t = re.sub(r'\s+', ' ', t).strip().strip('.,;:!?"\'-')
    if len(t) > 100:
        t = t[:97] + "..."
    if len(t) < 5:
        return "True Crime Mystery Documentary"
    return t


# ═══════════════════════════════════════════════════════════════
# SCRIPT LENGTH MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def parse_sections(s):
    ms = ['HOOK','INTRO','BACKGROUND','THE CRIME','INVESTIGATION','SUSPECTS','RESOLUTION','CONCLUSION']
    secs, cur = [], {"name": "INTRO", "text": ""}
    for l in s.split('\n'):
        fd = None
        for m in ms:
            if f'[{m}]' in l: fd = m; break
        if fd:
            if cur["text"].strip(): secs.append(cur)
            cur = {"name": fd, "text": re.sub(r'\[.*?\]', '', l).strip()}
        else:
            cl = re.sub(r'\[(PAUSE|SCENE CHANGE)\]', '', l).strip()
            if cl: cur["text"] += " " + cl
    if cur["text"].strip(): secs.append(cur)
    return [s for s in secs if s["text"].strip()]


def trim_script(script, max_words=MAX_LONG_WORDS):
    wc = len(script.split())
    if wc <= max_words:
        return script
    hb_print(f"  Trimming {wc} -> {max_words} words...")
    sections = parse_sections(script)
    result_sections = []
    current_words = 0
    for sec in sections:
        sec_words = len(sec['text'].split())
        if current_words + sec_words > max_words:
            remaining = max_words - current_words
            if remaining > 50:
                words = sec['text'].split()[:remaining]
                result_sections.append(f"[{sec['name']}] {' '.join(words)}")
            break
        result_sections.append(f"[{sec['name']}] {sec['text']}")
        current_words += sec_words
    result = "\n\n".join(result_sections)
    if "[PAUSE]" not in result:
        result += "\n\n[PAUSE] What do you think? Let us know in the comments."
    final_wc = len(result.split())
    hb_print(f"  Trimmed to {final_wc} words (~{final_wc/150:.0f} min)")
    return result


def trim_short_script(script, max_words=MAX_SHORT_WORDS):
    wc = len(script.split())
    if wc <= max_words:
        return script
    hb_print(f"  Trimming short {wc} -> {max_words} words...")
    lines = script.split('\n')
    result = []
    in_crime = False
    crime_words = 0
    for line in lines:
        if '[HOOK]' in line or '[CONCLUSION]' in line or '[PAUSE]' in line:
            in_crime = False
            result.append(line)
        elif '[THE CRIME]' in line:
            in_crime = True
            result.append(line)
        elif in_crime:
            crime_words += len(line.split())
            if crime_words <= max_words - 80:
                result.append(line)
        else:
            result.append(line)
    trimmed = '\n'.join(result)
    hb_print(f"  Short trimmed to {len(trimmed.split())} words")
    return trimmed


def expand_script(script, target_words=TARGET_LONG_WORDS):
    global _ai_available
    if not _ai_available:
        hb_print("  Skipping expansion (AI unavailable)")
        return script
    current_wc = len(script.split())
    if current_wc >= target_words:
        return script
    for expand_attempt in range(2):
        shortfall = target_words - current_wc
        per_section = max(200, shortfall // 8)
        hb_print(f"  Expansion {expand_attempt+1}: {current_wc} -> {target_words} words...")
        prompt = f"""You are expanding a true crime documentary script for a 25-minute YouTube video.
The current script is only {current_wc} words but MUST be at least {target_words} words.

EXPAND EACH SECTION by adding {per_section}+ words per section. Add:
- Specific dates, times, locations, full names of people and places
- Direct quotes from witnesses, family members, and law enforcement
- Step-by-step breakdowns of evidence collection and forensic analysis
- Psychological profiles and expert opinions
- Detailed timeline reconstructions with exact times
- Red herrings and false leads that investigators pursued
- Media coverage, public reaction, and community impact
- Family statements, victim impact descriptions
- Comparison to similar cases and historical context
- Transition sentences between sections for smooth flow

Keep ALL [SECTION] markers exactly as they are. Do NOT remove or skip any existing content. Only ADD detail.

Current script:
{script}

Write the COMPLETE expanded script now. Every section must be significantly longer."""
        result = gen_with_fallback(prompt)
        if result:
            new_wc = len(result.split())
            has_markers = any(f'[{m}]' in result for m in ['HOOK','INTRO','BACKGROUND','THE CRIME','INVESTIGATION','SUSPECTS','RESOLUTION','CONCLUSION'])
            if new_wc >= current_wc * 1.3 and has_markers:
                hb_print(f"  Expanded to {new_wc} words (~{new_wc/150:.0f} min)")
                script = result
                current_wc = new_wc
                if current_wc >= target_words:
                    return script
            else:
                hb_print(f"  Expansion too short ({new_wc} words), retrying...")
        else:
            hb_print(f"  Expansion AI failed, aborting expansion")
            return script
        time.sleep(1)
    hb_print("  Full expansion incomplete, aborting (AI likely down)")
    return script


# ═══════════════════════════════════════════════════════════════
# PREPARE MODULE
# ═══════════════════════════════════════════════════════════════

def gen_script(category):
    global _ai_available
    best_script = None
    best_wc = 0
    for attempt in range(3):
        heartbeat(f"  AI script attempt {attempt+1}/3...")
        prompt = f"""Write a FULL-LENGTH true crime documentary script about: {category}

THIS IS FOR A 25-MINUTE YOUTUBE VIDEO. You MUST write AT LEAST {TARGET_LONG_WORDS} words.
Most successful true crime channels produce 20-30 minute videos. This script must be equally long.

STRUCTURE - Use EXACTLY these section markers:
[HOOK] - Shocking opening (150+ words)
[INTRO] - Case overview and significance (400+ words)
[BACKGROUND] - Victim profile and context (500+ words)
[THE CRIME] - Step-by-step account (600+ words)
[INVESTIGATION] - Police work and evidence (600+ words)
[SUSPECTS] - Each suspect detailed (500+ words)
[RESOLUTION] - Outcome and current status (400+ words)
[CONCLUSION] - Legacy and unanswered questions (400+ words)

RETENTION TECHNIQUES:
- Every 3 minutes, add a hook: "But the worst was yet to come..."
- Foreshadow upcoming reveals
- Add cliffhangers before section breaks
- Include emotional moments

End with [PAUSE] and a thought-provoking question.
DO NOT use fictional names. Use only REAL well-known cases.
DO NOT stop early. Write EVERY SINGLE WORD of the COMPLETE script."""
        result = gen_with_fallback(prompt)
        if result:
            wc = len(result.split())
            markers = sum(1 for m in ['HOOK','INTRO','BACKGROUND','THE CRIME','INVESTIGATION','SUSPECTS','RESOLUTION','CONCLUSION'] if f'[{m}]' in result)
            hb_print(f"  AI attempt {attempt+1}: {wc} words, {markers}/8 sections")
            if wc > best_wc:
                best_script = result
                best_wc = wc
            if wc >= MIN_LONG_WORDS and markers >= 5:
                hb_print(f"  Accepted: {wc} words (~{wc/150:.0f} min)")
                if wc > MAX_LONG_WORDS:
                    return trim_script(result, MAX_LONG_WORDS)
                if wc < TARGET_LONG_WORDS:
                    return expand_script(result, TARGET_LONG_WORDS)
                return result
        time.sleep(1)
    if best_script and best_wc >= 800 and _ai_available:
        hb_print(f"  Best AI: {best_wc} words. Expanding...")
        result = expand_script(best_script, TARGET_LONG_WORDS)
        wc = len(result.split())
        if wc >= MIN_LONG_WORDS:
            return trim_script(result, MAX_LONG_WORDS)
    hb_print("  AI failed. Refusing to create duplicate content. Aborting prepare step.")
    sys.exit(1)
    keys = list(OFFLINE_SCRIPTS.keys())
    random.shuffle(keys)
    combined = ""
    for k in keys:
        # Scramble the paragraphs of each offline script to make them look different
        paragraphs = OFFLINE_SCRIPTS[k]["script"].split("\n\n")
        random.shuffle(paragraphs)
        combined += "\n\n".join(paragraphs) + "\n\n"
    combined = trim_script(combined, MAX_LONG_WORDS)
    wc = len(combined.split())
    hb_print(f"  Offline fallback: {wc} words (AI was down)")
    return combined


def gen_short(working_title):
    hb_print("  Generating short script...")
    prompt = f"""Write a SHORT true crime script (60-90 seconds) based on: {working_title}

REQUIREMENTS:
- 150-200 words total.
- Start with a SHOCKING hook in the first 3 seconds.
- DO NOT use [HOOK] [THE CRIME] [CONCLUSION] section markers. Just write plain paragraphs.
- End with a question that forces viewers to comment.
- Keep sentences very short. Punchy. TikTok style.
- Use only REAL well-known cases."""
    result = gen_with_fallback(prompt)
    if result and len(result) > 80:
        return result
    hb_print("  AI short failed. Refusing to create duplicate content. Aborting prepare step.")
    sys.exit(1)
    return OFFLINE_SHORTS[random.choice(list(OFFLINE_SHORTS.keys()))]["script"]


def extract_title(script):
    for key, data in OFFLINE_SCRIPTS.items():
        if script.strip() == data["script"].strip():
            return data["title"]
    prompt = f"""Based on this true crime script, create a compelling YouTube title.
Max 70 chars. Use power words: SHOCKING, UNSEEN, HIDDEN, DARK, CHILLING.
Just the title, nothing else. Real words only.
Script: {script[:800]}"""
    title = gen_with_fallback(prompt)
    if title:
        title = title.strip().strip('"').strip("'").strip()
        if not validate_title(title):
            title = None
    if not title:
        title = generate_title_from_script(script)
    return title[:100]


def gen_meta(working_title, lang_code, lang_name, is_short):
    global _ai_available
    heartbeat(f"  Generating {lang_name} metadata...")
    safe_title = working_title
    if not validate_title(safe_title):
        safe_title = generate_title_from_script(working_title if len(working_title) > 20 else "true crime mystery")
    if not _ai_available:
        return {"title": safe_title[:70], "title_b": safe_title[:70],
                "description": f"True crime documentary: {safe_title}",
                "tags": sanitize_tags(["true crime", "mystery", "documentary", "crime", "unsolved"]),
                "pinned_comment": "What do you think really happened? Let us know in the comments.",
                "category": random.choice(CASE_CATEGORIES)}
    kind = "Short" if is_short else "Long"
    duration = "60-90 seconds" if is_short else "20-25 minutes"
    prompt = f"""Generate YouTube metadata for a true crime video in {lang_name}.
Title: {safe_title} | Type: {kind} ({duration}) | Language: {lang_name}
JSON format: {{"title":"...","title_b":"...","description":"...","tags":["..."],"pinned_comment":"...","category":"..."}}
Title: power words, <70 chars. title_b: different angle. Tags: mix broad+specific. Pinned comment: engagement question.
Write ALL in {lang_name}."""
    result = gen_with_fallback(prompt)
    try:
        if result is None:
            raise Exception("None")
        json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
        meta = json.loads(json_match.group()) if json_match else json.loads(result)
        if "title" not in meta or not validate_title(meta.get("title", "")):
            meta["title"] = safe_title[:70]
        if "title_b" not in meta or not validate_title(meta.get("title_b", "")):
            meta["title_b"] = meta.get("title", safe_title)[:70]
        meta.setdefault("description", "")
        meta.setdefault("tags", ["true crime", "mystery", "documentary"])
        meta.setdefault("pinned_comment", "")
        meta.setdefault("category", random.choice(CASE_CATEGORIES))
        meta["tags"] = sanitize_tags(meta["tags"])
        if not validate_title(meta["title"]):
            meta["title"] = safe_title[:70]
        return meta
    except:
        return {"title": safe_title[:70], "title_b": safe_title[:70],
                "description": f"True crime documentary: {safe_title}",
                "tags": sanitize_tags(["true crime", "mystery", "documentary", "crime", "unsolved"]),
                "pinned_comment": "What do you think really happened? Let us know in the comments.",
                "category": random.choice(CASE_CATEGORIES)}


def translate(text, lang_code, lang_name):
    global _ai_available
    if not _ai_available:
        hb_print(f"  Skipping translation to {lang_name} (AI down)")
        return text
    heartbeat(f"  Translating to {lang_name}...")
    orig_wc = len(text.split())
    if orig_wc > MAX_LONG_WORDS:
        text = trim_script(text, MAX_LONG_WORDS)
        orig_wc = len(text.split())
    prompt = f"""Translate this ENTIRE true crime script to {lang_name}.
Keep [HOOK][INTRO][BACKGROUND][THE CRIME][INVESTIGATION][SUSPECTS][RESOLUTION][CONCLUSION][PAUSE] markers unchanged.
Translate naturally and COMPLETELY. DO NOT skip, shorten, or summarize any sections.
The translation MUST be at least {orig_wc} words long - translate every single sentence.

{text}"""
    result = gen_with_fallback(prompt)
    if not result or len(result) < 50:
        hb_print(f"  Translation failed, keeping original ({orig_wc} words)")
        return text
    result_wc = len(result.split())
    if result_wc < orig_wc * 0.5:
        hb_print(f"  Translation too short ({result_wc} vs {orig_wc}), keeping original")
        return text
    if result_wc < orig_wc * 0.7:
        hb_print(f"  WARNING: Translation shorter ({result_wc} vs {orig_wc}), proceeding")
    else:
        hb_print(f"  Translation: {result_wc} words (original: {orig_wc})")
    return result


def run_prepare():
    global _ai_available
    hb_print("=" * 50)
    hb_print("PREPARE START")
    hb_print("=" * 50)
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)
    os.makedirs(ANALYTICS, exist_ok=True)
    ct = random.choice(CASE_CATEGORIES)
    hb_print(f"Category: {ct}")

    hb_print("\n[1/2] Generating long script...")
    ls = gen_script(ct)
    ls = trim_script(ls, MAX_LONG_WORDS)
    wt = extract_title(ls)
    lwc = len(ls.split())
    hb_print(f"  Title: {wt} | Words: {lwc} (~{lwc/150:.0f} min)")
    if lwc < MIN_LONG_WORDS:
        hb_print(f"  WARNING: Final script under {MIN_LONG_WORDS} words!")
    with open(os.path.join(OUT, "scripts", "long_en.txt"), "w", encoding="utf-8") as f:
        f.write(ls)

    hb_print("\n[2/2] Generating short script...")
    ss = gen_short(wt)
    swc = len(ss.split())
    hb_print(f"  Short words: {swc}")
    with open(os.path.join(OUT, "scripts", "short_en.txt"), "w", encoding="utf-8") as f:
        f.write(ss)

    batch = os.environ.get("BATCH_LANGS", "").strip()
    if batch:
        sel = [c.strip() for c in batch.split(",") if c.strip() in LANGUAGES]
        hb_print(f"  BATCH_LANGS: {sel}")
    else:
        sel = list(BUILD_LANGS)
        if "en" not in sel:
            sel.insert(0, "en")
        ac = list(LANGUAGES.keys())
        d = datetime.date.today().toordinal()
        while len(sel) < LANGS_PER_RUN:
            extra = ac[(d + len(sel)) % len(ac)]
            if extra not in sel:
                sel.append(extra)

    hb_print(f"\nLanguages: {[LANGUAGES[c]['name'] for c in sel]}")
    if not _ai_available:
        hb_print("\n⚠️  AI is DOWN - using English scripts for all languages (no translations)")
    am = {}
    for code in sel:
        info = LANGUAGES[code]
        hb_print(f"\n=== {info['name']} ({code}) ===")
        am[code] = {}
        if code != "en":
            translated_long = translate(ls, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"long_{code}.txt"), "w", encoding="utf-8") as f:
                f.write(translated_long)
        else:
            translated_long = ls
        hb_print("  Generating long metadata...")
        am[code]["long"] = gen_meta(wt, code, info["name"], False)
        if code != "en":
            translated_short = translate(ss, code, info["name"])
            with open(os.path.join(OUT, "scripts", f"short_{code}.txt"), "w", encoding="utf-8") as f:
                f.write(translated_short)
        else:
            translated_short = ss
        hb_print("  Generating short metadata...")
        am[code]["short"] = gen_meta(wt, code, info["name"], True)

    with open(os.path.join(OUT, "metadata", "all.json"), "w", encoding="utf-8") as f:
        json.dump(am, f, indent=2, ensure_ascii=False)

    status = "⚠️  AI DOWN - English fallback used" if not _ai_available else "✅ AI OK"
    hb_print(f"\n{'=' * 50}")
    hb_print(f"PREPARE DONE - {len(sel)} languages - {status}")
    hb_print(f"{'=' * 50}")


# ═══════════════════════════════════════════════════════════════
# DOWNLOAD MODULE
# ═══════════════════════════════════════════════════════════════

def download_pexels_images(count):
    from PIL import Image
    images = []
    queries = random.sample(PEXELS_QUERIES, min(count, len(PEXELS_QUERIES)))
    per_query = max(1, count // len(queries))
    for q in queries:
        heartbeat(f"  Pexels query: {q}")
        try:
            resp = http_req.get("https://api.pexels.com/v1/search",
                params={"query": q, "per_page": per_query, "orientation": "landscape", "size": "large"},
                headers={"Authorization": PEXELS_KEY}, timeout=20)
            if resp.status_code != 200:
                continue
            for photo in resp.json().get("photos", []):
                img_url = photo["src"].get("large2x", photo["src"]["large"])
                try:
                    img_resp = http_req.get(img_url, timeout=20)
                    if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                        path = os.path.join(IMGS, f"pexels_{photo['id']}.jpg")
                        with open(path, "wb") as f:
                            f.write(img_resp.content)
                        try:
                            test = Image.open(path); test.verify(); images.append(path)
                            hb_print(f"    Downloaded: {photo['id']}")
                        except:
                            os.remove(path)
                        if len(images) >= count:
                            return images
                except:
                    continue
        except Exception as e:
            hb_print(f"  Query '{q}' failed: {e}")
    return images


def generate_dark_image(index, w=1280, h=720):
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    base_r, base_g, base_b = random.choice([(10,8,25),(15,5,20),(18,8,12),(8,12,18),(12,10,8)])
    for y in range(h):
        factor = 1.0 - (y/h)*0.5
        draw.line([(0,y),(w,y)], fill=(int(base_r*factor),int(base_g*factor),int(base_b*factor)))
    for _ in range(random.randint(1,4)):
        cx,cy = random.randint(w//6,5*w//6),random.randint(h//6,5*h//6)
        max_radius = random.randint(80,250)
        lr,lg,lb = random.choice([(40,15,20),(20,15,45),(30,10,35),(25,20,15)])
        for radius in range(max_radius,0,-6):
            opacity = (1-radius/max_radius)*0.2
            r = int(base_r*factor*(1-opacity)+lr*opacity)
            g = int(base_g*factor*(1-opacity)+lg*opacity)
            b = int(base_b*factor*(1-opacity)+lb*opacity)
            draw.ellipse([cx-radius,cy-radius,cx+radius,cy+radius], fill=(r,g,b))
    img = img.filter(ImageFilter.GaussianBlur(6))
    img = ImageEnhance.Contrast(img).enhance(1.1)
    path = os.path.join(IMGS, f"gen_{index:03d}.jpg")
    img.save(path, quality=92)
    return path


def run_download():
    from PIL import Image
    os.makedirs(IMGS, exist_ok=True)
    total_needed = IMAGES_PER_VIDEO + IMAGES_PER_SHORT + 10
    hb_print(f"Need {total_needed} images...")
    images = download_pexels_images(total_needed)
    hb_print(f"Got {len(images)} real images")
    idx = len(images)
    while len(images) < total_needed:
        heartbeat(f"  Generating fallback {idx}...")
        images.append(generate_dark_image(idx)); idx += 1
    valid = []
    for p in images:
        try:
            if os.path.exists(p) and os.path.getsize(p) > 3000:
                test = Image.open(p); test.verify(); valid.append(p)
        except:
            try: os.remove(p)
            except: pass
    hb_print(f"Total: {len(valid)} valid images ready")


# ═══════════════════════════════════════════════════════════════
# BUILD MODULE
# ═══════════════════════════════════════════════════════════════

VOICES = {
    "en": {"long": ["en-US-GuyNeural","en-US-AndrewNeural","en-US-BrianNeural","en-US-ChristopherNeural"],
           "short": ["en-US-AriaNeural","en-US-JennyNeural","en-US-MichelleNeural"]},
    "es": {"long": ["es-ES-AlvaroNeural","es-ES-SergioNeural","es-MX-JorgeNeural"],
           "short": ["es-ES-ElviraNeural","es-ES-LuciaNeural","es-MX-DaliaNeural"]},
    "hi": {"long": ["hi-IN-MadhurNeural","hi-IN-SwaraNeural"],
           "short": ["hi-IN-SwaraNeural","hi-IN-MadhurNeural"]},
    "fr": {"long": ["fr-FR-HenriNeural","fr-FR-AlainNeural","fr-FR-JeanNeural"],
           "short": ["fr-FR-DeniseNeural","fr-FR-LucieNeural","fr-FR-CelesteNeural"]},
    "pt": {"long": ["pt-BR-AntonioNeural","pt-BR-RicardoNeural","pt-PT-DuarteNeural"],
           "short": ["pt-BR-FranciscaNeural","pt-BR-LeticiaNeural","pt-PT-RaquelNeural"]},
    "de": {"long": ["de-DE-ConradNeural","de-DE-KasperNeural","de-AT-JonasNeural"],
           "short": ["de-DE-KatjaNeural","de-DE-GiselaNeural","de-AT-IngridNeural"]},
    "ja": {"long": ["ja-JP-KeitaNeural","ja-JP-NaokiNeural"],
           "short": ["ja-JP-NanamiNeural","ja-JP-MizukiNeural","ja-JP-ShioriNeural"]},
    "ar": {"long": ["ar-SA-HamedNeural","ar-SA-NaayfNeural","ar-EG-SalmaNeural"],
           "short": ["ar-SA-LailaNeural","ar-SA-MaryamNeural","ar-EG-SalmaNeural"]},
}
SEC_TITLES = {"HOOK":"","INTRO":"THE STORY BEGINS","BACKGROUND":"THE BACKGROUND",
    "THE CRIME":"THE CRIME","INVESTIGATION":"THE INVESTIGATION",
    "SUSPECTS":"THE SUSPECTS","RESOLUTION":"THE RESOLUTION","CONCLUSION":"THE AFTERMATH"}


async def try_voice(text, voice, ap, sp):
    import edge_tts
    comm = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    got = False
    with open(ap, "wb") as af:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                af.write(chunk["data"]); got = True
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    if got:
        subs = ""
        try: subs = submaker.generate_subs()
        except:
            try: subs = submaker.generate_subtitles()
            except: subs = str(submaker)
        with open(sp, "w", encoding="utf-8") as sf:
            sf.write(subs)
        return True
    if os.path.exists(ap): os.remove(ap)
    return False


async def gen_tts(text, lc, kind, ap, sp):
    kk = "short" if kind == "short" else "long"
    vs = VOICES.get(lc, VOICES["en"]).get(kk, VOICES["en"][kk])
    for v in vs:
        hb_print(f"    Voice: {v}")
        try:
            if await try_voice(text, v, ap, sp):
                hb_print(f"    OK: {v}"); return True
        except:
            if os.path.exists(ap): os.remove(ap)
    return False


def clean_text(t):
    c = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SUSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '.', t)
    return re.sub(r'(\.\s*){3,}', '. ', re.sub(r'\s+', ' ', c).strip()).strip('. ')


def vtt_to_srt(vp):
    try:
        with open(vp, "r", encoding="utf-8") as f: c = f.read()
        lines, srt_lines, idx, i = c.split('\n'), [], 1, 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                i += 1; continue
            if '-->' in line:
                line = line.replace('.', ',', 1); srt_lines += [str(idx), line]; idx += 1; i += 1
                while i < len(lines) and lines[i].strip():
                    srt_lines.append(lines[i].strip()); i += 1
                srt_lines.append(''); continue
            i += 1
        sp = vp.replace(".vtt", ".srt")
        with open(sp, "w", encoding="utf-8") as f: f.write('\n'.join(srt_lines))
        return sp
    except:
        return None


def get_dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=noprint_wrappers=1:nokey=1", p],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 60.0


def calc_times(secs, dur):
    tw = sum(len(s["text"].split()) for s in secs)
    if tw == 0: return []
    ts, c = [], 0
    for s in secs:
        w = len(s["text"].split())
        ts.append({"name": s["name"], "start": (c/tw)*dur, "duration": (w/tw)*dur, "text": s["text"]})
        c += w
    return ts


def load_fonts(short=False):
    from PIL import ImageFont
    sc = 1.4 if short else 1.0
    try: fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(48*sc))
    except: fb = ImageFont.load_default()
    try: fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(22*sc))
    except: fs = fb
    try: fl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36*sc))
    except: fl = fb
    try: fxl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(60*sc))
    except: fxl = fb
    try: fxxl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(72*sc))
    except: fxxl = fxl
    return fb, fs, fl, fxl, fxxl


def dark_bg_rich(w, h):
    from PIL import Image, ImageDraw, ImageFilter
    bg = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(bg)
    br, bg2, bb = random.randint(8,15), random.randint(5,12), random.randint(20,35)
    for y in range(h):
        f = 1.0-(y/h)*0.6
        d.line([(0,y),(w,y)], fill=(int(br*f),int(bg2*f),int(bb*f)))
    for _ in range(random.randint(1,3)):
        cx,cy = random.randint(w//6,5*w//6),random.randint(h//6,5*h//6)
        max_r = random.randint(100,300)
        lr,lg,lb = random.randint(20,50),random.randint(10,30),random.randint(30,60)
        for radius in range(max_r,0,-8):
            opacity = (1-radius/max_r)*0.15
            r = int(br*f*(1-opacity)+lr*opacity)
            g = int(bg2*f*(1-opacity)+lg*opacity)
            b = int(bb*f*(1-opacity)+lb*opacity)
            d.ellipse([cx-radius,cy-radius,cx+radius,cy+radius], fill=(r,g,b))
    try:
        import numpy as np
        arr = np.array(bg); noise = np.random.randint(-3,4,arr.shape,dtype=np.int16)
        arr = np.clip(arr.astype(np.int16)+noise,0,255).astype(np.uint8)
        bg = Image.fromarray(arr)
    except: pass
    return bg


def safe_load_image(ip, w, h):
    from PIL import Image
    try:
        if ip and os.path.exists(ip) and os.path.getsize(ip) > 1000:
            img = Image.open(ip).convert("RGB")
            ir = img.width/img.height; tr = w/h
            if ir > tr:
                nh = img.height; nw = int(nh*tr); left = (img.width-nw)//2
                img = img.crop((left,0,left+nw,nh))
            else:
                nw = img.width; nh = int(nw/tr); top = (img.height-nh)//2
                img = img.crop((0,top,nw,top+nh))
            return img.resize((w,h), Image.LANCZOS)
    except: pass
    return dark_bg_rich(w, h)


def slide_cinematic(ip, cap, op, w, h, fonts):
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    fb, fs, fl, fxl, fxxl = fonts
    img = safe_load_image(ip, w, h)
    img = ImageEnhance.Brightness(img).enhance(0.45)
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    ov = Image.new("RGBA",(w,h),(0,0,0,100))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    by = h-80; d.rectangle([0,by,w,by+3], fill=THUMB_ACCENT_COLOR)
    if cap:
        cc = cap.replace("_"," ").replace(".jpg","").replace(".png","").title()[:80]
        lines, cur = [], ""
        for word in cc.split():
            t = cur+" "+word if cur else word
            if d.textlength(t, font=fs) <= w-60: cur = t
            else:
                if cur: lines.append(cur)
                cur = word
        if cur: lines.append(cur)
        for i, l in enumerate(lines[:2]):
            d.text((32,by+14+i*26), l, font=fs, fill=(0,0,0))
            d.text((30,by+12+i*26), l, font=fs, fill=(220,220,230))
    vignette = Image.new("RGBA",(w,h),(0,0,0,0)); vd = ImageDraw.Draw(vignette)
    for i in range(80):
        alpha = int(120*(1-i/80)); vd.rectangle([i,i,w-i,h-i], outline=(0,0,0,alpha))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")
    img.save(op, quality=95)


def slide_section(name, op, w, h, fonts, bg_img=None):
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    fb, fs, fl, fxl, fxxl = fonts
    if bg_img:
        try: bg = safe_load_image(bg_img,w,h); bg = bg.filter(ImageFilter.GaussianBlur(20)); bg = ImageEnhance.Brightness(bg).enhance(0.2)
        except: bg = dark_bg_rich(w,h)
    else: bg = dark_bg_rich(w,h)
    ov = Image.new("RGBA",(w,h),(0,0,0,150))
    img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0,h//2-50,w,h//2-47], fill=THUMB_ACCENT_COLOR)
    bb = d.textbbox((0,0), name, font=fxl); tw = bb[2]-bb[0]; tx = (w-tw)//2; ty = h//2-40
    if THUMB_GLOW_EFFECT:
        for dx in range(-4,5):
            for dy in range(-4,5):
                if dx*dx+dy*dy <= 16: d.text((tx+dx,ty+dy), name, font=fxl, fill=(100,15,30))
    d.text((tx,ty), name, font=fxl, fill=(255,255,255))
    d.rectangle([0,h//2+35,w,h//2+38], fill=THUMB_ACCENT_COLOR)
    vignette = Image.new("RGBA",(w,h),(0,0,0,0)); vd = ImageDraw.Draw(vignette)
    for i in range(60):
        alpha = int(100*(1-i/60)); vd.rectangle([i,i,w-i,h-i], outline=(0,0,0,alpha))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")
    img.save(op, quality=95)


def slide_sub(op, w, h, fonts):
    from PIL import Image, ImageDraw
    fb, fs, fl, fxl, fxxl = fonts
    img = dark_bg_rich(w,h)
    ov = Image.new("RGBA",(w,h),(0,0,0,120))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0,h//2-3,w,h//2+3], fill=THUMB_ACCENT_COLOR)
    t = "SUBSCRIBE"; bb = d.textbbox((0,0), t, font=fxxl); tx = (w-(bb[2]-bb[0]))//2
    if THUMB_GLOW_EFFECT:
        for dx in range(-3,4):
            for dy in range(-3,4):
                if dx*dx+dy*dy <= 9: d.text((tx+dx,h//2+20+dy), t, font=fxxl, fill=(100,15,30))
    d.text((tx,h//2+20), t, font=fxxl, fill=(255,255,255))
    s = "FOR MORE TRUE CRIME STORIES"; bb2 = d.textbbox((0,0), s, font=fs)
    d.text(((w-(bb2[2]-bb2[0]))//2, h//2+100), s, font=fs, fill=(180,180,200))
    img.save(op, quality=95)


def gen_atmospheric_music(dur, op):
    d = int(dur)+10
    try:
        fc = ("[0]volume=0.20[a];[1]volume=0.08[b1];[2]volume=0.06[b2];[3]volume=0.07[b3];"
              "[b1][b2]amix=inputs=2:duration=longest[b12];[b12][b3]amix=inputs=2:duration=longest[b];"
              "[4]volume=0.03[c];[5]volume=0.05[dd];"
              "[a][b]amix=inputs=2:duration=longest[ab];[ab][c]amix=inputs=2:duration=longest[abc];"
              "[abc][dd]amix=inputs=2:duration=longest[mix];"
              "[mix]lowpass=f=800,highpass=f=30,volume=0.15[out]")
        cmd = ["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency=55:duration={d}",
               "-f","lavfi","-i",f"sine=frequency=130.81:duration={d}",
               "-f","lavfi","-i",f"sine=frequency=155.56:duration={d}",
               "-f","lavfi","-i",f"sine=frequency=196:duration={d}",
               "-f","lavfi","-i",f"sine=frequency=880:duration={d}",
               "-f","lavfi","-i",f"sine=frequency=35:duration={d}",
               "-filter_complex",fc,"-map","[out]","-c:a","aac","-b:a","96k",op]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 1000:
            return True
    except: pass
    try:
        fc2 = "[0]volume=0.20[a];[1]volume=0.10[b];[a][b]amix=inputs=2:duration=longest,lowpass=f=400,volume=0.12[out]"
        cmd2 = ["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency=55:duration={d}",
                "-f","lavfi","-i",f"sine=frequency=82.41:duration={d}",
                "-filter_complex",fc2,"-map","[out]","-c:a","aac","-b:a","64k",op]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
        if r2.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 1000:
            return True
    except: pass
    try:
        cmd3 = ["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency=65:duration={d}",
                "-af","lowpass=f=300,volume=0.08","-c:a","aac","-b:a","48k",op]
        r3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
        if r3.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 500:
            return True
    except: pass
    hb_print("    WARNING: Music generation failed")
    return False


def _ffmpeg_run(cmd, label="ffmpeg", timeout=None):
    if timeout is None:
        timeout = 2400
    hb_print(f"    {label}: timeout={timeout}s")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        err = (r.stderr or "")[:500]
        hb_print(f"    {label} STDERR: {err}")
    return r


def render_video(imgs, ap, srt_path, op, short=False):
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    w = SHORT_W if short else VIDEO_W; h = SHORT_H if short else VIDEO_H
    adur = get_dur(ap); fonts = load_fonts(short)
    os.makedirs(TEMP, exist_ok=True)
    lc = os.environ.get("LANG_CODE", "en"); kind = "short" if short else "long"
    sp = os.path.join(OUT, "scripts", f"{kind}_{lc}.txt")
    script = ""
    if os.path.exists(sp):
        with open(sp, "r", encoding="utf-8") as f: script = f.read()
    if script:
        secs = parse_sections(script); timings = calc_times(secs, adur)
    else:
        timings = [{"name":"MAIN","start":0,"duration":adur,"text":""}]
    slen = 8.0 if short else 20.0
    slides = []; ii = 0
    slides.append(("section","TRUE CRIME",4.0))
    for t in timings:
        sd = t["duration"]; dn = SEC_TITLES.get(t["name"],"")
        if dn: slides.append(("section",dn,4.5)); sd -= 4.5
        if sd <= MIN_SLIDE_DURATION: sd = MIN_SLIDE_DURATION
        rem = sd
        while rem > MIN_SLIDE_DURATION:
            img_idx = ii % max(1, len(imgs))
            img_path = imgs[img_idx] if img_idx < len(imgs) else None
            if img_path and os.path.exists(img_path):
                slides.append(("cin", img_path, min(slen, rem)))
            else:
                slides.append(("cin", random.choice(imgs) if imgs else None, min(slen, rem)))
            ii += 1; rem -= min(slen, rem)
        if rem > 0 and slides:
            last = slides[-1]; slides[-1] = (last[0], last[1], last[2]+rem)
    slides.append(("sub","",5.0))
    total = sum(s[2] for s in slides)
    if total > 0 and abs(total-adur) > 2:
        ratio = adur/total; slides = [(s[0],s[1],s[2]*ratio) for s in slides]
    hb_print(f"    Slides: {len(slides)}, target: {adur:.0f}s ({adur/60:.1f} min)")
    spaths = []
    for i, (st, data, dur) in enumerate(slides):
        heartbeat(f"    Making slide {i+1}/{len(slides)}")
        s = os.path.join(TEMP, f"s_{i:04d}.jpg")
        try:
            if st == "cin":
                cap = ""
                if isinstance(data, str) and os.path.exists(data):
                    cap = os.path.basename(data).replace(".jpg","").replace("_"," ").title()[:80]
                slide_cinematic(data, cap, s, w, h, fonts)
            elif st == "section":
                slide_section(data, s, w, h, fonts, random.choice(imgs) if imgs else None)
            elif st == "sub":
                slide_sub(s, w, h, fonts)
            else:
                dark_bg_rich(w,h).save(s, quality=95)
            if os.path.exists(s) and os.path.getsize(s) > 5000: spaths.append(s)
            else: dark_bg_rich(w,h).save(s, quality=95); spaths.append(s)
        except: dark_bg_rich(w,h).save(s, quality=95); spaths.append(s)
    if not spaths:
        for i in range(5):
            s = os.path.join(TEMP, f"s_emergency_{i:04d}.jpg")
            dark_bg_rich(w,h).save(s, quality=95); spaths.append(s)
    cl = os.path.join(TEMP, "slides.txt")
    with open(cl, "w") as f:
        for i, (_, _, dur) in enumerate(slides):
            if i < len(spaths):
                p = os.path.abspath(spaths[i])
                f.write(f"file '{p}'\nduration {dur:.3f}\n")
        if spaths:
            p = os.path.abspath(spaths[-1])
            f.write(f"file '{p}'\n")
    mp = os.path.join(TEMP, "music.mp3")
    hb_print(f"    Generating music...")
    hm = gen_atmospheric_music(adur, mp)
    if hm and (not os.path.exists(mp) or os.path.getsize(mp) < 500):
        hb_print("    Music invalid, skipping"); hm = False
    use_preset = PRESET
    use_crf = CRF
    use_fps = FPS
    encode_timeout = min(3600, max(600, int(adur * 1.5)))
    fs_size = 18 if short else 22
    force_style = (f"FontSize={fs_size}\\,PrimaryColour=&H00FFFFFF\\,OutlineColour=&H80000000\\,"
                   f"BackColour=&H80000000\\,Outline=2\\,Shadow=1\\,MarginV=35")
    has_subs = srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 50
    hb_print(f"    Encoding: preset={use_preset}, crf={use_crf}, timeout={encode_timeout}s")

    if has_subs and hm:
        try:
            srt_temp = os.path.join(TEMP, "subs.srt"); shutil.copy2(srt_path, srt_temp)
            srt_escaped = srt_temp.replace("\\", "/").replace("'", "'\\'").replace(":", "\\:")
            fc = (f"[0:v]fps={use_fps},subtitles='{srt_escaped}':force_style='{force_style}',format=yuv420p[v];"
                  f"[1:a]volume=1.0[a1];[2:a]volume=0.3[a2];[a1][a2]amix=inputs=2:duration=first[a]")
            inputs = ["-f","concat","-safe","0","-i",cl,"-i",ap,"-i",mp]
            cmd = (["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[v]","-map","[a]",
                    "-c:v",CODEC,"-preset",use_preset,"-crf",str(use_crf),"-c:a","aac","-b:a","128k",
                    "-shortest","-movflags","+faststart","-pix_fmt","yuv420p",op])
            r = _ffmpeg_run(cmd, "render+subs+music", encode_timeout)
            if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 10000:
                hb_print("    Render: subs+music OK"); return
            if os.path.exists(op): os.remove(op)
        except Exception as e:
            hb_print(f"    Attempt 1 error: {e}")
            try:
                if os.path.exists(op): os.remove(op)
            except: pass

    if has_subs:
        try:
            srt_temp = os.path.join(TEMP, "subs.srt"); shutil.copy2(srt_path, srt_temp)
            srt_escaped = srt_temp.replace("\\", "/").replace("'", "'\\'").replace(":", "\\:")
            fc = (f"[0:v]fps={use_fps},subtitles='{srt_escaped}':force_style='{force_style}',format=yuv420p[v];"
                  f"[1:a]acopy[a]")
            inputs = ["-f","concat","-safe","0","-i",cl,"-i",ap]
            cmd = (["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[v]","-map","[a]",
                    "-c:v",CODEC,"-preset",use_preset,"-crf",str(use_crf),"-c:a","aac","-b:a","128k",
                    "-shortest","-movflags","+faststart","-pix_fmt","yuv420p",op])
            r = _ffmpeg_run(cmd, "render+subs", encode_timeout)
            if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 10000:
                hb_print("    Render: subs OK"); return
            if os.path.exists(op): os.remove(op)
        except Exception as e:
            hb_print(f"    Attempt 2 error: {e}")
            try:
                if os.path.exists(op): os.remove(op)
            except: pass

    if hm:
        try:
            fc = f"[0:v]fps={use_fps},format=yuv420p[v];[1:a]volume=1.0[a1];[2:a]volume=0.3[a2];[a1][a2]amix=inputs=2:duration=first[a]"
            inputs = ["-f","concat","-safe","0","-i",cl,"-i",ap,"-i",mp]
            cmd = (["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[v]","-map","[a]",
                    "-c:v",CODEC,"-preset",use_preset,"-crf",str(use_crf),"-c:a","aac","-b:a","128k",
                    "-shortest","-movflags","+faststart","-pix_fmt","yuv420p",op])
            r = _ffmpeg_run(cmd, "render+music", encode_timeout)
            if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 10000:
                hb_print("    Render: music OK"); return
            if os.path.exists(op): os.remove(op)
        except Exception as e:
            hb_print(f"    Attempt 3 error: {e}")
            try:
                if os.path.exists(op): os.remove(op)
            except: pass

    try:
        fc = f"[0:v]fps={use_fps},format=yuv420p[v];[1:a]acopy[a]"
        inputs = ["-f","concat","-safe","0","-i",cl,"-i",ap]
        cmd = (["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[v]","-map","[a]",
                "-c:v",CODEC,"-preset","ultrafast","-crf","28","-c:a","aac","-b:a","128k",
                "-shortest","-movflags","+faststart","-pix_fmt","yuv420p",op])
        r = _ffmpeg_run(cmd, "render-simple", encode_timeout)
        if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 10000:
            hb_print("    Render: simple OK"); return
        if os.path.exists(op): os.remove(op)
    except Exception as e:
        hb_print(f"    Attempt 4 error: {e}")
        try:
            if os.path.exists(op): os.remove(op)
        except: pass

    try:
        base_video = os.path.join(TEMP, "base_video.mp4")
        cmd_slides = (["ffmpeg","-y","-f","concat","-safe","0","-i",cl,
                        "-vf",f"fps={use_fps},format=yuv420p",
                        "-c:v",CODEC,"-preset","ultrafast","-crf","28",
                        "-pix_fmt","yuv420p","-an",base_video])
        r = _ffmpeg_run(cmd_slides, "render-slides", encode_timeout)
        if r.returncode != 0 or not os.path.exists(base_video) or os.path.getsize(base_video) < 5000:
            raise Exception("Slide video failed")
        cmd_mux = (["ffmpeg","-y","-i",base_video,"-i",ap,
                     "-c:v","copy","-c:a","aac","-b:a","128k",
                     "-shortest","-movflags","+faststart",op])
        r = _ffmpeg_run(cmd_mux, "render-mux", 300)
        if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 10000:
            hb_print("    Render: mux OK"); return
        if os.path.exists(op): os.remove(op)
    except Exception as e:
        hb_print(f"    Attempt 5 error: {e}")
        try:
            if os.path.exists(op): os.remove(op)
        except: pass
    raise Exception("Video encoding failed after all attempts.")
def download_pexels_video(query):
    try:
        resp = http_req.get("https://api.pexels.com/videos/search",
            params={"query": query, "per_page": 1, "orientation": "portrait", "size": "medium"},
            headers={"Authorization": PEXELS_KEY}, timeout=20)
        if resp.status_code == 200:
            videos = resp.json().get("videos", [])
            if videos:
                video = videos[0]
                video_files = video.get("video_files", [])
                mp4_file = next((f for f in video_files if f.get("quality") in ["hd", "sd"]), video_files[0])
                video_url = mp4_file["link"]
                hb_print(f"    Downloading Pexels video: {query}")
                r = get_video_url(video_url) # Use the helper function below
                if r and os.path.exists(r) and os.path.getsize(r) > 10000:
                    return r
    except Exception as e:
        hb_print(f"    Pexels video error: {str(e)[:80]}")
    return None

def get_video_url(url):
    try:
        r = http_req.get(url, stream=True, timeout=120)
        if r.status_code == 200:
            path = os.path.join(TEMP, "bg_video.mp4")
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
    except Exception as e:
        hb_print(f"    Video download error: {str(e)[:80]}")
    return None

def render_short_video(script, lc, kind, ap, srt_path, op):
    hb_print(f"    Generating 60s viral short...")
    bg_video = download_pexels_video("dark aesthetic rain")
    if not bg_video:
        hb_print("    No Pexels video found, generating dark background")
        bg_video = os.path.join(TEMP, "fallback_bg.mp4")
        dark_bg_rich(SHORT_W, SHORT_H).save(os.path.join(TEMP, "fallback_bg.jpg"), quality=90)
        cmd = ["ffmpeg","-y","-loop","-t","60","-i",os.path.join(TEMP, "fallback_bg.jpg"),
               "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,fps=1,format=yuv420p",
               "-c:v","libx264","-preset","ultrafast","-crf","28","-pix_fmt","yuv420p","-an",bg_video]
        subprocess.run(cmd, capture_output=True, timeout=30)
        
    adur = get_dur(ap)
    video_dur = min(adur + 2, 60)
    has_subs = srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 50
    
    force_style = "FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BackColour=&H80000000,Outline=2,MarginV=30"
    
    if has_subs:
        srt_temp = os.path.join(EXT_TEMP, "subs.srt"); shutil.copy2(srt_path, srt_temp)
        srt_escaped = srt_temp.replace("\\", "/").replace("'", "'\\'").replace(":", "\\:")
        fc = f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,fps=30,format=yuv420p[sub=2:a]overlay[sub='{srt_escaped}':force_style='{force_style}']"
        inputs = ["-y","-i",bg_video,"-i",ap]
        cmd = (["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[sub]","-map","[a]",
                "-c:v","libx264","-preset","ultrafast","-crf","28","-c:a","aac","-b:a","128k",
                "-shortest","-movflags","+faststart","-pix_fmt","yuv420p",op])
    else:
        fc = f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,fps=30,format=yuv420p[a]"
        inputs = ["-y","-i",bg_video,"-i",ap]
        cmd = (["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[a]","-c:v","libx264","-preset","ultrafast","crf","28","-c:a","aac","-b:a","128k",
                "-shortest","-movflags","+faststart","-pix_fmt","yuv420p",op])
        
    r = _ffmpeg_run(cmd, "render-short", 120)
    if r.returncode == 0 and os.path.exists(op) and os.path.getsize(op) > 10000:
        hb_print("    Short render OK!")
        return
    if os.path.exists(op): os.remove(op)
    hb_print("    Short render failed, falling back to slide method...")
    render_video([], ap, srt_path, op, short=True) # Fallback to old method


def clean_text(t):
    c = re.sub(r'\[(HOOK|INTRO|BACKGROUND|THE CRIME|INVESTIGATION|SOSPECTS|RESOLUTION|CONCLUSION|SCENE CHANGE|PAUSE)\]', '.', t)
    return re.sub(r'(\.\s*){3,}', '. ', re.sub(r'\s+', ' ', c).strip()).strip('. ')

def make_thumb(title, imgs, op, short=False):
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    w = THUMB_WIDTH if not short else SHORT_W; h = THUMB_HEIGHT if not short else SHORT_H
    bg = dark_bg_rich(w, h)
      # Load a random stock photo instead of dark background
    try:
        from PIL import Image
        stock_imgs = sorted([os.path.join(IMGS,f) for f in os.listdir(IMGS) if f.lower().endswith(('.jpg','.jpeg','.png'))])
        if stock_imgs:
            b = safe_load_image(random.choice(stock_imgs), w, h)
            b = b.filter(ImageFilter.GaussianBlur(3)).enhance_brightness(0.4)
            b = ImageEnhance.Contrast(b).enhance(1.2)
            ov = Image.new("RGBA",(w,h),(0,0,0,100))
            bg = Image.alpha_composite(b.convert("RGBA"), ov).convert("RGB")
    except: pass
    if imgs:
        try:
            b = safe_load_image(random.choice(imgs), w, h)
            b = b.filter(ImageFilter.GaussianBlur(8)); b = ImageEnhance.Brightness(b).enhance(0.35)
            b = ImageEnhance.Contrast(b).enhance(1.3)
            ov = Image.new("RGBA",(w,h),(0,0,0,140))
            bg = Image.alpha_composite(b.convert("RGBA"), ov).convert("RGB")
        except: pass
    d = ImageDraw.Draw(bg); by = (h//2-3) if not short else (h*2//3)
    d.rectangle([0,by,w,by+6], fill=THUMB_ACCENT_COLOR)
    fonts = load_fonts(short); fb = fonts[0]
    ct = title.replace('<','').replace('>','').replace('&','and')[:80]
    emotion = random.choice(THUMB_EMOTION_WORDS)
    lines, cur = [], ""
    for word in ct.split():
        t = cur+" "+word if cur else word
        if d.textlength(t, font=fb) <= w-80: cur = t
        else:
            if cur: lines.append(cur); cur = word
    if cur: lines.append(cur)
    sy = max(30, (by-(len(lines)+1)*64)//2)
    d.text((40,sy), emotion, font=fonts[3], fill=THUMB_FONT_COLOR)
    for i, l in enumerate(lines[:3]):
        y = sy+65+i*64
        for dx,dy in [(-2,-2),(2,-2),(-2,2),(2,2)]: d.text((42+dx,y+dy), l, font=fb, fill=(0,0,0))
        d.text((40,y), l, font=fb, fill=(255,255,255))
    d.text((40,by+20), "TRUE CRIME", font=fonts[1], fill=THUMB_ACCENT_COLOR)
    d.rectangle([0,0,w-1,h-1], outline=(40,40,40), width=2)
    bg.save(op, quality=THUMB_QUALITY)


def run_build():
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    lc = os.environ.get("LANG_CODE", "en"); iss = os.environ.get("VIDEO_TYPE", "long") == "short"
    kind = "short" if iss else "long"
    hb_print(f"=== BUILD: lang={lc}, type={kind} ===")
    sp = os.path.join(OUT, "scripts", f"{kind}_{lc}.txt")
    if not os.path.exists(sp): hb_print("SKIP: no script"); sys.exit(1)
    with open(sp, "r", encoding="utf-8") as f: raw = f.read()
    if not iss:
        wc = len(raw.split())
        hb_print(f"  Script: {wc} words (~{wc/150:.0f} min)")
        if wc > MAX_LONG_WORDS:
            raw = trim_script(raw, MAX_LONG_WORDS)
            with open(sp, "w", encoding="utf-8") as f: f.write(raw)
            wc = len(raw.split())
        if wc < MIN_LONG_WORDS:
            hb_print(f"  Expanding {wc} -> {TARGET_LONG_WORDS}...")
            expanded = expand_script(raw, TARGET_LONG_WORDS)
            expanded = trim_script(expanded, MAX_LONG_WORDS)
            with open(sp, "w", encoding="utf-8") as f: f.write(expanded)
            raw = expanded; wc = len(raw.split())
    else:
        wc = len(raw.split())
        if wc > MAX_SHORT_WORDS:
            raw = trim_short_script(raw, MAX_SHORT_WORDS)
            with open(sp, "w", encoding="utf-8") as f: f.write(raw)
            wc = len(raw.split())
    clean = clean_text(raw); wc = len(clean.split())
    if not iss and wc < MIN_LONG_WORDS and _ai_available:
        hb_print(f"SKIP: script too short ({wc} words)"); sys.exit(1)
    if not iss and wc < MIN_LONG_WORDS:
        hb_print(f"  WARNING: Script under {MIN_LONG_WORDS} words (AI was down), proceeding anyway...")
    hb_print(f"Building {LANGUAGES[lc]['name']} {kind} ({wc} words, ~{wc/150:.0f} min)...")
    ap = os.path.join(OUT, f"audio_{kind}_{lc}.mp3")
    vtt_path = os.path.join(OUT, f"subs_{kind}_{lc}.vtt")
    ok = asyncio.run(gen_tts(clean, lc, kind, ap, vtt_path))
    if not ok or not os.path.exists(ap) or os.path.getsize(ap) < 1000:
        hb_print("FAIL: TTS failed"); sys.exit(1)
    adur = get_dur(ap)
    min_dur = 10.0 if iss else 900.0
    max_dur = 120.0 if iss else 2400.0
    if adur < min_dur:
        hb_print(f"SKIP: audio too short ({adur/60:.1f} min)"); sys.exit(1)
    if adur > max_dur:
        hb_print(f"SKIP: audio too long ({adur/60:.1f} min)"); sys.exit(1)
    hb_print(f"  Audio: {adur:.0f}s ({adur/60:.1f} min)")
    srt_path = vtt_to_srt(vtt_path)
    ai = sorted([os.path.join(IMGS,f) for f in os.listdir(IMGS) if f.lower().endswith(('.jpg','.jpeg','.png'))]) if os.path.exists(IMGS) else []
    if not ai:
        os.makedirs(IMGS, exist_ok=True)
        for idx in range(10):
            fp = os.path.join(IMGS, f"fallback_{idx:03d}.jpg")
            dark_bg_rich(VIDEO_W if not iss else SHORT_W, VIDEO_H if not iss else SHORT_H).save(fp, quality=90); ai.append(fp)
    ni = IMAGES_PER_SHORT if iss else min(60, IMAGES_PER_VIDEO)
    imgs = random.sample(ai, min(ni, len(ai)))
    vp = os.path.join(OUT, f"video_{kind}_{lc}.mp4")
    if iss:
        try: render_short_video(clean, lc, kind, ap, srt_path, vp)
        except Exception as e: hb_print(f"FAIL: short render: {e}"); sys.exit(1)
    else:
        try: render_video(imgs, ap, srt_path, vp, iss)
        except Exception as e: hb_print(f"FAIL: long render: {e}"); sys.exit(1)
    if not os.path.exists(vp): sys.exit(1)
    vd = get_dur(vp); md = 10.0 if iss else 900.0
    if vd < md:
        try: os.remove(vp)
        except: pass
        hb_print(f"SKIP: video too short ({vd/60:.1f} min)"); sys.exit(1)
    hb_print(f"Video: {vd:.0f}s ({vd/60:.1f} min)")
    mf = os.path.join(OUT, "metadata", "all.json"); tt = f"{LANGUAGES[lc]['name']} Crime Story"
    if os.path.exists(mf):
        try:
            with open(mf, "r", encoding="utf-8") as f: am = json.load(f)
            m = am.get(lc, {}).get(kind, {})
            if m and m.get("title"): tt = m["title"]
        except: pass
    tp = os.path.join(OUT, f"thumb_{kind}_{lc}.jpg")
    try: make_thumb(tt, imgs, tp, iss)
    except:
        try: dark_bg_rich(THUMB_WIDTH, THUMB_HEIGHT).save(tp, quality=THUMB_QUALITY)
        except: pass
    try: shutil.rmtree(TEMP, ignore_errors=True)
    except: pass
    r = {"video": vp, "thumbnail": tp, "lang": lc, "kind": kind, "duration": vd}
    with open(os.path.join(OUT, "result.json"), "w") as f: json.dump(r, f)
    hb_print(f"BUILD SUCCESS: {lc} {kind} ({vd/60:.1f} min)")


# ═══════════════════════════════════════════════════════════════
# UPLOAD MODULE
# ═══════════════════════════════════════════════════════════════

def get_yt_token():
    r = http_req.post("https://oauth2.googleapis.com/token", data={
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SEC,
        "refresh_token": YT_REFRESH, "grant_type": "refresh_token"})
    if r.status_code != 200: raise Exception(f"Token failed: {r.status_code}: {r.text[:200]}")
    return r.json()["access_token"]


def get_yt_service():
    import google.oauth2.credentials, googleapiclient.discovery
    t = get_yt_token(); c = google.oauth2.credentials.Credentials(t)
    return googleapiclient.discovery.build("youtube", "v3", credentials=c)


def generate_seo_tags(base_tags, lang_code, category=""):
    all_tags = []
    for tag in (base_tags or []):
        st = sanitize_tag(tag)
        if st: all_tags.append(st)
    lang_seo = SEO_KEYWORDS.get(lang_code, SEO_KEYWORDS.get("en", {}))
    if TAG_STRATEGY in ("broad", "hybrid"):
        for tag in lang_seo.get("broad", []):
            st = sanitize_tag(tag)
            if st and st.lower() not in [t.lower() for t in all_tags]: all_tags.append(st)
    if TAG_STRATEGY in ("niche", "hybrid"):
        for tag in lang_seo.get("niche", []):
            st = sanitize_tag(tag)
            if st and st.lower() not in [t.lower() for t in all_tags]: all_tags.append(st)
    if category:
        cat_clean = sanitize_tag(category)
        if cat_clean: all_tags.append(cat_clean)
        for word in category.lower().split():
            st = sanitize_tag(word)
            if st and len(st) > 2 and st.lower() not in [t.lower() for t in all_tags]: all_tags.append(st)
    for tag in lang_seo.get("trending", []):
        st = sanitize_tag(tag)
        if st and st.lower() not in [t.lower() for t in all_tags]: all_tags.append(st)
    seen, unique = set(), []
    for tag in all_tags:
        tl = tag.lower().strip()
        if tl and tl not in seen and len(tag) > 1: seen.add(tl); unique.append(tag)
    result, total_len = [], 0
    for tag in unique:
        if total_len + len(tag) + 1 > 490: break
        result.append(tag); total_len += len(tag) + 1
    if len(result) < 3:
        for d in ["true crime","mystery","documentary","crime story","unsolved"]:
            if d.lower() not in [t.lower() for t in result]: result.append(d)
            if len(result) >= 5: break
    return result[:MAX_TAGS]


def generate_hashtags(lang_code, category=""):
    groups = HASHTAG_GROUPS.get(lang_code, HASHTAG_GROUPS.get("default", []))
    if not groups: groups = HASHTAG_GROUPS["default"]
    chosen = random.choice(groups)
    if category:
        cat_tag = "#" + category.replace(" ","").replace("-","").title()
        cat_tag = re.sub(r'[^a-zA-Z0-9#]', '', cat_tag)
        if 2 < len(cat_tag) <= 30: chosen = [cat_tag] + chosen
    return chosen[:12]


def build_seo_description(base_desc, lang_code, category="", short=False, timestamps=""):
    parts = []
    hooks = {"en": ["The truth behind this case will leave you speechless.",
                     "What the investigators missed will shock you."],
             "default": ["The truth behind this case will leave you speechless."]}
    parts.append(random.choice(hooks.get(lang_code, hooks["default"]))); parts.append("")
    if not short and timestamps: parts.append(timestamps); parts.append("")
    if base_desc: parts.append(base_desc); parts.append("")
    lang_seo = SEO_KEYWORDS.get(lang_code, SEO_KEYWORDS.get("en", {}))
    broad_kw = lang_seo.get("broad", [])[:5]
    if broad_kw:
        if lang_code == "en":
            parts.append(f"Dive deep into {broad_kw[0]} and {broad_kw[1]}. This {broad_kw[2]} investigation explores {broad_kw[3]} and {broad_kw[4]} like never before.")
        else: parts.append(" | ".join(broad_kw))
        parts.append("")
    hashtags = generate_hashtags(lang_code, category)
    if short and "#shorts" not in [h.lower() for h in hashtags]: hashtags.insert(0, "#shorts")
    parts.append(" ".join(hashtags)); parts.append("")
    if short: parts.append("Watch the full documentary on our channel!")
    else:
        parts.append("Subscribe and hit the bell icon for weekly true crime documentaries.")
        parts.append("Disclaimer: This content is for educational and informational purposes only.")
    return "\n".join(parts)


def upload_video(vp, tp, title, desc, tags, lc, short=False, pinned_comment="",
           title_b="", category="", timestamps=""):
    import googleapiclient.http
    yt = get_yt_service()
    ct = sanitize_youtube_title(title)
    hb_print(f"  Title: {ct[:60]}")
    prefixes = ["SHOCKING:","BREAKING:","EXPOSED:","REVEALED:","THE TRUTH:"]
    if not any(ct.upper().startswith(p.rstrip(":")) for p in prefixes):
        if random.random() < 0.5:
            new_t = f"{random.choice(prefixes)} {ct}"[:100]
            if len(new_t) > 10: ct = new_t
    full_desc = build_seo_description(desc, lc, category, short, timestamps)
    opt_tags = generate_seo_tags(tags, lc, category)
    body = {"snippet": {"title": ct, "description": full_desc, "tags": opt_tags,
                        "categoryId": YT_CATEGORY, "defaultLanguage": LANGUAGES[lc]["yt"],
                        "defaultAudioLanguage": LANGUAGES[lc]["yt"]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                       "embeddable": True, "publicStatsViewable": True}}
    vid = None
    for attempt in range(3):
        try:
            req = yt.videos().insert(part="snippet,status", body=body,
                media_body=googleapiclient.http.MediaFileUpload(vp, chunksize=8*1024*1024, resumable=True))
            res = None
            while res is None:
                heartbeat(f"  Upload progress...")
                status, res = req.next_chunk()
                if status: hb_print(f"  Upload: {int(status.progress()*100)}%")
            vid = res["id"]; hb_print(f"  Video ID: {vid}"); break
        except Exception as e:
            err = str(e).lower()
            if attempt < 2:
                if "quota" in err: time.sleep(60)
                elif "invalid" in err and "keyword" in err:
                    opt_tags = ["true crime","mystery","documentary"]; body["snippet"]["tags"] = opt_tags
                else: time.sleep(10)
                yt = get_yt_service()
            else: raise Exception(f"Upload failed 3x: {str(e)[:200]}")
    if not vid: raise Exception("Upload failed - no video ID")
    if tp and os.path.exists(tp) and os.path.getsize(tp) > 5000:
        try: yt.thumbnails().set(videoId=vid, media_body=googleapiclient.http.MediaFileUpload(tp)).execute(); hb_print("  Thumbnail set")
        except: pass
    try:
        pl_title = f"{'Shorts - ' if short else ''}True Crime - {LANGUAGES[lc]['name']}"
        playlists = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()
        pid = None
        for pl in playlists.get("items", []):
            if pl["snippet"]["title"] == pl_title: pid = pl["id"]; break
        if not pid:
            res = yt.playlists().insert(part="snippet,status", body={
                "snippet": {"title": pl_title, "description": f"True crime in {LANGUAGES[lc]['name']}"},
                "status": {"privacyStatus": "public"}}).execute()
            pid = res["id"]
        yt.playlistItems().insert(part="snippet", body={
            "snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        hb_print("  Added to playlist")
    except: pass
    if pinned_comment and len(pinned_comment.strip()) >= 5:
        try:
            pc = pinned_comment.replace('<','').replace('>','').replace('&','and')[:500]
            yt.commentThreads().insert(part="snippet", body={
                "snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": pc}}}}).execute()
            hb_print("  Pinned comment posted")
        except: pass
    os.makedirs(ANALYTICS, exist_ok=True)
    with open(os.path.join(ANALYTICS, "uploads.jsonl"), "a") as f:
        f.write(json.dumps({"video_id": vid, "lang": lc, "type": "short" if short else "long",
                "title": ct, "title_b": title_b,
                "uploaded_at": datetime.datetime.utcnow().isoformat()}) + "\n")
    return vid


def run_upload():
    rf = os.path.join(OUT, "result.json")
    mf = os.path.join(OUT, "metadata", "all.json")
    lc = os.environ.get("LANG_CODE", "en"); short = os.environ.get("VIDEO_TYPE", "long") == "short"
    kind = "short" if short else "long"
    hb_print(f"=== UPLOAD: lang={lc}, type={kind} ===")
    if not os.path.exists(rf): hb_print("FAIL: no result.json"); sys.exit(1)
    with open(rf) as f: r = json.load(f)
    if r.get("skip"): hb_print("FAIL: build skipped"); sys.exit(1)
    if not os.path.exists(mf): hb_print("FAIL: no metadata"); sys.exit(1)
    with open(mf) as f: am = json.load(f)
    m = am.get(lc, {}).get(kind, {})
    if not m: hb_print(f"FAIL: no metadata for {lc}/{kind}"); sys.exit(1)
    if not os.path.exists(r.get("video", "")): hb_print("FAIL: video not found"); sys.exit(1)
    ts = ""
    if not short:
        ts = "0:00 - Intro\n2:00 - Background\n5:00 - The Crime\n10:00 - Investigation\n15:00 - Suspects\n18:00 - Resolution\n21:00 - Conclusion\n"
    try:
        vid = upload_video(r["video"], r["thumbnail"], m.get("title","True Crime Mystery"),
            m.get("description",""), m.get("tags",["true crime"]), lc, short,
            m.get("pinned_comment",""), m.get("title_b",""), m.get("category",""), ts)
        hb_print(f"\nUPLOAD SUCCESS: https://youtube.com/watch?v={vid}")
    except Exception as e: hb_print(f"\nUPLOAD FAILED: {e}"); sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# COMMENT MODULE
# ═══════════════════════════════════════════════════════════════

REPLY_TEMPLATES = {"en": ["That's interesting! Have you looked into the {detail}?",
    "Great observation! A lot of people miss the {detail}.",
    "The {detail} really is the key. Good catch!",
    "Nobody ever talks about the {detail} - thanks!"],
    "default": ["Interesting! What about {detail}?", "Great observation!"]}
CASE_DETAILS = ["timeline","evidence","witness testimony","motive","alibi","DNA evidence","911 call"]


def generate_ai_reply(comment_text, video_title, lang="en"):
    if _ai_available and GEMINI_KEY:
        try:
            prompt = f"""You host a true crime channel. A viewer commented on "{video_title}": "{comment_text}". Write a natural reply: acknowledge them, add a detail, end with a question. Under 200 chars. Reply:"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            r = http_req.post(url, json={"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 150}}, timeout=30)
            if r.status_code == 200:
                reply = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if 20 < len(reply) <= 250: return reply
        except: pass
    return random.choice(REPLY_TEMPLATES.get(lang, REPLY_TEMPLATES["default"])).format(detail=random.choice(CASE_DETAILS))


def run_comment():
    yt = get_yt_service()
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")
    replied_file = os.path.join(ANALYTICS, "replied_comments.txt")
    os.makedirs(ANALYTICS, exist_ok=True)
    if not os.path.exists(log_file): hb_print("No uploads"); return
    uploads = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip(): uploads.append(json.loads(line))
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    recent = [u for u in uploads[-50:] if datetime.datetime.fromisoformat(u["uploaded_at"][:-1]) > cutoff]
    if not recent: hb_print("No recent uploads"); return
    total = 0
    for upload in recent:
        vid, lang, title = upload["video_id"], upload["lang"], upload.get("title","")
        try: comments = yt.commentThreads().list(part="snippet,replies", videoId=vid, maxResults=20, order="time").execute().get("items", [])
        except: continue
        for thread in comments[:15]:
            snippet = thread["snippet"]["topLevelComment"]["snippet"]
            cid = thread["snippet"]["topLevelComment"]["id"]
            text = snippet.get("textOriginal", "")
            if len(text) < 10: continue
            if any(w in text.lower() for w in ["subscribe","sub4sub","follow me"]): continue
            if os.path.exists(replied_file):
                with open(replied_file, "r") as f:
                    if cid in f.read().split("\n"): continue
            reply = generate_ai_reply(text, title, lang)
            author = snippet.get("authorDisplayName", "")
            if "@" not in reply and len(author) < 30: reply = f"@{author} {reply}"
            try:
                yt.comments().insert(part="snippet", body={"snippet": {"parentId": cid, "textOriginal": reply[:10000]}}).execute()
                with open(replied_file, "a") as f: f.write(cid + "\n")
                total += 1; time.sleep(COMMENT_REPLY_DELAY_SECONDS)
            except: pass
            if total >= MAX_COMMENT_REPLIES_PER_RUN: break
        if total >= MAX_COMMENT_REPLIES_PER_RUN: break
    hb_print(f"Replied to {total} comments")


# ═══════════════════════════════════════════════════════════════
# AB TEST MODULE
# ═══════════════════════════════════════════════════════════════

def run_abtest():
    yt = get_yt_service()
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")
    ab_log = os.path.join(ANALYTICS, "ab_tests.jsonl")
    os.makedirs(ANALYTICS, exist_ok=True)
    if not os.path.exists(log_file): hb_print("No uploads"); return
    tested = set()
    if os.path.exists(ab_log):
        with open(ab_log, "r") as f:
            for line in f:
                if line.strip():
                    try: tested.add(json.loads(line)["video_id"])
                    except: pass
    uploads = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if u.get("title_b") and u["video_id"] not in tested: uploads.append(u)
    if not uploads: hb_print("No videos to test"); return
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=AB_TEST_WAIT_HOURS)
    tests = 0
    for upload in uploads:
        vid, ta, tb = upload["video_id"], upload["title"], upload["title_b"]
        try: ua = datetime.datetime.fromisoformat(upload.get("uploaded_at","").rstrip("Z"))
        except: continue
        if ua > cutoff: continue
        try:
            res = yt.videos().list(part="statistics", id=vid).execute()
            if not res.get("items"): continue
            views = int(res["items"][0]["statistics"].get("viewCount", 0))
        except: continue
        if views < 10 or ta == tb: continue
        hb_print(f"  Testing: {vid[:8]} | Views: {views}")
        try:
            vid_res = yt.videos().list(part="snippet,status", id=vid).execute()
            if not vid_res.get("items"): continue
            video = vid_res["items"][0]; snippet = video["snippet"]; snippet["title"] = tb[:100]
            yt.videos().update(part="snippet", body={"id": vid, "snippet": snippet, "status": video["status"]}).execute()
            with open(ab_log, "a") as f:
                f.write(json.dumps({"video_id": vid, "original": ta, "new": tb,
                        "views_before": views, "timestamp": datetime.datetime.utcnow().isoformat()}) + "\n")
            tests += 1
        except: pass
        time.sleep(5)
        if tests >= 3: break
    hb_print(f"A/B tests: {tests}")


# ═══════════════════════════════════════════════════════════════
# ANALYTICS MODULE
# ═══════════════════════════════════════════════════════════════

def run_analytics():
    yt = get_yt_service()
    log_file = os.path.join(ANALYTICS, "uploads.jsonl")
    stats_file = os.path.join(ANALYTICS, "stats.jsonl")
    os.makedirs(ANALYTICS, exist_ok=True)
    if not os.path.exists(log_file): hb_print("No uploads"); return
    uploads = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                try: uploads.append(json.loads(line))
                except: pass
    if not uploads: hb_print("No uploads"); return
    now = datetime.datetime.utcnow().isoformat()
    new_stats = []
    for upload in uploads:
        vid = upload["video_id"]
        try:
            result = yt.videos().list(part="statistics,snippet", id=vid).execute()
            if result.get("items"):
                item = result["items"][0]; stats = item.get("statistics", {})
                new_stats.append({"video_id": vid, "timestamp": now,
                    "views": int(stats.get("viewCount",0)), "likes": int(stats.get("likeCount",0)),
                    "title": item["snippet"].get("title","")[:60],
                    "lang": upload.get("lang","en"), "type": upload.get("type","long")})
                hb_print(f"  {vid[:8]}... {stats.get('viewCount',0):>6} views")
        except: pass
        time.sleep(1)
    if new_stats:
        with open(stats_file, "a") as f:
            for e in new_stats: f.write(json.dumps(e) + "\n")
        tv = sum(s["views"] for s in new_stats); av = tv / len(new_stats)
        best = max(new_stats, key=lambda x: x["views"])
        hb_print(f"\n  Total: {tv:,} views | Avg: {av:,.0f}/video")
        hb_print(f"  Best: {best['title'][:50]} ({best['views']:,} views)")


# ═══════════════════════════════════════════════════════════════
# CLEANUP MODULE
# ═══════════════════════════════════════════════════════════════

def is_gibberish_title(text):
    words = text.split()
    if not words: return True
    gc = sum(1 for w in words if len(w) > 5 and not re.search(r'[aeiouAEIOU]', w))
    return gc / len(words) > 0.3


def run_cleanup():
    yt = get_yt_service()
    channels = yt.channels().list(part="contentDetails", mine=True).execute()
    if not channels.get("items"): hb_print("No channel"); return
    uploads_playlist = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = []; page_token = None
    while True:
        pl = yt.playlistItems().list(part="snippet,contentDetails",
            playlistId=uploads_playlist, maxResults=50, pageToken=page_token).execute()
        for item in pl.get("items", []):
            videos.append({"id": item["contentDetails"]["videoId"], "title": item["snippet"]["title"]})
        page_token = pl.get("nextPageToken")
        if not page_token: break
    hb_print(f"Found {len(videos)} videos")
    to_delete = []
    for v in videos:
        reason = None
        if "Error:" in v["title"] or "All AI providers failed" in v["title"]: reason = "ERROR"
        elif is_gibberish_title(v["title"]): reason = "GIBBERISH"
        if reason: to_delete.append((v["id"], v["title"], reason)); hb_print(f"  [{reason}] {v['title'][:60]}")
    if not to_delete: hb_print("No bad videos!"); return
    hb_print(f"\nDeleting {len(to_delete)} bad videos...")
    deleted = 0
    for vid, title, reason in to_delete:
        try: yt.videos().delete(id=vid).execute(); hb_print(f"  DELETED: {title[:50]}"); deleted += 1; time.sleep(2)
        except: pass
    hb_print(f"Cleaned {deleted}/{len(to_delete)}")


# ═══════════════════════════════════════════════════════════════
# FULL PIPELINE
# ═══════════════════════════════════════════════════════════════

def run_full():
    hb_print("=" * 60); hb_print("FULL PIPELINE START"); hb_print("=" * 60)
    hb_print("\n>>> STEP 1: PREPARE <<<"); run_prepare()
    hb_print("\n>>> STEP 2: DOWNLOAD <<<"); run_download()
    lc = os.environ.get("LANG_CODE", "en")
    for vtype in ["long", "short"]:
        os.environ["VIDEO_TYPE"] = vtype
        hb_print(f"\n>>> STEP 3: BUILD {vtype.upper()} <<<")
        try: run_build()
        except Exception as e: hb_print(f"Build {vtype} failed: {e}"); continue
        hb_print(f"\n>>> STEP 4: UPLOAD {vtype.upper()} <<<")
        try: run_upload()
        except Exception as e: hb_print(f"Upload {vtype} failed: {e}")
    hb_print("\n" + "=" * 60); hb_print("FULL PIPELINE COMPLETE"); hb_print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    cmd = sys.argv[1].lower()
    commands = {"prepare": run_prepare, "download": run_download, "build": run_build,
                "upload": run_upload, "comment": run_comment, "abtest": run_abtest,
                "analytics": run_analytics, "cleanup": run_cleanup, "full": run_full}
    if cmd not in commands:
        hb_print(f"Unknown: {cmd}\nAvailable: {', '.join(commands.keys())}"); sys.exit(1)
    commands[cmd]()
