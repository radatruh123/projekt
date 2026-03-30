"""
Testy pro Space Invaders
Testuje: 1) logiku škálování rozlišení
         2) ukládání a řazení highscores
"""

import json
import os
import tempfile
import time

# ===== BARVY PRO VÝSTUP =====
GREEN  = "\033[92m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0

def ok(name):
    global passed
    passed += 1
    print(f"  {GREEN}✓ V pořádku{RESET}  —  {name}")

def fail(name, reason):
    global failed
    failed += 1
    print(f"  {RED}✗ CHYBA{RESET}    —  {name}")
    print(f"           {RED}↳ {reason}{RESET}")

def section(title):
    print(f"\n{BOLD}[ {title} ]{RESET}")

# =============================================================
# TEST 1 — Škálování rozlišení
# =============================================================
# Ověřuje, že škálovací koeficienty sx/sy vychází správně
# pro různá rozlišení vůči základnímu 800×600.
# =============================================================

section("TEST 1: Škálování rozlišení")

REF_W, REF_H = 800, 600

def compute_scale(width, height):
    sx = width / REF_W
    sy = height / REF_H
    return sx, sy

def compute_scaled_size(base_w, base_h, width, height):
    sx, sy = compute_scale(width, height)
    return int(base_w * sx), int(base_h * sy)

# 1a) Základní rozlišení → škálování musí být 1.0
try:
    sx, sy = compute_scale(800, 600)
    assert sx == 1.0 and sy == 1.0, f"očekáváno 1.0, 1.0 — dostáno {sx}, {sy}"
    ok("800×600 dává sx=1.0, sy=1.0")
except AssertionError as e:
    fail("800×600 dává sx=1.0, sy=1.0", e)

# 1b) 1600×900 → sx=2.0, sy=1.5  →  player 50×40 by měl být 100×60
try:
    pw, ph = compute_scaled_size(50, 40, 1600, 900)
    assert pw == 100, f"šířka: očekáváno 100, dostáno {pw}"
    assert ph == 60,  f"výška: očekáváno 60, dostáno {ph}"
    ok("1600×900: player_img se škáluje na 100×60")
except AssertionError as e:
    fail("1600×900: player_img se škáluje na 100×60", e)

# 1c) 1920×1080 → base_img 300×60 by měl být 720×108
try:
    bw, bh = compute_scaled_size(300, 60, 1920, 1080)
    assert bw == 720, f"šířka: očekáváno 720, dostáno {bw}"
    assert bh == 108, f"výška: očekáváno 108, dostáno {bh}"
    ok("1920×1080: base_img se škáluje na 720×108")
except AssertionError as e:
    fail("1920×1080: base_img se škáluje na 720×108", e)

# 1d) Škálování nikdy nesmí vrátit záporné nebo nulové rozměry
try:
    for (w, h) in [(800,600),(1024,768),(1280,720),(1280,960),(1600,900),(1920,1080)]:
        pw, ph = compute_scaled_size(50, 40, w, h)
        assert pw > 0 and ph > 0, f"záporný/nulový rozměr pro {w}×{h}"
    ok("Všechna rozlišení dávají kladné rozměry obrázků")
except AssertionError as e:
    fail("Všechna rozlišení dávají kladné rozměry obrázků", e)

# =============================================================
# TEST 2 — Ukládání a řazení highscores
# =============================================================
# Ověřuje, že se záznamy správně ukládají do JSON souboru
# a jsou seřazeny od nejvyššího skóre.
# =============================================================

section("TEST 2: Ukládání a řazení highscores")

def save_highscore(path, name, score, game_time):
    """Stejná logika jako v hlavní hře, ale s vlastní cestou k souboru."""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"highscores": []}
        data["highscores"].append({
            "name": name,
            "score": score,
            "time": game_time,
            "date": time.strftime("%d.%m.%Y %H:%M")
        })
        data["highscores"].sort(key=lambda x: x["score"], reverse=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

with tempfile.TemporaryDirectory() as tmpdir:
    hs_path = os.path.join(tmpdir, "highscores.json")

    # 2a) Uložení vrátí True (žádná chyba)
    try:
        result = save_highscore(hs_path, "Testovaci", 100, 42)
        assert result is True, "funkce vrátila False místo True"
        ok("Uložení highscore vrátí True")
    except AssertionError as e:
        fail("Uložení highscore vrátí True", e)

    # 2b) Soubor se skutečně vytvoří a obsahuje správné jméno
    try:
        assert os.path.exists(hs_path), "soubor nebyl vytvořen"
        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["highscores"][0]["name"] == "Testovaci", "jméno nesedí"
        ok("Soubor highscores.json je vytvořen se správným jménem")
    except (AssertionError, json.JSONDecodeError) as e:
        fail("Soubor highscores.json je vytvořen se správným jménem", e)

    # 2c) Více záznamů je seřazeno od nejvyššího skóre
    try:
        save_highscore(hs_path, "Porazeny",  50,  30)
        save_highscore(hs_path, "Vitez",     999, 120)
        save_highscore(hs_path, "Prostredni",250,  75)

        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        scores = [e["score"] for e in data["highscores"]]
        assert scores == sorted(scores, reverse=True), \
            f"skóre nejsou seřazena sestupně: {scores}"
        ok("Více záznamů je seřazeno od nejvyššího skóre")
    except AssertionError as e:
        fail("Více záznamů je seřazeno od nejvyššího skóre", e)

    # 2d) Nejvyšší skóre je skutečně na prvním místě
    try:
        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        top = data["highscores"][0]
        assert top["name"] == "Vitez" and top["score"] == 999, \
            f"první místo: {top}"
        ok("Na prvním místě je hráč s nejvyšším skóre (999)")
    except AssertionError as e:
        fail("Na prvním místě je hráč s nejvyšším skóre (999)", e)

# =============================================================
# VÝSLEDEK
# =============================================================
total = passed + failed
print(f"\n{BOLD}{'='*40}{RESET}")
if failed == 0:
    print(f"{GREEN}{BOLD}Všechny testy prošly! ({passed}/{total}){RESET}")
else:
    print(f"{RED}{BOLD}{failed} test(y) selhaly! ({passed}/{total} prošlo){RESET}")
print(f"{BOLD}{'='*40}{RESET}\n")

exit(0 if failed == 0 else 1)
