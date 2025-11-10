import pygame
import sys

# Inicializace Pygame
pygame.init()
pygame.display.set_caption("Pacman Menu")

# Rozměry okna
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Barvy
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)

# Fonty
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 50)

# Herní stavy
MENU = "menu"
START = "start"
SETTINGS = "settings"
current_state = MENU

# Tlačítka v menu
menu_items = ["Start", "Settings", "Quit"]
menu_rects = []

# "Šipka zpět" v levém horním rohu
back_button = pygame.Rect(20, 20, 60, 40)

def draw_back_arrow():
    # Trojúhelník směřující doleva nahoře
    pygame.draw.polygon(screen, YELLOW, [
        (20, 40),   # levý hrot
        (60, 20),   # pravý horní
        (60, 60)    # pravý dolní
    ])

def draw_menu():
    screen.fill(BLACK)
    title = font.render("PACMAN MENU", True, YELLOW)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

    menu_rects.clear()
    for i, item in enumerate(menu_items):
        text = small_font.render(item, True, WHITE)
        rect = text.get_rect(center=(WIDTH // 2, 250 + i * 100))
        screen.blit(text, rect)
        menu_rects.append((item, rect))

def draw_start():
    screen.fill(BLACK)
    text = font.render("Coming soon...", True, WHITE)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    draw_back_arrow()

def draw_settings():
    screen.fill(BLACK)
    title = font.render("SETTINGS", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    draw_back_arrow()

# Herní smyčka
running = True
while running:
    screen.fill(BLACK)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if current_state == MENU:
                for item, rect in menu_rects:
                    if rect.collidepoint(mouse_pos):
                        if item == "Start":
                            current_state = START
                        elif item == "Settings":
                            current_state = SETTINGS
                        elif item == "Quit":
                            pygame.quit()
                            sys.exit()

            else:  # jsme v jiném stavu (Start nebo Settings)
                if back_button.collidepoint(mouse_pos):
                    current_state = MENU

    # Vykreslení podle stavu
    if current_state == MENU:
        draw_menu()
    elif current_state == START:
        draw_start()
    elif current_state == SETTINGS:
        draw_settings()

    pygame.display.flip()

pygame.quit()
