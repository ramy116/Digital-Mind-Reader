import pygame
import random
import sys
import math

# --- 1. INITIALIZE & STYLING ---
pygame.init()
pygame.font.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Digital Mind Reader: Enigma")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.SysFont("Verdana", 55, bold=True)
subtitle_font = pygame.font.SysFont("Consolas", 28)
card_font = pygame.font.SysFont("Trebuchet MS", 26, bold=True)
result_font = pygame.font.SysFont("Verdana", 65, bold=True)

# Colors
COLOR_BG = (15, 15, 25)
COLOR_TEXT_MAIN = (240, 240, 240)
COLOR_TEXT_ACCENT = (0, 255, 200)
COLOR_CARD_BORDER = (100, 100, 100)
COLOR_HIGHLIGHT = (255, 215, 0)
COLOR_BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# --- 2. ASSET LOADING ---
try:
    # This will load your background.jpg
    bg_image_raw = pygame.image.load("background.jpg").convert()
    bg_image = pygame.transform.scale(bg_image_raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_overlay.fill((0, 0, 0))
    bg_overlay.set_alpha(150)
except Exception as e:
    print(f"Background image load failed: {e}")
    bg_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_image.fill(COLOR_BG)
    bg_overlay = None

# --- 3. THEMES & STATE ---
themes = {
    "1": {"name": "Numbers (Easy)", "data": [f"[{i:02}]" for i in range(1, 22)]},
    "2": {"name": "Fruits (Medium)", "data": ["Apple", "Banana", "Cherry", "Date", "Elderberry", "Fig", "Grape",
            "Honeydew", "Kiwi", "Lemon", "Mango", "Nectarine", "Orange", "Papaya",
            "Quince", "Raspberry", "Strawberry", "Tangerine", "Ugli Fruit", "Vanilla", "Watermelon"]},
    "3": {"name": "Names (Hard)", "data": ["Samy","Ramy","Mountasser","Ibrahim","kachiha","Imad","Samir","Walid",
            "Raouf","Amine","Yasser","Mohammed","Khaled","Djamel","boualem","Ali",
            "Mourad","Hassen","Wassim","Haithem","Chiheb"]}
}

game_state = "MENU"
deck = []
round_num = 1
selection_rects = []
menu_rects = []
particles = []
reveal_phase_start = 0

def reset_game(selected_level):
    global deck, round_num, particles, reveal_phase_start, game_state
    deck = list(themes[selected_level]["data"])
    random.shuffle(deck)
    round_num = 1
    particles = []
    reveal_phase_start = 0
    game_state = "PLAYING"

# --- 4. VISUAL CLASSES & HELPERS ---
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-4, 4), random.uniform(-10, -2)
        self.life, self.color, self.size = 100, color, random.randint(3, 8)
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.2; self.life -= 1
    def draw(self, surf):
        if self.life > 0:
            alpha = int(self.life * 2.55)
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, self.color + (alpha,), (self.size, self.size), self.size)
            surf.blit(s, (self.x - self.size, self.y - self.size))

def draw_beautiful_text(surf, text, font, base_color, accent_color, x, y, center=False, glow=False):
    img = font.render(text, True, base_color)
    rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
    # Shadow
    shad = font.render(text, True, COLOR_BLACK)
    surf.blit(shad, (rect.x+2, rect.y+2))
    # Glow effect
    if glow:
        glow_img = font.render(text, True, accent_color)
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]: surf.blit(glow_img, (rect.x+ox, rect.y+oy), special_flags=pygame.BLEND_ADD)
    surf.blit(img, rect)
    return rect

def get_piles(current_deck):
    p = [[], [], []]
    for i, card in enumerate(current_deck): p[i % 3].append(card)
    return p

def draw_card_piles(surf, piles):
    global selection_rects
    selection_rects = []
    p_width, p_spacing, start_y = 300, 20, 220
    for i, pile in enumerate(piles):
        px = (SCREEN_WIDTH - (3 * p_width + 2 * p_spacing)) // 2 + i * (p_width + p_spacing)
        pr = pygame.Rect(px, start_y - 20, p_width, 360)
        is_h = pr.collidepoint(pygame.mouse.get_pos())
        # Draw Box
        s = pygame.Surface((p_width, pr.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (255,255,255, 50 if is_h else 20), (0,0,p_width, pr.height), border_radius=15)
        surf.blit(s, pr.topleft)
        pygame.draw.rect(surf, COLOR_HIGHLIGHT if is_h else COLOR_CARD_BORDER, pr, width=2, border_radius=15)
        selection_rects.append(pr)
        # Draw Pile Text
        draw_beautiful_text(surf, f"GROUP {i+1}", subtitle_font, COLOR_TEXT_ACCENT, COLOR_HIGHLIGHT, pr.centerx, start_y, center=True, glow=is_h)
        for c_idx, card in enumerate(pile):
            draw_beautiful_text(surf, str(card), card_font, COLOR_HIGHLIGHT if is_h else COLOR_TEXT_MAIN, COLOR_HIGHLIGHT, pr.centerx, start_y + 45 + (c_idx*35), center=True)

# --- 5. MAIN LOOP ---
def main():
    global game_state, round_num, deck, particles, reveal_phase_start, menu_rects
    running = True
    while running:
        t = pygame.time.get_ticks() / 1000.0
        screen.blit(bg_image, (0, 0))
        if bg_overlay:
            bg_overlay.set_alpha(130 + int(30 * math.sin(t * 2)))
            screen.blit(bg_overlay, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: game_state = "MENU"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "MENU":
                    for idx, rect in enumerate(menu_rects):
                        if rect.collidepoint(event.pos): reset_game(str(idx + 1))
                elif game_state == "PLAYING" and round_num <= 3:
                    for idx, rect in enumerate(selection_rects):
                        if rect.collidepoint(event.pos):
                            p = get_piles(deck)
                            others = [i for i in range(3) if i != idx]
                            deck = p[others[0]] + p[idx] + p[others[1]]
                            round_num += 1
                            if round_num > 3: reveal_phase_start = pygame.time.get_ticks()
                            break

        if game_state == "MENU":
            menu_rects = []
            draw_beautiful_text(screen, "CHOOSE DIFFICULTY", title_font, COLOR_HIGHLIGHT, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, 150, center=True, glow=True)
            for i, (k, v) in enumerate(themes.items()):
                ry = 300 + (i * 100)
                br = pygame.Rect(SCREEN_WIDTH//2 - 200, ry - 40, 400, 80)
                ish = br.collidepoint(pygame.mouse.get_pos())
                draw_beautiful_text(screen, v["name"], subtitle_font, COLOR_TEXT_ACCENT if ish else COLOR_TEXT_MAIN, COLOR_HIGHLIGHT, SCREEN_WIDTH//2, ry, center=True, glow=ish)
                menu_rects.append(br)

        elif game_state == "PLAYING":
            if round_num <= 3:
                draw_beautiful_text(screen, f"ROUND {round_num}", title_font, COLOR_TEXT_MAIN, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, 70, center=True, glow=True)
                draw_beautiful_text(screen, "Click the group with your item...", subtitle_font, COLOR_TEXT_MAIN, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, 140, center=True)
                draw_card_piles(screen, get_piles(deck))
            else:
                ms = pygame.time.get_ticks() - reveal_phase_start
                if ms < 2000:
                    draw_beautiful_text(screen, "READING MIND...", title_font, COLOR_HIGHLIGHT, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, center=True, glow=True)
                else:
                    if 2300 < ms < 2350:
                        for _ in range(100): particles.append(Particle(SCREEN_WIDTH//2, SCREEN_HEIGHT//2-50, random.choice([COLOR_HIGHLIGHT, COLOR_TEXT_ACCENT, WHITE])))
                    draw_beautiful_text(screen, "YOUR ITEM IS:", subtitle_font, COLOR_TEXT_MAIN, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 120, center=True)
                    draw_beautiful_text(screen, str(deck[10]), result_font, COLOR_TEXT_MAIN, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40, center=True, glow=True)
                    draw_beautiful_text(screen, "Press [R] for Menu", card_font, COLOR_TEXT_MAIN, COLOR_TEXT_ACCENT, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, center=True)
                    for p in particles[:]:
                        p.update(); p.draw(screen)
                        if p.life <= 0: particles.remove(p)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()