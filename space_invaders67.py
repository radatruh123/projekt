import pygame
import sys
import random
import time
import math
import json
import os

pygame.init()

# ===== NASTAVENÍ ROZLIŠENÍ =====
RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1280, 960),
    (1600, 900),
    (1920, 1080),
]
resolution_index = 0
fullscreen = False

# ===== REFERENČNÍ ROZLIŠENÍ PRO ŠKÁLOVÁNÍ =====
REF_W, REF_H = 800, 600

WIDTH, HEIGHT = RESOLUTIONS[resolution_index]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()

# ===== BARVY =====
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
DARK_GRAY = (50, 50, 50)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
CYAN = (0, 220, 255)
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 255)
LIGHT_BLUE = (100, 180, 255)
PINK = (255, 100, 180)
GOLD = (255, 215, 0)

# ===== FONTY =====
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 24)

# ===== STAVY =====
MENU = "menu"
SETTINGS = "settings"
GAME = "game"
PAUSE = "pause"
GAME_OVER = "game_over"
state = MENU

# ===== POMOCNÉ FUNKCE PRO ŠKÁLOVÁNÍ =====
def scale_x():
    return WIDTH / REF_W

def scale_y():
    return HEIGHT / REF_H

def scale_val(val):
    """Škáluje hodnotu průměrem obou os – vhodné pro tloušťky, rádiusy apod."""
    return val * (scale_x() + scale_y()) / 2

# ===== OBRÁZKY =====
def load_images():
    global player_img, enemy_img, meteor_img, base_img
    sx, sy = scale_x(), scale_y()

    player_img = pygame.transform.scale(
        pygame.image.load("player.png").convert_alpha(),
        (int(50 * sx), int(40 * sy))
    )
    enemy_img = pygame.transform.scale(
        pygame.image.load("enemy.png").convert_alpha(),
        (int(45 * sx), int(35 * sy))
    )
    meteor_img = pygame.image.load("meteor.png").convert_alpha()
    base_img = pygame.transform.scale(
        pygame.image.load("base.png").convert_alpha(),
        (int(300 * sx), int(60 * sy))
    )

load_images()

# ===== MENU =====
menu_items = ["Start", "Settings", "Quit"]
menu_rects = []

# ===== HRÁČ =====
def make_player_rect():
    sx, sy = scale_x(), scale_y()
    return pygame.Rect(
        WIDTH // 2 - int(25 * sx),
        HEIGHT - int(120 * sy),
        int(50 * sx),
        int(40 * sy)
    )

player = make_player_rect()
player_speed = 6
player_bullets = []
lives = 3

# ===== ZÁKLADNA =====
def make_base_rect():
    sx, sy = scale_x(), scale_y()
    return pygame.Rect(
        WIDTH // 2 - int(150 * sx),
        HEIGHT - int(70 * sy),
        int(300 * sx),
        int(60 * sy)
    )

base_rect = make_base_rect()
base_hp = 5

# ===== SCORE & TIME =====
score = 0
start_time = 0
final_score = 0
final_time = 0

# ===== GAME OVER =====
player_name = ""
name_submitted = False

# ===== PAUSE =====
pause_button = pygame.Rect(10, 10, 100, 40)
countdown_start = None

# ===== POWERUPY =====
auto_shoot_active = False
auto_shoot_end = 0
AUTO_SHOOT_DURATION = 10
auto_shoot_interval = 200
auto_shoot_timer = 0

shield_active = False
shield_end = 0
SHIELD_DURATION = 15
shield_pulse = 0

# ===== PADAJÍCÍ PŘEDMĚTY =====
class Collectible:
    def __init__(self, kind):
        self.kind = kind
        x = random.randint(40, WIDTH - 80)
        self.rect = pygame.Rect(x, -40, 36, 36)
        self.speed = 2.5
        self.pulse = random.uniform(0, math.pi * 2)

    def move(self):
        self.rect.y += self.speed
        self.pulse += 0.08

    def draw(self, surf):
        cx = self.rect.centerx
        cy = self.rect.centery
        r = 18 + math.sin(self.pulse) * 2

        if self.kind == "autoshoot":
            pygame.draw.circle(surf, ORANGE, (cx, cy), int(r), 0)
            pygame.draw.circle(surf, YELLOW, (cx, cy), int(r - 4), 0)
            pts = [
                (cx + 4, cy - 12), (cx - 2, cy - 2), (cx + 3, cy - 2),
                (cx - 4, cy + 12), (cx + 2, cy + 1), (cx - 3, cy + 1),
            ]
            pygame.draw.polygon(surf, WHITE, pts)
            label = small_font.render("AUTO", True, BLACK)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

        elif self.kind == "shield":
            pygame.draw.circle(surf, CYAN, (cx, cy), int(r), 0)
            pygame.draw.circle(surf, LIGHT_BLUE, (cx, cy), int(r - 4), 0)
            pts = [(cx, cy - 12), (cx + 10, cy - 6), (cx + 10, cy + 4),
                   (cx, cy + 13), (cx - 10, cy + 4), (cx - 10, cy - 6)]
            pygame.draw.polygon(surf, WHITE, pts)
            label = small_font.render("SHIELD", True, BLACK)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

        elif self.kind == "heart":
            pygame.draw.circle(surf, RED, (cx, cy), int(r), 0)
            pygame.draw.circle(surf, PINK, (cx, cy), int(r - 4), 0)
            draw_heart(surf, cx, cy, 10, RED)
            label = small_font.render("+LIFE", True, WHITE)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

        elif self.kind == "wrench":
            pygame.draw.circle(surf, GOLD, (cx, cy), int(r), 0)
            pygame.draw.circle(surf, YELLOW, (cx, cy), int(r - 4), 0)
            pygame.draw.rect(surf, WHITE, (cx - 3, cy - 10, 6, 20), 0)
            pygame.draw.circle(surf, WHITE, (cx, cy - 10), 6, 2)
            pygame.draw.rect(surf, WHITE, (cx, cy + 4, 6, 4), 0)
            label = small_font.render("+BASE", True, BLACK)
            surf.blit(label, (cx - label.get_width() // 2, cy + int(r) + 2))

def draw_heart(surf, cx, cy, size, color):
    pts = []
    for angle in range(0, 360, 5):
        t = math.radians(angle)
        x = size * (16 * math.sin(t) ** 3)
        y = -size * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        pts.append((cx + x / 16, cy + y / 16))
    if len(pts) > 2:
        pygame.draw.polygon(surf, color, pts)

collectibles = []
collectible_timer = 0
COLLECTIBLE_INTERVAL = 8000

# ===== NEPŘÁTELÉ =====
class Enemy:
    def __init__(self):
        sx, sy = scale_x(), scale_y()
        w, h = int(45 * sx), int(35 * sy)
        self.rect = pygame.Rect(
            random.randint(50, WIDTH - 90), -40, w, h
        )
        self.hp = random.choice([1, 2])
        self.dir = random.choice([-1, 1])
        self.speed = 2

    def move(self):
        self.rect.y += self.speed
        self.rect.x += self.dir
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.dir *= -1

    def shoot(self):
        return pygame.Rect(self.rect.centerx - 2, self.rect.bottom, 4, 10)

enemies = []
enemy_bullets = []

# ===== METEORITY =====
class Meteor:
    def __init__(self, x, y, size, vx):
        self.size = size
        # Poloměr meteoritu se škáluje průměrem os
        self.radius = int(size * 18 * scale_val(1))
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = 2 + (3 - size)

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        img = pygame.transform.scale(
            meteor_img,
            (self.radius * 2, self.radius * 2)
        )
        screen.blit(img, (self.x - self.radius, self.y - self.radius))

meteors = []

def spawn_meteor():
    size = random.choice([2, 3])
    x = random.randint(50, WIDTH - 50)
    meteors.append(Meteor(x, -50, size, random.choice([-1, 1])))

# ===== FUNKCE =====
def draw_hearts():
    for i in range(lives):
        draw_heart(screen, 25 + i * 35, HEIGHT - 25, 10, RED)

def apply_resolution():
    global screen, WIDTH, HEIGHT, player, base_rect, pause_button
    W, H = RESOLUTIONS[resolution_index]
    WIDTH, HEIGHT = W, H
    flags = pygame.FULLSCREEN if fullscreen else 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    # Přepočítej recty a obrázky podle nového rozlišení
    player = make_player_rect()
    base_rect = make_base_rect()
    pause_button = pygame.Rect(10, 10, 100, 40)
    load_images()  # Znovu načti obrázky ve správné velikosti

def reset_game():
    global lives, score, start_time, base_hp, player_name, name_submitted, final_score, final_time
    global auto_shoot_active, auto_shoot_end, shield_active, shield_end
    global collectible_timer, auto_shoot_timer
    global player, base_rect
    lives = 3
    base_hp = 5
    score = 0
    start_time = time.time()
    player_name = ""
    name_submitted = False
    final_score = 0
    final_time = 0
    auto_shoot_active = False
    auto_shoot_end = 0
    shield_active = False
    shield_end = 0
    collectible_timer = 0
    auto_shoot_timer = 0
    enemies.clear()
    meteors.clear()
    player_bullets.clear()
    enemy_bullets.clear()
    collectibles.clear()
    # Obnov pozici i velikost hráče podle aktuálního rozlišení
    player = make_player_rect()
    base_rect = make_base_rect()

def save_highscore(name, score, game_time):
    try:
        if os.path.exists("highscores.json"):
            with open("highscores.json", "r", encoding="utf-8") as f:
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
        with open("highscores.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Chyba při ukládání: {e}")
        return False

def draw_hud():
    screen.blit(font.render(f"Score: {score}", True, WHITE), (WIDTH - 160, 10))
    game_time = int(time.time() - start_time)
    screen.blit(font.render(f"Time: {game_time}s", True, WHITE), (WIDTH // 2 - 60, 10))
    draw_hearts()
    screen.blit(font.render(f"Base HP: {base_hp}", True, WHITE), (base_rect.x, base_rect.y - 20))
    pygame.draw.rect(screen, GRAY, pause_button)
    screen.blit(font.render("PAUSE", True, BLACK), (18, 18))

    y_off = 55
    now = time.time()

    if auto_shoot_active:
        remaining = auto_shoot_end - now
        if remaining > 0:
            bar_w = int((remaining / AUTO_SHOOT_DURATION) * 160)
            pygame.draw.rect(screen, DARK_GRAY, (10, y_off, 160, 18))
            pygame.draw.rect(screen, ORANGE, (10, y_off, bar_w, 18))
            pygame.draw.rect(screen, YELLOW, (10, y_off, bar_w, 18), 2)
            label = small_font.render(f"AUTO {remaining:.1f}s", True, YELLOW)
            screen.blit(label, (12, y_off + 1))
            y_off += 26

    if shield_active:
        remaining = shield_end - now
        if remaining > 0:
            bar_w = int((remaining / SHIELD_DURATION) * 160)
            pygame.draw.rect(screen, DARK_GRAY, (10, y_off, 160, 18))
            pygame.draw.rect(screen, CYAN, (10, y_off, bar_w, 18))
            pygame.draw.rect(screen, WHITE, (10, y_off, bar_w, 18), 2)
            label = small_font.render(f"SHIELD {remaining:.1f}s", True, CYAN)
            screen.blit(label, (12, y_off + 1))

def draw_shield_effect():
    global shield_pulse
    shield_pulse += 0.1
    alpha = int(120 + 80 * math.sin(shield_pulse))
    radius = 36 + int(4 * math.sin(shield_pulse * 2))
    shield_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(shield_surf, (*CYAN, alpha), (radius + 2, radius + 2), radius, 3)
    pygame.draw.circle(shield_surf, (*LIGHT_BLUE, alpha // 2), (radius + 2, radius + 2), radius - 5, 2)
    screen.blit(shield_surf, (player.centerx - radius - 2, player.centery - radius - 2))

def spawn_collectible():
    kinds = ["autoshoot", "shield", "heart", "wrench"]
    weights = [30, 20, 30, 20]
    kind = random.choices(kinds, weights=weights)[0]
    collectibles.append(Collectible(kind))

# ===== SETTINGS FUNKCE =====
def draw_settings():
    screen.fill(BLACK)
    title = big_font.render("SETTINGS", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

    res_label = font.render("Rozlišení:", True, GRAY)
    screen.blit(res_label, (WIDTH // 2 - 200, 180))

    res_rects = []
    for i, (w, h) in enumerate(RESOLUTIONS):
        label = f"{w}x{h}"
        col = GREEN if i == resolution_index else WHITE
        txt = font.render(label, True, col)
        rx = WIDTH // 2 - 200 + (i % 3) * 160
        ry = 220 + (i // 3) * 50
        r = txt.get_rect(topleft=(rx, ry))
        if i == resolution_index:
            pygame.draw.rect(screen, DARK_GRAY, r.inflate(12, 8))
            pygame.draw.rect(screen, GREEN, r.inflate(12, 8), 2)
        screen.blit(txt, r)
        res_rects.append((i, r.inflate(12, 8)))

    fs_label = font.render("Fullscreen:", True, GRAY)
    screen.blit(fs_label, (WIDTH // 2 - 200, 340))
    fs_val = font.render("ZAP" if fullscreen else "VYP", True, GREEN if fullscreen else WHITE)
    fs_rect = fs_val.get_rect(topleft=(WIDTH // 2 - 200 + 160, 340))
    toggle_rect = fs_rect.inflate(20, 10)
    pygame.draw.rect(screen, DARK_GRAY, toggle_rect)
    pygame.draw.rect(screen, GREEN if fullscreen else GRAY, toggle_rect, 2)
    screen.blit(fs_val, fs_rect)

    apply_txt = font.render("[ENTER] Použít & Zpět", True, YELLOW)
    screen.blit(apply_txt, (WIDTH // 2 - apply_txt.get_width() // 2, 420))
    esc_txt = font.render("[ESC] Zpět bez uložení", True, GRAY)
    screen.blit(esc_txt, (WIDTH // 2 - esc_txt.get_width() // 2, 460))

    hint = small_font.render("Klikni na rozlišení pro výběr | Klikni na ZAP/VYP pro fullscreen", True, GRAY)
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 510))

    return res_rects, toggle_rect

# ===== HLAVNÍ SMYČKA =====
enemy_timer = 0
meteor_timer = 0
shield_pulse = 0
running = True

tmp_resolution_index = resolution_index
tmp_fullscreen = fullscreen

while running:
    dt = clock.tick(60)
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if state == GAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not auto_shoot_active:
                    player_bullets.append(
                        pygame.Rect(player.centerx - 3, player.top, 6, 12)
                    )
                if event.key == pygame.K_ESCAPE:
                    state = PAUSE

            if event.type == pygame.MOUSEBUTTONDOWN:
                if pause_button.collidepoint(event.pos):
                    state = PAUSE

        elif state == PAUSE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    countdown_start = time.time()
                if event.key == pygame.K_m:
                    state = MENU

        elif state == GAME_OVER:
            if not name_submitted:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        save_highscore(player_name, final_score, final_time)
                        name_submitted = True
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.unicode.isprintable() and len(player_name) < 15:
                        player_name += event.unicode
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = MENU

        elif state == SETTINGS:
            res_rects, toggle_rect = draw_settings()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, r in res_rects:
                    if r.collidepoint(event.pos):
                        tmp_resolution_index = idx
                if toggle_rect.collidepoint(event.pos):
                    tmp_fullscreen = not tmp_fullscreen
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    resolution_index = tmp_resolution_index
                    fullscreen = tmp_fullscreen
                    apply_resolution()  # Tady se načtou obrázky ve správném měřítku
                    state = MENU
                elif event.key == pygame.K_ESCAPE:
                    tmp_resolution_index = resolution_index
                    tmp_fullscreen = fullscreen
                    state = MENU

    # ===== MENU =====
    if state == MENU:
        title = big_font.render("SPACE INVADERS", True, GREEN)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        menu_rects.clear()
        for i, item in enumerate(menu_items):
            text = font.render(item, True, WHITE)
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 60))
            screen.blit(text, rect)
            menu_rects.append((item, rect))

        if pygame.mouse.get_pressed()[0]:
            time.sleep(0.15)
            for item, rect in menu_rects:
                if rect.collidepoint(pygame.mouse.get_pos()):
                    if item == "Start":
                        reset_game()
                        state = GAME
                    elif item == "Settings":
                        tmp_resolution_index = resolution_index
                        tmp_fullscreen = fullscreen
                        state = SETTINGS
                    elif item == "Quit":
                        pygame.quit()
                        sys.exit()

    # ===== SETTINGS =====
    elif state == SETTINGS:
        _old_ri = resolution_index
        _old_fs = fullscreen
        resolution_index = tmp_resolution_index
        fullscreen = tmp_fullscreen
        res_rects, toggle_rect = draw_settings()
        resolution_index = _old_ri
        fullscreen = _old_fs

    # ===== GAME =====
    elif state == GAME:
        now = time.time()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]: player.x -= player_speed
        if keys[pygame.K_d]: player.x += player_speed
        if keys[pygame.K_w]: player.y -= player_speed
        if keys[pygame.K_s]: player.y += player_speed
        player.clamp_ip(screen.get_rect())

        if auto_shoot_active and now < auto_shoot_end:
            if keys[pygame.K_SPACE]:
                auto_shoot_timer += dt
                if auto_shoot_timer >= auto_shoot_interval:
                    auto_shoot_timer = 0
                    player_bullets.append(
                        pygame.Rect(player.centerx - 3, player.top, 6, 12)
                    )
        else:
            if now >= auto_shoot_end:
                auto_shoot_active = False

        if shield_active and now >= shield_end:
            shield_active = False

        enemy_timer += dt
        meteor_timer += dt
        collectible_timer += dt

        if enemy_timer > 1500:
            enemies.append(Enemy())
            enemy_timer = 0

        if meteor_timer > 3000:
            spawn_meteor()
            meteor_timer = 0

        if collectible_timer > COLLECTIBLE_INTERVAL:
            collectible_timer = 0
            if random.random() < 0.75:
                spawn_collectible()

        for e in enemies[:]:
            e.move()
            if random.randint(0, 120) == 1:
                enemy_bullets.append(e.shoot())
            if e.rect.colliderect(base_rect):
                enemies.remove(e)
                base_hp -= 1

        for m in meteors[:]:
            m.move()
            if base_rect.collidepoint(m.x, m.y):
                meteors.remove(m)
                base_hp -= 1

        for b in player_bullets[:]:
            b.y -= 8
            if b.bottom < 0:
                player_bullets.remove(b)

        for b in enemy_bullets[:]:
            b.y += 5
            if b.bottom > HEIGHT:
                enemy_bullets.remove(b)
                continue
            if b.colliderect(player):
                enemy_bullets.remove(b)
                if not shield_active:
                    lives -= 1

        for b in player_bullets[:]:
            hit = False
            for e in enemies[:]:
                if b.colliderect(e.rect):
                    if b in player_bullets:
                        player_bullets.remove(b)
                    e.hp -= 1
                    if e.hp <= 0:
                        enemies.remove(e)
                        score += 15
                    hit = True
                    break
            if hit:
                continue
            for m in meteors[:]:
                if math.hypot(b.centerx - m.x, b.centery - m.y) < m.radius:
                    if b in player_bullets:
                        player_bullets.remove(b)
                    meteors.remove(m)
                    score += 5
                    if m.size > 1:
                        meteors.append(Meteor(m.x, m.y, m.size - 1, -3))
                        meteors.append(Meteor(m.x, m.y, m.size - 1, 3))
                    break

        for e in enemies[:]:
            if e.rect.colliderect(player):
                enemies.remove(e)
                if not shield_active:
                    lives -= 1

        for m in meteors[:]:
            if math.hypot(player.centerx - m.x, player.centery - m.y) < m.radius + 20:
                meteors.remove(m)
                if not shield_active:
                    lives -= 1

        for c in collectibles[:]:
            c.move()
            if c.rect.bottom > HEIGHT:
                collectibles.remove(c)
                continue
            if c.rect.colliderect(player):
                collectibles.remove(c)
                if c.kind == "autoshoot":
                    auto_shoot_active = True
                    auto_shoot_end = now + AUTO_SHOOT_DURATION
                    auto_shoot_timer = 0
                elif c.kind == "shield":
                    shield_active = True
                    shield_end = now + SHIELD_DURATION
                elif c.kind == "heart":
                    lives += 1
                elif c.kind == "wrench":
                    base_hp = min(base_hp + 2, 10)

        screen.blit(player_img, player)

        if shield_active:
            draw_shield_effect()

        for e in enemies:
            screen.blit(enemy_img, e.rect)
        for m in meteors:
            m.draw()
        for b in player_bullets:
            pygame.draw.rect(screen, YELLOW, b)
        for b in enemy_bullets:
            pygame.draw.rect(screen, RED, b)

        for c in collectibles:
            c.draw(screen)

        screen.blit(base_img, base_rect)
        draw_hud()

        if lives <= 0 or base_hp <= 0:
            final_score = score
            final_time = int(time.time() - start_time)
            state = GAME_OVER

    # ===== PAUSE =====
    elif state == PAUSE:
        screen.blit(big_font.render("PAUSE", True, WHITE),
                    (WIDTH // 2 - 100, HEIGHT // 2 - 120))
        screen.blit(font.render("C - Pokračovat", True, WHITE),
                    (WIDTH // 2 - 80, HEIGHT // 2 - 20))
        screen.blit(font.render("M - Hlavní menu", True, WHITE),
                    (WIDTH // 2 - 100, HEIGHT // 2 + 20))

        if countdown_start:
            remaining = 3 - int(time.time() - countdown_start)
            if remaining <= 0:
                countdown_start = None
                state = GAME
            else:
                screen.blit(big_font.render(str(remaining), True, RED),
                            (WIDTH // 2 - 20, HEIGHT // 2 + 80))

    # ===== GAME OVER =====
    elif state == GAME_OVER:
        screen.blit(big_font.render("GAME OVER", True, RED),
                    (WIDTH // 2 - 180, 100))
        screen.blit(font.render(f"Final Score: {final_score}", True, WHITE),
                    (WIDTH // 2 - 100, 200))
        screen.blit(font.render(f"Time: {final_time}s", True, WHITE),
                    (WIDTH // 2 - 60, 240))

        if not name_submitted:
            screen.blit(font.render("Zadej své jméno:", True, WHITE),
                        (WIDTH // 2 - 100, 300))
            input_rect = pygame.Rect(WIDTH // 2 - 150, 340, 300, 40)
            pygame.draw.rect(screen, WHITE, input_rect, 2)
            name_surface = font.render(player_name, True, WHITE)
            screen.blit(name_surface, (input_rect.x + 10, input_rect.y + 5))
            if int(time.time() * 2) % 2 == 0:
                cursor_x = input_rect.x + 10 + name_surface.get_width()
                pygame.draw.line(screen, WHITE,
                                 (cursor_x, input_rect.y + 5),
                                 (cursor_x, input_rect.y + 35), 2)
            screen.blit(small_font.render("Stiskni ENTER pro uložení", True, GRAY),
                        (WIDTH // 2 - 100, 400))
        else:
            screen.blit(font.render("Skóre uloženo!", True, GREEN),
                        (WIDTH // 2 - 80, 320))
            screen.blit(small_font.render("Stiskni ENTER pro pokračování", True, GRAY),
                        (WIDTH // 2 - 120, 370))

    pygame.display.flip()

pygame.quit()
sys.exit()