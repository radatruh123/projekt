"""
===================================================
  SPACE INVADERS – hlavní soubor hry
===================================================
Tento soubor obsahuje veškerou logiku hry:
  - inicializaci okna a grafiky
  - herní objekty (hráč, nepřátelé, meteority, powerupy)
  - hlavní herní smyčku (game loop)
  - vykreslování menu, hry, pauzy a game over obrazovky
  - ukládání vysokých skóre do JSON souboru

Knihovny:
  pygame  – grafika, zvuk, vstupy (klávesnice/myš)
  random  – náhodná čísla (spawn nepřátel, meteorů atd.)
  math    – matematické funkce (sin, cos, hypot…)
  json    – čtení/zápis highscores souboru
  os      – práce se soubory
  time    – měření herního času
  sys     – ukončení programu
"""

import pygame   # Hlavní herní knihovna
import sys       # Pro sys.exit() – čisté ukončení programu
import random    # Pro náhodné generování pozic a hodnot
import time      # Pro měření herního času a timeouty
import math      # Pro matematiku (sin, cos, vzdálenosti…)
import json      # Pro čtení a zápis souboru s highscores
import os        # Pro práci se soubory (existuje? apod.)

# ── Inicializace pygame ─────────────────────────────────────
# Musí být voláno jako první, než cokoli jiného v pygame
pygame.init()

# ===== NASTAVENÍ ROZLIŠENÍ =====
# Seznam podporovaných rozlišení obrazovky (šířka × výška v pixelech)
RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1280, 960),
    (1600, 900),
    (1920, 1080),
]
resolution_index = 0   # Aktuálně zvolené rozlišení (index do seznamu výše)
fullscreen = False       # True = celá obrazovka, False = okno

# ===== REFERENČNÍ ROZLIŠENÍ PRO ŠKÁLOVÁNÍ =====
# Vše je designováno pro 800×600; při jiném rozlišení se přepočítá
REF_W, REF_H = 800, 600

# Nastavíme okno hry na zvolené rozlišení
WIDTH, HEIGHT = RESOLUTIONS[resolution_index]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# clock řídí počet snímků za sekundu (FPS) – zabrání tomu,
# aby hra běžela příliš rychle na výkonných počítačích
clock = pygame.time.Clock()

# ===== BARVY =====
# Barvy jsou trojice (červená, zelená, modrá) v rozsahu 0–255
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (150, 150, 150)
DARK_GRAY  = (50,  50,  50 )
RED        = (255, 0,   0  )
YELLOW     = (255, 255, 0  )
GREEN      = (0,   255, 0  )
CYAN       = (0,   220, 255)
ORANGE     = (255, 165, 0  )
PURPLE     = (180, 0,   255)
LIGHT_BLUE = (100, 180, 255)
PINK       = (255, 100, 180)
GOLD       = (255, 215, 0  )
DEEP_BLUE  = (5,   5,   20 )   # Tmavě modrá – barva vesmírného pozadí

# ===== FONTY =====
# Font(None, velikost) – None = výchozí pygame font (bez souboru)
font       = pygame.font.Font(None, 32)   # Normální text
big_font   = pygame.font.Font(None, 72)   # Velké nadpisy
small_font = pygame.font.Font(None, 24)   # Malý text (popisky, tipy)
title_font = pygame.font.Font(None, 110)  # Obrovský titulek v menu

# ===== STAVY HRY =====
# Hra má různé "obrazovky" – každý stav říká, co se právě zobrazuje
MENU      = "menu"       # Hlavní menu
SETTINGS  = "settings"   # Nastavení rozlišení
GAME      = "game"       # Probíhající hra
PAUSE     = "pause"      # Pauza
GAME_OVER = "game_over"  # Konec hry (zadávání jména)
state     = MENU          # Začínáme na hlavním menu

# ===== POMOCNÉ FUNKCE PRO ŠKÁLOVÁNÍ =====
# Tyto funkce zajistí, že objekty budou mít správnou velikost
# na všech rozlišeních obrazovky.

def scale_x():
    """Vrátí koeficient škálování pro osu X (šířka)."""
    return WIDTH / REF_W

def scale_y():
    """Vrátí koeficient škálování pro osu Y (výška)."""
    return HEIGHT / REF_H

def scale_val(val):
    """Škáluje hodnotu průměrem obou os – vhodné pro tloušťky, rádiusy apod."""
    return val * (scale_x() + scale_y()) / 2

# ===== OBRÁZKY =====
def load_images():
    """
    Načte PNG obrázky ze souborů a přizpůsobí je aktuálnímu rozlišení.
    Volá se při startu a po každé změně rozlišení.
    """
    global player_img, enemy_img, meteor_img, base_img
    sx, sy = scale_x(), scale_y()   # Aktuální škálovací koeficienty

    # Načteme a přizpůsobíme obrázek hráče (loď)
    player_img = pygame.transform.scale(
        pygame.image.load("player.png").convert_alpha(),
        (int(50 * sx), int(40 * sy))
    )
    # Načteme a přizpůsobíme obrázek nepřítele
    enemy_img = pygame.transform.scale(
        pygame.image.load("enemy.png").convert_alpha(),
        (int(45 * sx), int(35 * sy))
    )
    # Meteorit se škáluje dynamicky podle velikosti – načteme jen originál
    meteor_img = pygame.image.load("meteor.png").convert_alpha()
    # Základna (základna hráče na spodku obrazovky)
    base_img = pygame.transform.scale(
        pygame.image.load("base.png").convert_alpha(),
        (int(300 * sx), int(60 * sy))
    )

load_images()   # Zavoláme hned při spuštění

# ===== MENU – seznam položek =====
menu_items = ["Start", "Settings", "Quit"]
menu_rects = []   # Zde si uložíme obdélníky tlačítek pro detekci kliknutí

# ===== HRÁČ =====
def make_player_rect():
    """
    Vytvoří Rect (obdélník) pro hráče na správné pozici
    podle aktuálního rozlišení.
    """
    sx, sy = scale_x(), scale_y()
    return pygame.Rect(
        WIDTH // 2 - int(25 * sx),   # Horizontálně uprostřed
        HEIGHT - int(120 * sy),       # Blízko spodku obrazovky
        int(50 * sx),                  # Šířka hráče
        int(40 * sy)                   # Výška hráče
    )

player       = make_player_rect()   # Rect hráče (pozice + rozměry)
player_speed = 6                     # Rychlost pohybu hráče v pixelech/snímek
player_bullets = []                  # Seznam střel hráče (každá je Rect)
lives        = 3                     # Počet životů hráče

# ===== ZÁKLADNA =====
def make_base_rect():
    """
    Vytvoří Rect pro základnu hráče na spodku obrazovky.
    Základna se ztratí, pokud ji zasáhne nepřítel nebo meteorit.
    """
    sx, sy = scale_x(), scale_y()
    return pygame.Rect(
        WIDTH // 2 - int(150 * sx),
        HEIGHT - int(70 * sy),
        int(300 * sx),
        int(60 * sy)
    )

base_rect = make_base_rect()
base_hp   = 5   # Životy základny (0 = konec hry)

# ===== SKÓRE & ČAS =====
score       = 0   # Aktuální skóre hráče
start_time  = 0   # Unix timestamp začátku hry (pro měření délky hry)
final_score = 0   # Skóre uložené při game over (pro zobrazení a highscores)
final_time  = 0   # Čas hry uložený při game over

# ===== GAME OVER – zadávání jména =====
player_name    = ""     # Jméno hráče (zadává se na game over obrazovce)
name_submitted = False  # True = jméno bylo odesláno a skóre uloženo

# ===== PAUSE – tlačítko a odpočítávání =====
# Rect tlačítka PAUSE v levém horním rohu (pozice a rozměry)
pause_button    = pygame.Rect(10, 10, 100, 40)
countdown_start = None   # Čas, kdy začalo odpočítávání před pokračováním

# ===== POWERUPY – AUTO-STŘELBA =====
auto_shoot_active   = False  # Je auto-střelba aktivní?
auto_shoot_end      = 0      # Kdy vyprší (Unix timestamp)
AUTO_SHOOT_DURATION = 10     # Délka trvání v sekundách
auto_shoot_interval = 200    # Interval střel v milisekundách
auto_shoot_timer    = 0      # Interní čítač pro interval střel

# ===== POWERUPY – ŠTÍT =====
shield_active   = False  # Je štít aktivní?
shield_end      = 0      # Kdy vyprší
SHIELD_DURATION = 15     # Délka trvání v sekundách
shield_pulse    = 0      # Fáze animace pulzování štítu (v radiánech)

# ===================================================================
# ===== HVĚZDNÉ POZADÍ =====
# Tvoří iluzi letění vesmírem – hvězdy se pohybují dolů a dokola.
# Každá hvězda je slovník s pozicí (x, y), rychlostí a jasností.
# ===================================================================
def make_stars(count=200):
    """Vygeneruje seznam hvězd pro pozadí."""
    stars = []
    for _ in range(count):
        stars.append({
            "x":    random.randint(0, WIDTH),    # Náhodná x-pozice
            "y":    random.randint(0, HEIGHT),   # Náhodná y-pozice
            "vy":   random.uniform(0.3, 2.0),    # Rychlost pádu (různé vrstvy = iluze hloubky)
            "size": random.choice([1, 1, 1, 2]),  # Většina hvězd je malá (1px)
            "brightness": random.randint(80, 255) # Jas 0–255 (světlé i tmavé)
        })
    return stars

stars = make_stars()   # Vytvoříme hvězdy při spuštění

def update_stars():
    """
    Posune každou hvězdu dolů (simulace pohybu vesmírnou lodí).
    Hvězda, která odejde ze spodku, se znovu objeví nahoře.
    """
    for s in stars:
        s["y"] += s["vy"]
        if s["y"] > HEIGHT:          # Odešla ze spodku?
            s["y"] = 0                # Teleport na vrch
            s["x"] = random.randint(0, WIDTH)  # Nová náhodná x

def draw_stars():
    """Vykreslí všechny hvězdy jako malé bílé tečky."""
    for s in stars:
        c = s["brightness"]
        pygame.draw.circle(screen, (c, c, c), (int(s["x"]), int(s["y"])), s["size"])

# ===================================================================
# ===== MENU – DEKORACE =====
# Animovaná raketka, dekorativní nepřátelé a pulsující titulek.
# ===================================================================

# Raketka v menu – pohybuje se nahoru a dolů (sinusovka)
menu_rocket_y   = 0.0    # Aktuální y-offset (float pro plynulost)
menu_rocket_dir = 1      # Směr pohybu (+1 = dolů, -1 = nahoru)

# Dekorativní nepřátelé v menu – poletují vlevo-vpravo
menu_enemies = [
    {"x": float(random.randint(60, WIDTH - 60)),
     "y": float(random.randint(int(HEIGHT * 0.55), int(HEIGHT * 0.80))),
     "vx": random.choice([-1.2, 1.2]),
     "pulse": random.uniform(0, math.pi * 2)}
    for _ in range(5)
]

menu_title_pulse = 0.0   # Fáze animace titulku (pro barvy / třpyt)


def draw_menu_rocket(cx, cy):
    """
    Vykreslí pixel-art raketku na střed pozice (cx, cy).
    Raketka je sestavena z primitivních tvarů pygame (polygon, circle, rect).
    """
    # ── Tělo raketky ─────────────────────────────────────────
    # pygame.draw.polygon(povrch, barva, seznam_bodů)
    body_pts = [
        (cx,      cy - 42),   # Špička
        (cx + 14, cy + 10),   # Pravý dolní roh těla
        (cx - 14, cy + 10),   # Levý dolní roh těla
    ]
    pygame.draw.polygon(screen, (220, 220, 255), body_pts)

    # ── Střed těla (tmavší část) ──────────────────────────────
    inner_pts = [
        (cx,      cy - 30),
        (cx + 8,  cy + 8 ),
        (cx - 8,  cy + 8 ),
    ]
    pygame.draw.polygon(screen, (140, 140, 220), inner_pts)

    # ── Okno (kruh uprostřed trupu) ───────────────────────────
    pygame.draw.circle(screen, CYAN,      (cx, cy - 10), 8)
    pygame.draw.circle(screen, LIGHT_BLUE,(cx, cy - 10), 5)

    # ── Levé křídlo ──────────────────────────────────────────
    left_wing = [
        (cx - 14, cy + 10),
        (cx - 28, cy + 20),
        (cx - 14, cy + 20),
    ]
    pygame.draw.polygon(screen, (180, 180, 240), left_wing)

    # ── Pravé křídlo ─────────────────────────────────────────
    right_wing = [
        (cx + 14, cy + 10),
        (cx + 28, cy + 20),
        (cx + 14, cy + 20),
    ]
    pygame.draw.polygon(screen, (180, 180, 240), right_wing)

    # ── Tryska (ústí motoru) ──────────────────────────────────
    pygame.draw.rect(screen, GRAY, (cx - 6, cy + 10, 12, 8))

    # ── Plamen z trysky ───────────────────────────────────────
    # Plamen "bliká" díky sinusovce – každý snímek je trochu jiný
    flame_h = 18 + int(8 * math.sin(menu_title_pulse * 3))
    flame_pts = [
        (cx - 6,  cy + 18),
        (cx,      cy + 18 + flame_h),
        (cx + 6,  cy + 18),
    ]
    pygame.draw.polygon(screen, ORANGE, flame_pts)
    inner_flame_pts = [
        (cx - 3,  cy + 18),
        (cx,      cy + 18 + int(flame_h * 0.6)),
        (cx + 3,  cy + 18),
    ]
    pygame.draw.polygon(screen, YELLOW, inner_flame_pts)


def draw_menu_enemy(x, y, pulse):
    """
    Vykreslí zjednodušeného Space Invaders nepřítele (pixel art styl).
    pulse je fáze animace – tělo lehce pulzuje.
    """
    # Malý "blink" efekt – každou chvíli se změní alfa/barva
    glow = int(180 + 60 * math.sin(pulse))
    col  = (glow, 0, glow)          # Fialová s pulzem
    body = (glow // 2, glow, glow)  # Tyrkysová varianta

    ix, iy = int(x), int(y)

    # ── Hlavní tělo (obdélník) ────────────────────────────────
    pygame.draw.rect(screen, col, (ix - 14, iy - 8, 28, 16))

    # ── Oči (dva čtverečky) ───────────────────────────────────
    pygame.draw.rect(screen, YELLOW, (ix - 9, iy - 5, 5, 5))
    pygame.draw.rect(screen, YELLOW, (ix + 4,  iy - 5, 5, 5))

    # ── Antény (čáry nahoru) ──────────────────────────────────
    pygame.draw.line(screen, body, (ix - 10, iy - 8), (ix - 16, iy - 18), 2)
    pygame.draw.line(screen, body, (ix + 10, iy - 8), (ix + 16, iy - 18), 2)

    # ── Nožičky dole ──────────────────────────────────────────
    pygame.draw.line(screen, col, (ix - 12, iy + 8), (ix - 18, iy + 14), 2)
    pygame.draw.line(screen, col, (ix,      iy + 8), (ix,       iy + 14), 2)
    pygame.draw.line(screen, col, (ix + 12, iy + 8), (ix + 18, iy + 14), 2)


def update_menu_animations():
    """
    Aktualizuje všechny animace v menu:
      - pohyb raketky (sinusoidní float nahoru/dolů)
      - pohyb dekorativních nepřátel (odrážení od okrajů)
      - fázi pulzu titulku
    """
    global menu_rocket_y, menu_title_pulse

    # Raketka jemně pluje nahoru/dolů (sinusovka)
    menu_title_pulse += 0.04
    menu_rocket_y = math.sin(menu_title_pulse) * 14  # ±14 pixelů

    # Dekorativní nepřátelé se pohybují vlevo-vpravo a odrážejí od okrajů
    for e in menu_enemies:
        e["x"]     += e["vx"]
        e["pulse"] += 0.05
        if e["x"] < 40 or e["x"] > WIDTH - 40:
            e["vx"] *= -1   # Otočení směru při nárazu do okraje


def draw_menu():
    """
    Vykreslí kompletní menu obrazovku:
      1. Hvězdné pozadí
      2. Dekorativní pás ve spodní části
      3. Animovaní nepřátelé
      4. Raketka hráče
      5. Titulek hry s barevným pulzem
      6. Klikatelná tlačítka menu
    """
    global menu_rects

    # ── 1. Hvězdné pozadí ──────────────────────────────────────
    screen.fill(DEEP_BLUE)
    draw_stars()

    # ── 2. Dekorativní pruh ve spodní části obrazovky ──────────
    # Tento pruh vizuálně odděluje menu od "vesmíru" dole
    strip_y = int(HEIGHT * 0.50)
    strip_surf = pygame.Surface((WIDTH, HEIGHT - strip_y), pygame.SRCALPHA)
    strip_surf.fill((10, 0, 30, 160))   # Tmavě fialová s průhledností
    screen.blit(strip_surf, (0, strip_y))
    # Tenká svítící čára na okraji pruhu
    pygame.draw.line(screen, PURPLE, (0, strip_y), (WIDTH, strip_y), 2)

    # ── 3. Dekorativní nepřátelé ──────────────────────────────
    for e in menu_enemies:
        draw_menu_enemy(e["x"], e["y"], e["pulse"])

    # ── 4. Raketka hráče ──────────────────────────────────────
    # Raketka je umístěna vpravo od titulku, pluje nahoru/dolů
    rocket_cx = int(WIDTH * 0.75)
    rocket_cy = int(HEIGHT * 0.27) + int(menu_rocket_y)
    draw_menu_rocket(rocket_cx, rocket_cy)

    # Malá záře pod raketkou (světelný efekt trysky)
    glow_alpha = int(80 + 40 * math.sin(menu_title_pulse * 3))
    glow_surf  = pygame.Surface((60, 30), pygame.SRCALPHA)
    pygame.draw.ellipse(glow_surf, (*ORANGE, glow_alpha), (0, 0, 60, 30))
    screen.blit(glow_surf, (rocket_cx - 30, rocket_cy + 20))

    # ── 5. Titulek hry ────────────────────────────────────────
    # Titulek "SPACE INVADERS" mění barvu pomocí sinusovky
    t = menu_title_pulse
    title_col = (
        int(180 + 75 * math.sin(t)),               # Červená složka
        int(80  + 80 * math.sin(t + 2)),            # Zelená složka
        255                                          # Modrá stálá
    )
    # Stín titulku (posunutý o 3px) – dává hloubku textu
    shadow = title_font.render("SPACE INVADERS", True, (0, 0, 80))
    main_t = title_font.render("SPACE INVADERS", True, title_col)
    tx = WIDTH // 2 - main_t.get_width() // 2
    ty = int(HEIGHT * 0.10)
    screen.blit(shadow, (tx + 3, ty + 3))
    screen.blit(main_t, (tx, ty))

    # Podtitulek pod titulkem
    sub = font.render("– Arcade Edition –", True, CYAN)
    screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, ty + main_t.get_height() + 4))

    # ── 6. Menu tlačítka ──────────────────────────────────────
    menu_rects.clear()
    mouse_pos = pygame.mouse.get_pos()   # Aktuální pozice kurzoru myši

    # Barvy tlačítek – každá položka menu má svou barvu
    btn_colors = [CYAN, YELLOW, RED]

    for i, item in enumerate(menu_items):
        # Vypočítáme pozici tlačítka (centrováno)
        bx = WIDTH  // 2
        by = int(HEIGHT * 0.44) + i * 64

        btn_w, btn_h = 260, 48
        btn_rect = pygame.Rect(bx - btn_w // 2, by - btn_h // 2, btn_w, btn_h)
        col      = btn_colors[i]

        # Hover efekt: když je myš nad tlačítkem, zvýrazníme ho
        hovered = btn_rect.collidepoint(mouse_pos)

        if hovered:
            # Tlačítko je podsvícené – plná barva s obrysem
            pygame.draw.rect(screen, col, btn_rect, border_radius=6)
            text_surf = font.render(item, True, BLACK)
        else:
            # Normální stav – průhledné s barevným obrysem
            overlay = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            overlay.fill((*col, 40))   # Jemné barevné tónování pozadí
            screen.blit(overlay, btn_rect.topleft)
            pygame.draw.rect(screen, col, btn_rect, 2, border_radius=6)
            text_surf = font.render(item, True, col)

        # Vykreslíme text tlačítka na střed
        screen.blit(text_surf,
                    (btn_rect.centerx - text_surf.get_width()  // 2,
                     btn_rect.centery - text_surf.get_height() // 2))

        menu_rects.append((item, btn_rect))   # Uložíme pro detekci kliknutí

    # Tip na ovládání dole
    tip = small_font.render("WASD pohyb  |  MEZERNÍK střelba  |  ESC pauza", True, GRAY)
    screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT - 24))


# ===================================================================
# ===== PADAJÍCÍ PŘEDMĚTY (POWERUPY) =====
# Collectible = předmět, který hráč může sebrat pro bonus
# ===================================================================
class Collectible:
    """
    Třída reprezentující padající powerup.
    Druhy (kind):
      - "autoshoot" : automatická střelba po dobu 10s
      - "shield"    : štít před projektily po dobu 15s
      - "heart"     : +1 život
      - "wrench"    : +2 HP základny
    """
    def __init__(self, kind):
        self.kind  = kind
        x          = random.randint(40, WIDTH - 80)    # Náhodná x-pozice spawnu
        self.rect  = pygame.Rect(x, -40, 36, 36)        # Spawnuje se nad obrazovkou
        self.speed = 2.5                                  # Rychlost pádu dolů
        self.pulse = random.uniform(0, math.pi * 2)      # Náhodná počáteční fáze pulzu

    def move(self):
        """Posune powerup o krok dolů a aktualizuje animaci."""
        self.rect.y   += self.speed
        self.pulse    += 0.08   # Animace pulzování (pro sin/cos výpočty)

    def draw(self, surf):
        """Vykreslí powerup na obrazovku jako kruh s ikonou."""
        cx = self.rect.centerx
        cy = self.rect.centery
        # Poloměr kruhu lehce "dýchá" pomocí sinu
        r  = 18 + math.sin(self.pulse) * 2

        if self.kind == "autoshoot":
            # Oranžovo-žlutý kruh s ikonou blesku
            pygame.draw.circle(surf, ORANGE,  (cx, cy), int(r),     0)
            pygame.draw.circle(surf, YELLOW,  (cx, cy), int(r - 4), 0)
            # Ikona blesku (polygon)
            pts = [
                (cx + 4, cy - 12), (cx - 2, cy - 2), (cx + 3, cy - 2),
                (cx - 4, cy + 12), (cx + 2, cy + 1), (cx - 3, cy + 1),
            ]
            pygame.draw.polygon(surf, WHITE, pts)
            label = small_font.render("AUTO", True, BLACK)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

        elif self.kind == "shield":
            # Tyrkysový kruh s ikonou štítu
            pygame.draw.circle(surf, CYAN,       (cx, cy), int(r),     0)
            pygame.draw.circle(surf, LIGHT_BLUE, (cx, cy), int(r - 4), 0)
            pts = [(cx, cy - 12), (cx + 10, cy - 6), (cx + 10, cy + 4),
                   (cx, cy + 13), (cx - 10, cy + 4), (cx - 10, cy - 6)]
            pygame.draw.polygon(surf, WHITE, pts)
            label = small_font.render("SHIELD", True, BLACK)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

        elif self.kind == "heart":
            # Červený kruh s ikonou srdce
            pygame.draw.circle(surf, RED,  (cx, cy), int(r),     0)
            pygame.draw.circle(surf, PINK, (cx, cy), int(r - 4), 0)
            draw_heart(surf, cx, cy, 10, RED)
            label = small_font.render("+LIFE", True, WHITE)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

        elif self.kind == "wrench":
            # Zlatý kruh s ikonou klíče (opravuje základnu)
            pygame.draw.circle(surf, GOLD,   (cx, cy), int(r),     0)
            pygame.draw.circle(surf, YELLOW, (cx, cy), int(r - 4), 0)
            pygame.draw.rect(surf, WHITE, (cx - 3, cy - 10, 6, 20), 0)
            pygame.draw.circle(surf, WHITE, (cx, cy - 10), 6, 2)
            pygame.draw.rect(surf, WHITE, (cx, cy + 4, 6, 4), 0)
            label = small_font.render("+BASE", True, BLACK)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))


def draw_heart(surf, cx, cy, size, color):
    """
    Vykreslí srdce (heart) pomocí matematické parametrické rovnice.
    cx, cy = střed srdce; size = velikost; color = barva
    """
    pts = []
    for angle in range(0, 360, 5):
        t = math.radians(angle)
        # Parametrická rovnice srdce (standardní matematický vzorec)
        x = size * (16 * math.sin(t) ** 3)
        y = -size * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        pts.append((cx + x / 16, cy + y / 16))
    if len(pts) > 2:
        pygame.draw.polygon(surf, color, pts)


collectibles          = []              # Seznam aktivních powerupů ve hře
collectible_timer     = 0               # Čítač pro spawnování dalšího powerupu
COLLECTIBLE_INTERVAL  = 8000            # Každých 8 sekund (v milisekundách)

# ===================================================================
# ===== NEPŘÁTELÉ =====
# ===================================================================
class Enemy:
    """
    Třída pro nepřátelské lodě.
    Každý nepřítel:
      - spawnuje se náhodně nahoře
      - pohybuje se dolů a vlevo/vpravo (odrazy od okrajů)
      - může střílet na hráče
      - má 1 nebo 2 životy (HP)
    """
    def __init__(self):
        sx, sy = scale_x(), scale_y()
        w, h = int(45 * sx), int(35 * sy)   # Velikost přizpůsobená rozlišení
        self.rect  = pygame.Rect(
            random.randint(50, WIDTH - 90), -40, w, h   # Spawnuje nahoře mimo obrazovku
        )
        self.hp  = random.choice([1, 2])     # 1 nebo 2 životy (náhodně)
        self.dir = random.choice([-1, 1])    # Počáteční směr pohybu (vlevo / vpravo)
        self.speed = 2                         # Rychlost pohybu

    def move(self):
        """Posune nepřítele dolů a do strany; odráží od okrajů."""
        self.rect.y += self.speed
        self.rect.x += self.dir
        # Pokud narazil na край (levý nebo pravý), obrátí směr
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.dir *= -1

    def shoot(self):
        """
        Vrátí Rect pro střelu nepřítele vystřelenou dolů z jeho středu.
        """
        return pygame.Rect(self.rect.centerx - 2, self.rect.bottom, 4, 10)


enemies       = []   # Seznam aktuálních nepřátel na obrazovce
enemy_bullets = []   # Seznam střel nepřátel (každá je Rect)

# ===================================================================
# ===== METEORITY =====
# ===================================================================
class Meteor:
    """
    Třída pro meteority.
    Velký meteorit (size 3) se po zásahu rozdělí na dva menší (size 2),
    a ty se dále rozdělí na size 1 (nejmenší, nelze dál rozbít).
    Každý kus je 5 bodů.
    """
    def __init__(self, x, y, size, vx):
        self.size   = size    # Velikost: 1 = malý, 2 = střední, 3 = velký
        # Poloměr se škáluje průměrem os – meteorit bude mít správnou velikost
        self.radius = int(size * 18 * scale_val(1))
        self.x      = x      # Počáteční x-pozice
        self.y      = y      # Počáteční y-pozice
        self.vx     = vx     # Horizontální rychlost (+ = vpravo, - = vlevo)
        self.vy     = 2 + (3 - size)   # Vertikální rychlost – menší meteority padají rychleji

    def move(self):
        """Posune meteorit o jeden herní snímek."""
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        """Vykreslí meteorit jako škálovaný obrázek."""
        img = pygame.transform.scale(
            meteor_img,
            (self.radius * 2, self.radius * 2)   # Velikost odpovídá poloměru
        )
        screen.blit(img, (self.x - self.radius, self.y - self.radius))


meteors = []   # Seznam všech meteorů na obrazovce

def spawn_meteor():
    """Spawnuje nový meteorit nahoře na náhodné x-pozici."""
    size = random.choice([2, 3])            # Velký nebo střední
    x    = random.randint(50, WIDTH - 50)   # Náhodná x-pozice
    meteors.append(Meteor(x, -50, size, random.choice([-1, 1])))


# ===================================================================
# ===== HUD (HEADS-UP DISPLAY) – informace na obrazovce během hry =====
# ===================================================================
def draw_hearts():
    """Vykreslí srdíčka reprezentující životy hráče v levém dolním rohu."""
    for i in range(lives):
        draw_heart(screen, 25 + i * 35, HEIGHT - 25, 10, RED)


def draw_hud():
    """
    Vykreslí všechny herní informace na obrazovku:
      - skóre (vpravo nahoře)
      - herní čas (nahoře uprostřed)
      - životy jako srdíčka (vlevo dole)
      - HP základny (nad základnou)
      - tlačítko PAUSE (vlevo nahoře)
      - časomíry powerupů AUTO / SHIELD (vlevo nahoře pod PAUSE)
    """
    # ── Skóre ──────────────────────────────────────────────────
    screen.blit(font.render(f"Score: {score}", True, WHITE), (WIDTH - 160, 10))

    # ── Herní čas (od startu) ────────────────────────────────
    game_time = int(time.time() - start_time)
    screen.blit(font.render(f"Time: {game_time}s", True, WHITE), (WIDTH // 2 - 60, 10))

    # ── Životy hráče (srdíčka vlevo dole) ────────────────────
    draw_hearts()

    # ── HP základny (text nad základnou) ─────────────────────
    screen.blit(font.render(f"Base HP: {base_hp}", True, WHITE),
                (base_rect.x, base_rect.y - 20))

    # ── Tlačítko PAUSE (šedý obdélník vlevo nahoře) ──────────
    pygame.draw.rect(screen, GRAY, pause_button)
    screen.blit(font.render("PAUSE", True, BLACK), (18, 18))

    # ── Časomíry aktivních powerupů ───────────────────────────
    # y_off = y-pozice pro první ukazatel (pod tlačítkem PAUSE)
    y_off = 55
    now   = time.time()

    if auto_shoot_active:
        remaining = auto_shoot_end - now
        if remaining > 0:
            # Délka pruhu odpovídá zbývajícímu času
            bar_w = int((remaining / AUTO_SHOOT_DURATION) * 160)
            pygame.draw.rect(screen, DARK_GRAY, (10, y_off, 160, 18))
            pygame.draw.rect(screen, ORANGE,    (10, y_off, bar_w, 18))
            pygame.draw.rect(screen, YELLOW,    (10, y_off, bar_w, 18), 2)  # Obrys pruhu
            label = small_font.render(f"AUTO {remaining:.1f}s", True, YELLOW)
            screen.blit(label, (12, y_off + 1))
            y_off += 26   # Posuň další ukazatel níž

    if shield_active:
        remaining = shield_end - now
        if remaining > 0:
            bar_w = int((remaining / SHIELD_DURATION) * 160)
            pygame.draw.rect(screen, DARK_GRAY, (10, y_off, 160, 18))
            pygame.draw.rect(screen, CYAN,      (10, y_off, bar_w, 18))
            pygame.draw.rect(screen, WHITE,     (10, y_off, bar_w, 18), 2)
            label = small_font.render(f"SHIELD {remaining:.1f}s", True, CYAN)
            screen.blit(label, (12, y_off + 1))


def draw_shield_effect():
    """
    Vykreslí animovaný pulzující štít okolo hráče.
    Štít je průhledný kruh, jehož jas a poloměr se mění se sinusovkou.
    """
    global shield_pulse
    shield_pulse += 0.1   # Inkrementujeme fázi animace

    # Průhlednost a poloměr se mění s časem – efekt "dýchání"
    alpha  = int(120 + 80 * math.sin(shield_pulse))
    radius = 36 + int(4 * math.sin(shield_pulse * 2))

    # Vytvoříme dočasný povrch (Surface) s alfa kanálem pro průhlednost
    shield_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(shield_surf, (*CYAN,       alpha),      (radius + 2, radius + 2), radius,     3)
    pygame.draw.circle(shield_surf, (*LIGHT_BLUE, alpha // 2), (radius + 2, radius + 2), radius - 5, 2)
    # Nakreslíme štít na pozici hráče
    screen.blit(shield_surf, (player.centerx - radius - 2, player.centery - radius - 2))


def spawn_collectible():
    """
    Náhodně vybere typ powerupu a přidá ho do hry.
    Váhy určují pravděpodobnost každého druhu (větší číslo = častější).
    """
    kinds   = ["autoshoot", "shield", "heart", "wrench"]
    weights = [30, 20, 30, 20]   # Pravděpodobnosti (celkem 100)
    kind    = random.choices(kinds, weights=weights)[0]
    collectibles.append(Collectible(kind))


# ===================================================================
# ===== ZMĚNA ROZLIŠENÍ =====
# ===================================================================
def apply_resolution():
    """
    Změní rozlišení okna hry a přepočítá všechny objekty.
    Volá se po potvrzení v nastavení (stisk ENTER).
    """
    global screen, WIDTH, HEIGHT, player, base_rect, pause_button, stars
    W, H    = RESOLUTIONS[resolution_index]
    WIDTH, HEIGHT = W, H
    flags   = pygame.FULLSCREEN if fullscreen else 0
    screen  = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    # Přepočítej pozice a obrázky podle nového rozlišení
    player       = make_player_rect()
    base_rect    = make_base_rect()
    pause_button = pygame.Rect(10, 10, 100, 40)
    load_images()   # Načti obrázky znovu ve správné velikosti
    stars = make_stars()   # Znovu vygeneruj hvězdy pro nové rozlišení


def reset_game():
    """
    Resetuje veškerý herní stav na začátek.
    Volá se při spuštění nové hry (z menu klik na 'Start').
    """
    global lives, score, start_time, base_hp, player_name, name_submitted
    global final_score, final_time
    global auto_shoot_active, auto_shoot_end, shield_active, shield_end
    global collectible_timer, auto_shoot_timer
    global player, base_rect

    lives           = 3
    base_hp         = 5
    score           = 0
    start_time      = time.time()   # Zaznamenáme čas začátku hry
    player_name     = ""
    name_submitted  = False
    final_score     = 0
    final_time      = 0
    auto_shoot_active = False
    auto_shoot_end    = 0
    shield_active     = False
    shield_end        = 0
    collectible_timer = 0
    auto_shoot_timer  = 0

    # Vyprázdníme všechny seznamy herních objektů
    enemies.clear()
    meteors.clear()
    player_bullets.clear()
    enemy_bullets.clear()
    collectibles.clear()

    # Obnov pozici a velikost hráče pro aktuální rozlišení
    player    = make_player_rect()
    base_rect = make_base_rect()


def save_highscore(name, score, game_time):
    """
    Uloží výsledek hráče do souboru highscores.json.
    Záznamy jsou seřazeny od nejvyššího skóre.
    Vrátí True při úspěchu, False při chybě.
    """
    try:
        # Pokud soubor existuje, načteme stávající záznamy
        if os.path.exists("highscores.json"):
            with open("highscores.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"highscores": []}   # Soubor neexistuje – začínáme prázdně

        # Přidáme nový záznam do seznamu
        data["highscores"].append({
            "name":  name,
            "score": score,
            "time":  game_time,
            "date":  time.strftime("%d.%m.%Y %H:%M")   # Aktuální datum a čas
        })

        # Seřadíme záznamy od nejvyššího skóre (reverse=True = sestupně)
        data["highscores"].sort(key=lambda x: x["score"], reverse=True)

        # Zapíšeme aktualizovaný seznam zpět do souboru
        with open("highscores.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    except Exception as e:
        print(f"Chyba při ukládání: {e}")
        return False


# ===================================================================
# ===== SETTINGS OBRAZOVKA =====
# ===================================================================
def draw_settings():
    """
    Vykreslí obrazovku nastavení (rozlišení + fullscreen).
    Vrátí seznam obdélníků rozlišení a obdélník fullscreen přepínače
    – potřebujeme je pro detekci kliknutí.
    """
    screen.fill(BLACK)

    # Titulek
    title = big_font.render("SETTINGS", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

    # Popisek sekce rozlišení
    res_label = font.render("Rozlišení:", True, GRAY)
    screen.blit(res_label, (WIDTH // 2 - 200, 180))

    # Vykreslíme tlačítka pro každé dostupné rozlišení
    res_rects = []
    for i, (w, h) in enumerate(RESOLUTIONS):
        label = f"{w}x{h}"
        col   = GREEN if i == resolution_index else WHITE   # Zelená = aktuální výběr
        txt   = font.render(label, True, col)
        rx    = WIDTH // 2 - 200 + (i % 3) * 160   # 3 sloupce
        ry    = 220 + (i // 3) * 50                  # 2 řádky
        r     = txt.get_rect(topleft=(rx, ry))

        if i == resolution_index:
            # Zvýrazníme aktivní rozlišení obdélníkem
            pygame.draw.rect(screen, DARK_GRAY, r.inflate(12, 8))
            pygame.draw.rect(screen, GREEN,     r.inflate(12, 8), 2)
        screen.blit(txt, r)
        res_rects.append((i, r.inflate(12, 8)))   # Uložíme pro klikání

    # ── Fullscreen přepínač ────────────────────────────────────
    fs_label = font.render("Fullscreen:", True, GRAY)
    screen.blit(fs_label, (WIDTH // 2 - 200, 340))
    fs_val      = font.render("ZAP" if fullscreen else "VYP",
                              True, GREEN if fullscreen else WHITE)
    fs_rect     = fs_val.get_rect(topleft=(WIDTH // 2 - 200 + 160, 340))
    toggle_rect = fs_rect.inflate(20, 10)
    pygame.draw.rect(screen, DARK_GRAY,                    toggle_rect)
    pygame.draw.rect(screen, GREEN if fullscreen else GRAY, toggle_rect, 2)
    screen.blit(fs_val, fs_rect)

    # Instrukce pro uložení / zrušení
    apply_txt = font.render("[ENTER] Použít & Zpět", True, YELLOW)
    screen.blit(apply_txt, (WIDTH // 2 - apply_txt.get_width() // 2, 420))
    esc_txt = font.render("[ESC] Zpět bez uložení", True, GRAY)
    screen.blit(esc_txt, (WIDTH // 2 - esc_txt.get_width() // 2, 460))

    hint = small_font.render(
        "Klikni na rozlišení pro výběr | Klikni na ZAP/VYP pro fullscreen",
        True, GRAY
    )
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 510))

    return res_rects, toggle_rect


# ===================================================================
# ===== HLAVNÍ HERNÍ SMYČKA =====
# Srdce celé hry – opakuje se 60× za sekundu (60 FPS).
# Každý průchod smyčkou:
#   1. Zpracuje eventy (kliknutí, stisky kláves…)
#   2. Aktualizuje stav hry (pohyb objektů, kolize…)
#   3. Vykreslí aktuální snímek na obrazovku
# ===================================================================
enemy_timer  = 0   # Čítač pro spawn nepřátel (ms)
meteor_timer = 0   # Čítač pro spawn meteorů (ms)
shield_pulse = 0   # Fáze animace štítu (globální sdílená proměnná)
running      = True  # False = ukončení hlavní smyčky

# Dočasné proměnné pro nastavení (aby se změny aplikovaly až po potvrzení)
tmp_resolution_index = resolution_index
tmp_fullscreen       = fullscreen

# ── MAIN LOOP ──────────────────────────────────────────────────────
while running:
    # dt = čas od posledního snímku v milisekundách (delta time)
    # Omezíme na 60 FPS – tick(60) vrátí ms od minulého snímku
    dt = clock.tick(60)

    # ── EVENT ZPRACOVÁNÍ ─────────────────────────────────────────
    # Projdeme všechny události, co se staly od posledního snímku
    for event in pygame.event.get():

        # Kliknutí na X = zavřít okno
        if event.type == pygame.QUIT:
            running = False

        # ── Eventy ve hře ──────────────────────────────────────
        if state == GAME:
            if event.type == pygame.KEYDOWN:
                # MEZERNÍK = manuální výstřel (pokud není auto-shoot)
                if event.key == pygame.K_SPACE and not auto_shoot_active:
                    player_bullets.append(
                        pygame.Rect(player.centerx - 3, player.top, 6, 12)
                    )
                # ESC = pauza
                if event.key == pygame.K_ESCAPE:
                    state = PAUSE

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Kliknutí na tlačítko PAUSE
                if pause_button.collidepoint(event.pos):
                    state = PAUSE

        # ── Eventy v pauze ─────────────────────────────────────
        elif state == PAUSE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    # C = odpočítávání před pokračováním (3, 2, 1…)
                    countdown_start = time.time()
                if event.key == pygame.K_m:
                    # M = návrat do menu
                    state = MENU

        # ── Eventy na game over obrazovce ──────────────────────
        elif state == GAME_OVER:
            if not name_submitted:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        # ENTER s neprázdným jménem = uložení highscore
                        save_highscore(player_name, final_score, final_time)
                        name_submitted = True
                    elif event.key == pygame.K_BACKSPACE:
                        # BACKSPACE = smazání posledního znaku jména
                        player_name = player_name[:-1]
                    elif event.unicode.isprintable() and len(player_name) < 15:
                        # Tisknutelný znak = přidání do jména (max 15 znaků)
                        player_name += event.unicode
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # Po uložení ENTER/MEZERNÍK = zpět do menu
                        state = MENU

        # ── Eventy v nastavení ─────────────────────────────────
        elif state == SETTINGS:
            res_rects, toggle_rect = draw_settings()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, r in res_rects:
                    if r.collidepoint(event.pos):
                        tmp_resolution_index = idx   # Vyber rozlišení
                if toggle_rect.collidepoint(event.pos):
                    tmp_fullscreen = not tmp_fullscreen  # Přepni fullscreen
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Potvrď nastavení a aplikuj nové rozlišení
                    resolution_index = tmp_resolution_index
                    fullscreen       = tmp_fullscreen
                    apply_resolution()
                    state = MENU
                elif event.key == pygame.K_ESCAPE:
                    # Zahoď změny
                    tmp_resolution_index = resolution_index
                    tmp_fullscreen       = fullscreen
                    state = MENU

    # ═══════════════════════════════════════════════════════════
    # ── VYKRESLOVÁNÍ AKTUÁLNÍHO STAVU ──────────────────────────
    # ═══════════════════════════════════════════════════════════

    # ── MENU ───────────────────────────────────────────────────
    if state == MENU:
        # Aktualizujeme a kreslíme animace menu (hvězdy + raketka + nepřátelé)
        update_stars()
        update_menu_animations()
        draw_menu()   # Celé menu nakreslí draw_menu()

        # Detekce kliknutí na tlačítka menu
        if pygame.mouse.get_pressed()[0]:
            time.sleep(0.15)   # Krátká prodleva aby se nezpracovalo kliknutí 2×
            for item, rect in menu_rects:
                if rect.collidepoint(pygame.mouse.get_pos()):
                    if item == "Start":
                        reset_game()
                        state = GAME
                    elif item == "Settings":
                        tmp_resolution_index = resolution_index
                        tmp_fullscreen       = fullscreen
                        state = SETTINGS
                    elif item == "Quit":
                        pygame.quit()
                        sys.exit()

    # ── SETTINGS ───────────────────────────────────────────────
    elif state == SETTINGS:
        # draw_settings() se volá i zde (ne jen v event sekci)
        # aby se obrazovka vykreslovala i bez eventů
        _old_ri = resolution_index
        _old_fs = fullscreen
        resolution_index = tmp_resolution_index
        fullscreen       = tmp_fullscreen
        res_rects, toggle_rect = draw_settings()
        resolution_index = _old_ri
        fullscreen       = _old_fs

    # ── HRA ────────────────────────────────────────────────────
    elif state == GAME:
        now  = time.time()
        keys = pygame.key.get_pressed()   # Přečteme aktuálně stisknuté klávesy

        # ── Pohyb hráče (WASD) ─────────────────────────────────
        if keys[pygame.K_a]: player.x -= player_speed   # Doleva
        if keys[pygame.K_d]: player.x += player_speed   # Doprava
        if keys[pygame.K_w]: player.y -= player_speed   # Nahoru
        if keys[pygame.K_s]: player.y += player_speed   # Dolů
        # Zabráníme, aby hráč odešel za okraj obrazovky
        player.clamp_ip(screen.get_rect())

        # ── Auto-střelba (powerup) ─────────────────────────────
        if auto_shoot_active and now < auto_shoot_end:
            if keys[pygame.K_SPACE]:
                auto_shoot_timer += dt   # Přičítáme uplynulý čas
                if auto_shoot_timer >= auto_shoot_interval:
                    auto_shoot_timer = 0   # Resetujeme čítač
                    player_bullets.append(
                        pygame.Rect(player.centerx - 3, player.top, 6, 12)
                    )
        else:
            if now >= auto_shoot_end:
                auto_shoot_active = False   # Powerup vypršel

        # ── Štít – kontrola vypršení ────────────────────────────
        if shield_active and now >= shield_end:
            shield_active = False

        # ── Čítače pro spawn objektů ────────────────────────────
        enemy_timer       += dt
        meteor_timer      += dt
        collectible_timer += dt

        # Každých 1,5s spawnuj nového nepřítele
        if enemy_timer > 1500:
            enemies.append(Enemy())
            enemy_timer = 0

        # Každé 3s spawnuj meteorit
        if meteor_timer > 3000:
            spawn_meteor()
            meteor_timer = 0

        # Každých ~8s (COLLECTIBLE_INTERVAL) s 75% pravděpodobností powerup
        if collectible_timer > COLLECTIBLE_INTERVAL:
            collectible_timer = 0
            if random.random() < 0.75:
                spawn_collectible()

        # ── Aktualizace nepřátel ────────────────────────────────
        for e in enemies[:]:   # [:] = kopie seznamu (bezpečné mazání za průchodu)
            e.move()
            if random.randint(0, 120) == 1:   # ~0.8% šance vystřelit každý snímek
                enemy_bullets.append(e.shoot())
            if e.rect.colliderect(base_rect):   # Nepřítel dosáhl základny
                enemies.remove(e)
                base_hp -= 1

        # ── Aktualizace meteorů ─────────────────────────────────
        for m in meteors[:]:
            m.move()
            if base_rect.collidepoint(m.x, m.y):   # Meteorit zasáhl základnu
                meteors.remove(m)
                base_hp -= 1

        # ── Pohyb střel hráče (nahoru) ──────────────────────────
        for b in player_bullets[:]:
            b.y -= 8   # Pohyb nahoru
            if b.bottom < 0:   # Opustila obrazovku nahoře – smaž
                player_bullets.remove(b)

        # ── Pohyb střel nepřátel (dolů) ─────────────────────────
        for b in enemy_bullets[:]:
            b.y += 5   # Pohyb dolů
            if b.bottom > HEIGHT:   # Opustila obrazovku dole
                enemy_bullets.remove(b)
                continue
            if b.colliderect(player):   # Zasáhla hráče
                enemy_bullets.remove(b)
                if not shield_active:   # Štít chrání před poškozením
                    lives -= 1

        # ── Kolize střel hráče s nepřáteli a meteority ──────────
        for b in player_bullets[:]:
            hit = False
            for e in enemies[:]:
                if b.colliderect(e.rect):   # Střela zasáhla nepřítele
                    if b in player_bullets:
                        player_bullets.remove(b)
                    e.hp -= 1
                    if e.hp <= 0:       # Nepřítel zemřel
                        enemies.remove(e)
                        score += 15     # +15 bodů za zlikvidování
                    hit = True
                    break
            if hit:
                continue
            for m in meteors[:]:
                # Kolize pomocí vzdálenosti (kruhový kolizní systém)
                if math.hypot(b.centerx - m.x, b.centery - m.y) < m.radius:
                    if b in player_bullets:
                        player_bullets.remove(b)
                    meteors.remove(m)
                    score += 5          # +5 bodů za zásah meteoritu
                    if m.size > 1:      # Velký/střední se rozštěpí na dva menší
                        meteors.append(Meteor(m.x, m.y, m.size - 1, -3))
                        meteors.append(Meteor(m.x, m.y, m.size - 1,  3))
                    break

        # ── Kolize nepřítele s hráčem ───────────────────────────
        for e in enemies[:]:
            if e.rect.colliderect(player):
                enemies.remove(e)
                if not shield_active:
                    lives -= 1

        # ── Kolize meteoritu s hráčem ────────────────────────────
        for m in meteors[:]:
            if math.hypot(player.centerx - m.x, player.centery - m.y) < m.radius + 20:
                meteors.remove(m)
                if not shield_active:
                    lives -= 1

        # ── Sbírání powerupů ────────────────────────────────────
        for c in collectibles[:]:
            c.move()
            if c.rect.bottom > HEIGHT:   # Odešel dole – zmiz
                collectibles.remove(c)
                continue
            if c.rect.colliderect(player):   # Hráč ho sebral
                collectibles.remove(c)
                if c.kind == "autoshoot":
                    auto_shoot_active = True
                    auto_shoot_end    = now + AUTO_SHOOT_DURATION
                    auto_shoot_timer  = 0
                elif c.kind == "shield":
                    shield_active = True
                    shield_end    = now + SHIELD_DURATION
                elif c.kind == "heart":
                    lives += 1
                elif c.kind == "wrench":
                    base_hp = min(base_hp + 2, 10)   # Max 10 HP základny

        # ── VYKRESLENÍ HERNÍ SCÉNY ──────────────────────────────
        # Pořadí vykreslování je důležité – objekty níže překryjí ty výše

        # 1. Tmavě modré pozadí (vesmír)
        screen.fill(DEEP_BLUE)

        # 2. Animované hvězdy na pozadí
        update_stars()
        draw_stars()

        # 3. Hráč (jeho loď)
        screen.blit(player_img, player)

        # 4. Štít okolo hráče (pokud je aktivní)
        if shield_active:
            draw_shield_effect()

        # 5. Nepřátelé
        for e in enemies:
            screen.blit(enemy_img, e.rect)

        # 6. Meteority
        for m in meteors:
            m.draw()

        # 7. Střely hráče (žluté)
        for b in player_bullets:
            pygame.draw.rect(screen, YELLOW, b)

        # 8. Střely nepřátel (červené)
        for b in enemy_bullets:
            pygame.draw.rect(screen, RED, b)

        # 9. Padající powerupy
        for c in collectibles:
            c.draw(screen)

        # 10. Základna dole
        screen.blit(base_img, base_rect)

        # 11. HUD – skóre, čas, životy, ukazatele powerupů
        draw_hud()

        # ── Konec hry? ──────────────────────────────────────────
        if lives <= 0 or base_hp <= 0:
            final_score = score
            final_time  = int(time.time() - start_time)
            state       = GAME_OVER

    # ── PAUZA ──────────────────────────────────────────────────
    elif state == PAUSE:
        # Ponecháme poslední herní snímek na obrazovce (screen.fill není voláno)
        # a přes něj zobrazíme pauza text

        # Zatmavíme obrazovku poloprůhlednou vrstvou
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        screen.blit(big_font.render("PAUSE", True, WHITE),
                    (WIDTH // 2 - 100, HEIGHT // 2 - 120))
        screen.blit(font.render("C - Pokračovat", True, WHITE),
                    (WIDTH // 2 - 80, HEIGHT // 2 - 20))
        screen.blit(font.render("M - Hlavní menu", True, WHITE),
                    (WIDTH // 2 - 100, HEIGHT // 2 + 20))

        # Odpočítávání 3-2-1 před návratem do hry
        if countdown_start:
            remaining = 3 - int(time.time() - countdown_start)
            if remaining <= 0:
                countdown_start = None
                state = GAME   # Spustíme hru
            else:
                screen.blit(big_font.render(str(remaining), True, RED),
                            (WIDTH // 2 - 20, HEIGHT // 2 + 80))

    # ── GAME OVER ──────────────────────────────────────────────
    elif state == GAME_OVER:
        # Tmavé pozadí s hvězdami
        screen.fill(DEEP_BLUE)
        draw_stars()

        # Velký červený nápis
        screen.blit(big_font.render("GAME OVER", True, RED),
                    (WIDTH // 2 - 180, 100))
        # Výsledky
        screen.blit(font.render(f"Final Score: {final_score}", True, WHITE),
                    (WIDTH // 2 - 100, 200))
        screen.blit(font.render(f"Time: {final_time}s", True, WHITE),
                    (WIDTH // 2 - 60, 240))

        if not name_submitted:
            # Zobraz políčko pro zadání jména
            screen.blit(font.render("Zadej své jméno:", True, WHITE),
                        (WIDTH // 2 - 100, 300))
            input_rect   = pygame.Rect(WIDTH // 2 - 150, 340, 300, 40)
            pygame.draw.rect(screen, WHITE, input_rect, 2)
            name_surface = font.render(player_name, True, WHITE)
            screen.blit(name_surface, (input_rect.x + 10, input_rect.y + 5))
            # Blikající kurzor (mění se 2× za sekundu)
            if int(time.time() * 2) % 2 == 0:
                cursor_x = input_rect.x + 10 + name_surface.get_width()
                pygame.draw.line(screen, WHITE,
                                 (cursor_x, input_rect.y + 5),
                                 (cursor_x, input_rect.y + 35), 2)
            screen.blit(small_font.render("Stiskni ENTER pro uložení", True, GRAY),
                        (WIDTH // 2 - 100, 400))
        else:
            # Jméno bylo odesláno
            screen.blit(font.render("Skóre uloženo!", True, GREEN),
                        (WIDTH // 2 - 80, 320))
            screen.blit(small_font.render("Stiskni ENTER pro pokračování", True, GRAY),
                        (WIDTH // 2 - 120, 370))

    # ── Zobrazíme hotový snímek na obrazovku ──────────────────
    # pygame.display.flip() překreslí celé okno najednou (double buffering)
    pygame.display.flip()

# ── Úklid po skončení smyčky ───────────────────────────────────────
pygame.quit()   # Uvolníme prostředky pygame
sys.exit()       # Čistě ukončíme program
