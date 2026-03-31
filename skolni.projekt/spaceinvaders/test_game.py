"""
===================================================
  TESTY PRO SPACE INVADERS
===================================================
Tento soubor testuje správnost klíčové logiky hry.
Testy jsou automatické – spustí se a samy zkontrolují,
zda výsledky odpovídají očekávání.

Co se testuje:
  1) Škálování rozlišení – přepočet velikostí objektů
     pro různá rozlišení obrazovky
  2) Highscores – ukládání výsledků do JSON souboru
     a jejich správné řazení

Jak spustit:
  python test_game.py

Výstup:
  ✓ V pořádku  – test prošel
  ✗ CHYBA      – test selhal (s popisem problému)
"""

import json      # Pro práci s JSON soubory (highscores)
import os        # Pro kontrolu existence souborů na disku
import tempfile  # Pro dočasné soubory/složky (bezpečné testování)
import time      # Pro generování datumu/času v záznamech

# ===== BARVY PRO VÝSTUP DO TERMINÁLU =====
# ANSI escape kódy – speciální sekvence, které terminál interpretuje jako barvu.
# \033[ = začátek escape sekvence; číslo = kód barvy/stylu; m = konec kódu.
GREEN  = "\033[92m"   # Světle zelená (pro úspěch)
RED    = "\033[91m"   # Světle červená (pro chybu)
RESET  = "\033[0m"    # Resetuje barvu na výchozí
BOLD   = "\033[1m"    # Tučný text

# ===== GLOBÁLNÍ ČÍTAČE TESTŮ =====
# Tyto proměnné sledují, kolik testů prošlo a kolik selhalo.
passed = 0   # Počet úspěšných testů
failed = 0   # Počet neúspěšných testů


def ok(name):
    """
    Zaznamená úspěšný test a vypíše zprávu o úspěchu.
    global = pracujeme s globální proměnnou (ne lokální kopií)
    @param name: Popis testu (zobrazí se ve výstupu)
    """
    global passed
    passed += 1   # Zvýšíme čítač úspěšných testů
    print(f"  {GREEN}✓ V pořádku{RESET}  —  {name}")
    # f-string = formátovaný řetězec; {proměnná} se nahradí hodnotou


def fail(name, reason):
    """
    Zaznamená neúspěšný test a vypíše popis chyby.
    @param name:   Popis testu
    @param reason: Důvod selhání (text nebo výjimka)
    """
    global failed
    failed += 1
    print(f"  {RED}✗ CHYBA{RESET}    —  {name}")
    print(f"           {RED}↳ {reason}{RESET}")
    # ↳ = vizuální šipka pro přehlednost ve výstupu


def section(title):
    """
    Vypíše nadpis sekce testů pro přehlednost výstupu.
    @param title: Název testovací sekce
    """
    print(f"\n{BOLD}[ {title} ]{RESET}")


# =============================================================
# TEST 1 — Škálování rozlišení
# =============================================================
# Hra je designována pro 800×600.
# Při jiném rozlišení se všechny objekty přepočítají pomocí
# koeficientů sx (šířka) a sy (výška).
#
# Příklad: hráč je 50×40px při 800×600
#          při 1600×900 → sx=2.0, sy=1.5 → hráč bude 100×60px
# =============================================================

section("TEST 1: Škálování rozlišení")

# Referenční rozlišení – hra je designována pro tyto rozměry
REF_W, REF_H = 800, 600


def compute_scale(width, height):
    """
    Vypočítá škálovací koeficienty pro dané rozlišení.
    sx = koeficient pro šířku (osa X)
    sy = koeficient pro výšku (osa Y)

    Příklad: compute_scale(1600, 900)
             → sx = 1600/800 = 2.0
             → sy = 900/600  = 1.5
    """
    sx = width  / REF_W   # Poměr nové šířky k referenční
    sy = height / REF_H   # Poměr nové výšky k referenční
    return sx, sy


def compute_scaled_size(base_w, base_h, width, height):
    """
    Vypočítá skutečnou velikost objektu po přizpůsobení danému rozlišení.
    @param base_w, base_h: Základní rozměry objektu (při 800×600)
    @param width, height:  Cílové rozlišení
    @returns: (nová_šířka, nová_výška) jako celá čísla
    """
    sx, sy = compute_scale(width, height)
    # int() zaokrouhlí dolů – pygame potřebuje celá čísla pro pixely
    return int(base_w * sx), int(base_h * sy)


# ── Test 1a: Základní rozlišení ────────────────────────────────────
# Při 800×600 musí být koeficienty přesně 1.0 (žádné škálování)
try:
    sx, sy = compute_scale(800, 600)
    # assert = tvrzení; pokud není pravda, vyvolá AssertionError
    assert sx == 1.0 and sy == 1.0, f"očekáváno 1.0, 1.0 — dostáno {sx}, {sy}"
    ok("800×600 dává sx=1.0, sy=1.0")
except AssertionError as e:
    # AssertionError nastane, pokud tvrzení neplatí
    fail("800×600 dává sx=1.0, sy=1.0", e)


# ── Test 1b: Dvojnásobné rozlišení ─────────────────────────────────
# 1600×900 → sx=2.0, sy=1.5
# Hráčova loď (50×40px) by měla být 100×60px
try:
    pw, ph = compute_scaled_size(50, 40, 1600, 900)
    assert pw == 100, f"šířka: očekáváno 100, dostáno {pw}"
    assert ph == 60,  f"výška: očekáváno 60, dostáno {ph}"
    ok("1600×900: player_img se škáluje na 100×60")
except AssertionError as e:
    fail("1600×900: player_img se škáluje na 100×60", e)


# ── Test 1c: Full HD rozlišení ─────────────────────────────────────
# 1920×1080 → sx=2.4, sy=1.8
# Základna (300×60px) by měla být 720×108px
try:
    bw, bh = compute_scaled_size(300, 60, 1920, 1080)
    assert bw == 720, f"šířka: očekáváno 720, dostáno {bw}"
    assert bh == 108, f"výška: očekáváno 108, dostáno {bh}"
    ok("1920×1080: base_img se škáluje na 720×108")
except AssertionError as e:
    fail("1920×1080: base_img se škáluje na 720×108", e)


# ── Test 1d: Žádné záporné rozměry ─────────────────────────────────
# Pro všechna podporovaná rozlišení nesmí vyjít záporný nebo nulový rozměr
try:
    for (w, h) in [(800, 600), (1024, 768), (1280, 720),
                   (1280, 960), (1600, 900), (1920, 1080)]:
        pw, ph = compute_scaled_size(50, 40, w, h)
        assert pw > 0 and ph > 0, f"záporný/nulový rozměr pro {w}×{h}"
    ok("Všechna rozlišení dávají kladné rozměry obrázků")
except AssertionError as e:
    fail("Všechna rozlišení dávají kladné rozměry obrázků", e)


# =============================================================
# TEST 2 — Ukládání a řazení highscores
# =============================================================
# Ověřuje, že:
#   - výsledky se správně ukládají do JSON souboru
#   - záznamy jsou seřazeny od nejvyššího skóre (sestupně)
#   - na prvním místě je skutečně hráč s nejvyšším skóre
#
# Používáme tempfile – dočasnou složku, která se po testu
# automaticky smaže. Nesmíme přepisovat skutečný highscores.json!
# =============================================================

section("TEST 2: Ukládání a řazení highscores")


def save_highscore(path, name, score, game_time):
    """
    Stejná logika jako v hlavní hře (space_invaders.py),
    ale s parametrem path = cesta k JSON souboru.
    Tím testujeme logiku bez závislosti na skutečném souboru.

    @param path:      Cesta k JSON souboru s highscores
    @param name:      Jméno hráče
    @param score:     Dosažené skóre (celé číslo)
    @param game_time: Délka hry v sekundách
    @returns: True při úspěchu, False při chybě
    """
    try:
        # Pokud soubor již existuje, načteme stávající záznamy
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)   # json.load() = parsování JSON ze souboru
        else:
            data = {"highscores": []}   # Soubor neexistuje – prázdný seznam

        # Přidáme nový záznam jako slovník (dictionary)
        data["highscores"].append({
            "name":  name,
            "score": score,
            "time":  game_time,
            "date":  time.strftime("%d.%m.%Y %H:%M")  # Aktuální datum a čas
        })

        # Seřadíme záznamy sestupně podle skóre
        # key=lambda x: x["score"] = seřaď podle hodnoty klíče "score"
        # reverse=True = od největšího (sestupně)
        data["highscores"].sort(key=lambda x: x["score"], reverse=True)

        # Zapíšeme aktualizovaný seznam zpět do souboru
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            # ensure_ascii=False = ukládá diakritiku přímo (ne jako \uXXXX)
            # indent=2 = odsazení 2 mezerami pro přehledný JSON

        return True   # Úspěch

    except Exception as e:
        # Exception = zachytí jakoukoli chybu (soubor nelze zapsat atd.)
        return False


# ── Spuštění testů v dočasné složce ────────────────────────────────
# tempfile.TemporaryDirectory() vytvoří dočasnou složku na disku.
# Blok "with" zajistí, že se složka automaticky smaže po skončení bloku.
with tempfile.TemporaryDirectory() as tmpdir:

    # Cesta k testovacímu JSON souboru uvnitř dočasné složky
    hs_path = os.path.join(tmpdir, "highscores.json")
    # os.path.join() = správné spojení cest pro aktuální OS (Linux/Windows)


    # ── Test 2a: Uložení vrátí True ────────────────────────────────
    # Základní test – funkce musí vrátit True (= žádná chyba při ukládání)
    try:
        result = save_highscore(hs_path, "Testovaci", 100, 42)
        assert result is True, "funkce vrátila False místo True"
        ok("Uložení highscore vrátí True")
    except AssertionError as e:
        fail("Uložení highscore vrátí True", e)


    # ── Test 2b: Soubor existuje a obsahuje správné jméno ──────────
    # Zkontrolujeme, že soubor byl skutečně vytvořen a obsahuje hráče
    try:
        assert os.path.exists(hs_path), "soubor nebyl vytvořen"

        # Otevřeme soubor a načteme obsah
        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Zkontrolujeme, že první záznam má správné jméno
        assert data["highscores"][0]["name"] == "Testovaci", "jméno nesedí"
        ok("Soubor highscores.json je vytvořen se správným jménem")

    except (AssertionError, json.JSONDecodeError) as e:
        # json.JSONDecodeError = soubor existuje, ale není validní JSON
        fail("Soubor highscores.json je vytvořen se správným jménem", e)


    # ── Test 2c: Záznamy jsou seřazeny od nejvyššího skóre ─────────
    # Přidáme více hráčů a zkontrolujeme, že jsou seřazeni správně
    try:
        # Přidáme 3 další hráče s různými skóre
        save_highscore(hs_path, "Porazeny",   50,  30)
        save_highscore(hs_path, "Vitez",     999, 120)
        save_highscore(hs_path, "Prostredni",250,  75)

        # Načteme finální obsah souboru
        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vytáhneme jen číselné hodnoty skóre ze všech záznamů
        # List comprehension: [výraz for proměnná in seznam]
        scores = [e["score"] for e in data["highscores"]]

        # Porovnáme, zda je seznam stejný jako jeho seřazená verze
        # sorted(scores, reverse=True) = vrátí NOVÝ seřazený seznam (originál nezměněn)
        assert scores == sorted(scores, reverse=True), \
            f"skóre nejsou seřazena sestupně: {scores}"
        ok("Více záznamů je seřazeno od nejvyššího skóre")

    except AssertionError as e:
        fail("Více záznamů je seřazeno od nejvyššího skóre", e)


    # ── Test 2d: Vítěz je skutečně na prvním místě ─────────────────
    # Explicitně ověříme, že hráč "Vitez" se skóre 999 je #1
    try:
        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # data["highscores"][0] = první prvek seznamu = nejlepší hráč
        top = data["highscores"][0]

        # Zkontrolujeme jméno i skóre zároveň pomocí jednoho assertu
        assert top["name"] == "Vitez" and top["score"] == 999, \
            f"první místo: {top}"
        ok("Na prvním místě je hráč s nejvyšším skóre (999)")

    except AssertionError as e:
        fail("Na prvním místě je hráč s nejvyšším skóre (999)", e)


# =============================================================
# SOUHRN VÝSLEDKŮ
# =============================================================
# Vypíšeme celkový výsledek po dokončení všech testů.
# =============================================================

total = passed + failed   # Celkový počet testů

print(f"\n{BOLD}{'=' * 40}{RESET}")

if failed == 0:
    # Všechny testy prošly
    print(f"{GREEN}{BOLD}Všechny testy prošly! ({passed}/{total}){RESET}")
else:
    # Některé testy selhaly
    print(f"{RED}{BOLD}{failed} test(y) selhaly! ({passed}/{total} prošlo){RESET}")

print(f"{BOLD}{'=' * 40}{RESET}\n")

# exit() ukončí program s návratovým kódem:
#   0 = úspěch (vše v pořádku)
#   1 = chyba  (CI/CD systémy toto rozlišení používají)
exit(0 if failed == 0 else 1)
