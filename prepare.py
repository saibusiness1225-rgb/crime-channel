def main():
    os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "metadata"), exist_ok=True)

    provs = build_providers()
    paid_provs = [p for p in provs if "Pollinations" not in p[0]]
    
    if not paid_provs:
        print("⚠️ WARNING: No PAID API keys found. Using FREE fallback (Pollinations).")
        print("   Note: Translations may fail due to text length limits.")

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
        
        # Process Translations (with error handling)
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
            successful_langs.append(code) # Only add if successful
            print(f"  Title: {lm.get('title', '?')}")
            print(f"  Comment: {lm.get('pinned_comment', '?')[:80]}...")
        except Exception as e:
            print(f"  ⚠️ Skipping {code} (Error: {str(e)[:50]}...)")
        time.sleep(1)

    with open(os.path.join(OUT, "metadata", "all.json"), "w") as f:
        json.dump(am, f, ensure_ascii=False, indent=2)
    
    # FIX: Only save languages that actually succeeded
    # If everything failed except English, ensure English is in the list
    if not successful_langs:
        successful_langs = ["en"]
    
    with open(os.path.join(OUT, "selected_languages.json"), "w") as f:
        json.dump(successful_langs, f)

    print(f"\n{'=' * 50}")
    print(f"DONE — {len(am)} languages with SEO + engagement")
    print(f"Final Build List: {successful_langs}")
    print(f"{'=' * 50}")
