"""Every screen of the game. The App owns the window, audio and saved data;
each scene handles input, updates and draws itself."""
import datetime
import math
import random
import webbrowser

import pygame

from . import RELEASE_DATE, __version__, storage, ui
from .config import (ACCENT, BAD, CREATOR, DIFFICULTIES, DIFFICULTY_ORDER, DIM, EMAIL,
                     FINGER_COLORS, FINGERS, GOLD, GOOD, HEIGHT, HOME_ROW, LICENSE_NAME, MAX_MISTAKES,
                     NAME_LENGTH, RECOMMENDED_AGE, SEQUENCES_PER_ROUND, SOFT, WEBSITE, WHITE, WIDTH,
                     key_label)
from .keyboard import KeyboardView
from .logic import Game

PRAISE = ["Great!", "Nice!", "Awesome!", "Perfect!", "Super!", "Brilliant!", "Yes!", "Fantastic!"]
LOGO_COLORS = [FINGER_COLORS[k] for k in ("a", "s", "d", "f", "j", "k", "l")]


def key_from_event(event):
    """The home-row character for a key press, '' for other printable keys,
    or None for keys that don't count at all (Shift, arrows, F-keys...)."""
    if event.key == pygame.K_SEMICOLON:
        return ";"
    if pygame.K_a <= event.key <= pygame.K_z:
        return chr(event.key)
    if event.unicode and event.unicode.isprintable() and not event.unicode.isspace():
        ch = event.unicode.lower()
        return ch if ch in HOME_ROW else ""
    if event.key == pygame.K_SPACE:
        return ""
    return None


def draw_cap(surface, center, size, letter, color, light, text_size=None):
    """A single big keycap, used for the logo."""
    x, y = center
    rect = pygame.Rect(0, 0, size, size)
    rect.center = (x, y)
    depth = max(6, size // 9)
    dy = int(light * depth * 0.5)
    if light > 0.02:
        ui.glow(surface, (x, y + dy), int(size * (1.0 + 0.5 * light)), ui.scale_color(color, 0.8 * light), 1.8)
    pygame.draw.rect(surface, ui.mix((10, 10, 30), color, 0.45), rect.move(0, depth), border_radius=size // 5)
    face = rect.move(0, dy)
    col = ui.mix((30, 30, 70), color, 0.5 + 0.5 * light)
    pygame.draw.rect(surface, col, face, border_radius=size // 5)
    pygame.draw.rect(surface, ui.mix(col, WHITE, 0.12), face.inflate(-size // 7, -size // 7),
                     border_radius=size // 6)
    pygame.draw.rect(surface, ui.mix(color, WHITE, 0.3 + 0.5 * light), face, 3, border_radius=size // 5)
    tcol = ui.mix(WHITE, (20, 15, 40), light * 0.8)
    ui.draw_text(surface, letter, text_size or int(size * 0.55), tcol, (face.centerx, face.centery - 3))


class BeatClock:
    def __init__(self, bpm):
        self.beat_len = 60.0 / bpm
        self.time = 0.0
        self.next = 0.2
        self.index = 0

    def update(self, dt):
        self.time += dt
        beats = []
        while self.time >= self.next:
            beats.append(self.index)
            self.index += 1
            self.next += self.beat_len
        return beats


class Scene:
    menu_music = True     # the App plays the calm menu music under this scene
    text_input = False    # True while typing a name, so M doesn't toggle music

    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.back_rect = None

    def handle(self, event):
        pass

    def on_menu_beat(self, index):
        pass

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        pass

    def draw_back(self, surface, hint):
        self.back_rect = pygame.Rect(30, HEIGHT - 58, 120, 40)
        hover = self.back_rect.collidepoint(self.app.mouse)
        ui.panel(surface, self.back_rect, edge=ACCENT if hover else (70, 90, 170), radius=12)
        ui.draw_text(surface, "< Back", 20, WHITE if hover else SOFT, self.back_rect.center, shadow=False)
        ui.draw_text(surface, hint, 17, DIM, (WIDTH // 2 + 60, HEIGHT - 38), shadow=False)

    def clicked_back(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.back_rect
                and self.back_rect.collidepoint(event.pos))

    def heading(self, surface, text, color=ACCENT):
        ui.draw_text(surface, text, 52, WHITE, (WIDTH // 2, 62), glow=color)


# Title ---------------------------------------------------------------------------------
class TitleScene(Scene):
    ITEMS = ["play", "difficulty", "top10", "parents", "credits", "music", "quit"]

    def __init__(self, app):
        super().__init__(app)
        self.selected = 0
        self.item_rects = {}
        self.logo_light = [0.0] * 7
        self.mini = KeyboardView(app.difficulty_keys(), top=594, size=42, gap=6, show_fingers=False)
        self.mini_step = 0

    def label(self, item):
        if item == "play":
            return "PLAY"
        if item == "difficulty":
            return f"<  {DIFFICULTIES[self.app.settings['difficulty']]['label']}  >"
        if item == "top10":
            return "TOP 10"
        if item == "parents":
            return "FOR PARENTS"
        if item == "credits":
            return "CREDITS"
        if item == "music":
            return f"MUSIC: {'ON' if self.app.settings['music'] else 'OFF'}"
        return "QUIT"

    def change_difficulty(self, step):
        order = DIFFICULTY_ORDER
        i = order.index(self.app.settings["difficulty"])
        self.app.settings["difficulty"] = order[(i + step) % len(order)]
        storage.save_settings(self.app.settings)
        self.mini.active = set(self.app.difficulty_keys())
        self.app.audio.play("move", 0.5)

    def activate(self, item):
        app = self.app
        if item == "play":
            app.audio.play("start", 0.8)
            app.goto(PlayScene(app))
        elif item == "difficulty":
            self.change_difficulty(1)
        elif item == "top10":
            app.audio.play("select", 0.6)
            app.goto(TopTenScene(app))
        elif item == "parents":
            app.audio.play("select", 0.6)
            app.goto(ParentsScene(app))
        elif item == "credits":
            app.audio.play("select", 0.6)
            app.goto(CreditsScene(app))
        elif item == "music":
            app.toggle_music()
        elif item == "quit":
            app.running = False

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.ITEMS)
                self.app.audio.play("move", 0.5)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.ITEMS)
                self.app.audio.play("move", 0.5)
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                step = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
                if self.ITEMS[self.selected] == "difficulty":
                    self.change_difficulty(step)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.activate(self.ITEMS[self.selected])
            elif event.key == pygame.K_ESCAPE:
                self.app.running = False
        elif event.type == pygame.MOUSEMOTION:
            for item, rect in self.item_rects.items():
                if rect.collidepoint(event.pos) and self.ITEMS[self.selected] != item:
                    self.selected = self.ITEMS.index(item)
                    self.app.audio.play("move", 0.3)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for item, rect in self.item_rects.items():
                if rect.collidepoint(event.pos):
                    if item == "difficulty":
                        self.change_difficulty(-1 if event.pos[0] < rect.centerx else 1)
                    else:
                        self.activate(item)

    def on_menu_beat(self, index):
        self.logo_light[index % 7] = 1.0
        keys = sorted(self.mini.active, key=HOME_ROW.index)
        if index % 2 == 0 and keys:
            self.mini.flash(keys[self.mini_step % len(keys)], 0.25)
            self.mini_step += 1

    def update(self, dt):
        super().update(dt)
        self.logo_light = [max(0.0, v - dt * 1.8) for v in self.logo_light]
        self.mini.update(dt)

    def draw(self, surface):
        app = self.app
        # Logo: KEY RUSH on keycaps that light up with the beat
        size, gap = 92, 14
        letters = "KEYRUSH"
        total = 7 * size + 6 * gap + 40
        x = (WIDTH - total) // 2 + size // 2
        for i, letter in enumerate(letters):
            bob = math.sin(self.t * 2 + i * 0.6) * 4
            draw_cap(surface, (x, 108 + bob), size, letter, LOGO_COLORS[i], self.logo_light[i])
            x += size + gap + (40 if i == 2 else 0)
        ui.draw_text(surface, "Watch.  Remember.  Type it back!", 24, SOFT, (WIDTH // 2, 192), shadow=False)

        self.item_rects = {}
        y = 244
        for i, item in enumerate(self.ITEMS):
            sel = i == self.selected
            text = self.label(item)
            rect = pygame.Rect(0, 0, 380, 44)
            rect.center = (WIDTH // 2, y)
            self.item_rects[item] = rect
            if sel:
                k = 0.5 + 0.5 * math.sin(self.t * 5)
                ui.panel(surface, rect, color=(40, 50, 120), edge=ui.mix(ACCENT, WHITE, k * 0.4), radius=14)
                ui.draw_text(surface, text, 30, WHITE, rect.center, glow=ACCENT)
            else:
                ui.draw_text(surface, text, 26, SOFT, rect.center)
            if item == "difficulty":
                blurb = DIFFICULTIES[app.settings["difficulty"]]["blurb"]
                if sel:
                    ui.draw_text(surface, blurb, 17, GOLD, (WIDTH // 2, y + 31), shadow=False)
                y += 16
            y += 46

        self.mini.draw(surface)
        ui.draw_text(surface, "Rest your fingers on  A S D F    J K L ;", 18, SOFT, (WIDTH // 2, 668), shadow=False)

        hi = storage.high_score(app.scores, app.settings["difficulty"])
        ui.draw_text(surface, f"HIGH SCORE  {hi}", 22, GOLD, (WIDTH - 40, 30), anchor="topright")
        ui.draw_text(surface, f"Recommended ages {RECOMMENDED_AGE}", 18, GOOD, (40, 34), anchor="topleft", shadow=False)
        ui.draw_text(surface, f"v{__version__}", 16, DIM, (WIDTH - 24, HEIGHT - 14), anchor="bottomright", shadow=False)
        ui.draw_text(surface, "Arrows + Enter, or the mouse  ·  M music  ·  F11 full screen", 16, DIM,
                     (24, HEIGHT - 14), anchor="bottomleft", shadow=False)
        if not app.audio.ready and app.audio.enabled:
            ui.draw_text(surface, "Tuning instruments...", 16, DIM, (WIDTH // 2, HEIGHT - 14),
                         anchor="midbottom", shadow=False)


# Play ----------------------------------------------------------------------------------
class PlayScene(Scene):
    menu_music = False

    def __init__(self, app, difficulty=None):
        super().__init__(app)
        self.difficulty = difficulty or app.settings["difficulty"]
        self.game = Game(self.difficulty, rng=random.Random(app.seed) if app.seed is not None else None)
        self.keyboard = KeyboardView(self.game.keys)
        self.particles = ui.Particles()
        self.popups = ui.Popups()
        self.banner = "Get ready..."
        self.banner_color = ACCENT
        self.banner_t = 0.0
        self.sub = "Put your fingers on the home row"
        self.dots_lit = 0
        self.shake = 0.0
        self.paused = False
        self.over_timer = None
        self.recorded = False
        self.round_flash = 0.0
        self.bot_wait = 0.0
        self.bot_rng = random.Random(5)
        self.high = storage.high_score(app.scores, self.difficulty)
        app.audio.stop_pads(600)
        app.music.start()
        app.music.intensity = 1
        app.music.sparkles = False
        app.music.clear()

    def set_banner(self, text, color, sub=None):
        self.banner = text
        self.banner_color = color
        self.banner_t = 0.0
        if sub is not None:
            self.sub = sub

    def record(self, finished):
        if self.recorded:
            return
        self.recorded = True
        if finished or self.game.time > 5:
            storage.record_game(self.app.stats, self.game.summary(), finished)

    def quit_to_title(self):
        self.record(False)
        self.app.music.clear()
        self.app.goto(TitleScene(self.app))

    def handle(self, event):
        if event.type == pygame.WINDOWFOCUSLOST and not self.game.over:
            self.paused = True
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.paused:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.paused = False
            elif event.key == pygame.K_q:
                self.quit_to_title()
            return
        if event.key == pygame.K_ESCAPE:
            if not self.game.over:
                self.paused = True
            return
        key = key_from_event(event)
        if key is None:
            return
        self.press(key)

    def press(self, key):
        if key == "":
            key = "?"
        self.game.press(key)

    def update(self, dt):
        super().update(dt)
        if self.paused:
            return
        g = self.game
        if self.app.autoplay:
            self.autoplay(dt)
        g.update(dt)
        for event in g.take_events():
            self.on_event(event)
        self.app.music.update(dt)
        self.keyboard.update(dt)
        self.particles.update(dt)
        self.popups.update(dt)
        self.banner_t += dt
        self.shake = max(0.0, self.shake - dt * 2.5)
        self.round_flash = max(0.0, self.round_flash - dt * 0.7)
        if self.over_timer is not None:
            self.over_timer -= dt
            if self.over_timer <= 0:
                self.app.goto(GameOverScene(self.app, g))

    def autoplay(self, dt):
        """The smoke test's player: mostly right, with the odd slip."""
        g = self.game
        if g.expected_key is None:
            self.bot_wait = 0.25
            return
        self.bot_wait -= dt
        if self.bot_wait <= 0:
            self.bot_wait = 0.22
            key = g.expected_key
            if self.bot_rng.random() < self.app.autoplay_error_rate:
                key = next(k for k in g.keys if k != key) if len(g.keys) > 1 else ";"
            self.press(key)

    def on_event(self, event):
        app, kb, g = self.app, self.keyboard, self.game
        kind = event[0]
        if kind == "beat":
            app.music.sparkles = g.state == "input"
            app.music.intensity = min(5, 1 + (g.round - 1))
            app.music.on_beat(event[1], event[2])
            app.bg.pulse(0.6)
            kb.beat()
        elif kind == "flash":
            _, key, duration, pos = event
            if pos == 0:
                self.dots_lit = 0
                self.set_banner("WATCH", ACCENT, "Remember the keys that light up")
            self.dots_lit = pos + 1
            kb.flash(key, duration)
            app.audio.key(key, 0.85)
        elif kind == "your_turn":
            self.dots_lit = 0
            self.set_banner("YOUR TURN", GOLD, "Type the keys in the same order")
        elif kind == "ok":
            _, key, pos = event
            kb.tap(key, True)
            app.audio.key(key, 0.75)
            self.dots_lit = pos + 1
            x, y = kb.center(key)
            self.particles.burst(x, y - 30, FINGER_COLORS[key], 10, 180, 0.5, 4)
        elif kind == "wrong":
            _, expected, pressed = event
            if pressed in HOME_ROW:
                kb.tap(pressed, False)
            kb.show_hint(expected, 1.4)
            app.audio.play("wrong", 0.7)
            app.bg.flash(BAD)
            self.shake = 1.0
            self.popups.add(f"-{10}", (WIDTH // 2 + 220, 190), BAD)
            left = g.lives
            why = "Too slow!" if pressed is None else "Oops!"
            if left > 0:
                more = f"{left} heart{'s' if left != 1 else ''} left - watch again"
                self.set_banner(why, BAD, f"It was {key_label(expected)}  ({FINGERS[expected]}).  {more}")
            else:
                self.set_banner("GAME OVER", BAD, f"It was {key_label(expected)}  ({FINGERS[expected]})")
        elif kind == "sequence_done":
            app.audio.play("success", 0.55)
            self.popups.add(f"+{event[1]}", (WIDTH // 2 + 220, 190), GOOD)
            for key in set(g.sequence):
                x, y = kb.center(key)
                self.particles.burst(x, y - 20, FINGER_COLORS[key], 16, 300, 0.9, 5)
            self.set_banner(random.choice(PRAISE), GOOD, "")
        elif kind == "round_up":
            app.audio.play("round_up", 0.7)
            self.round_flash = 1.0
            self.set_banner(f"ROUND {event[1]}", GOLD, "Faster and longer - you can do it!")
            for i in range(6):
                self.particles.burst(160 + i * 192, 300, LOGO_COLORS[i], 14, 340, 1.1, 5)
        elif kind == "off_row":
            app.audio.play("off_row", 0.4)
            if g.state != "input":
                self.set_banner(self.banner, self.banner_color, "Keep your fingers on the home row")
            else:
                self.sub = "Keep your fingers on the home row"
        elif kind == "early":
            app.audio.key(event[1], 0.25)
            if g.state == "show":
                self.sub = "Wait - watch first, then type"
        elif kind == "game_over":
            app.audio.play("game_over", 0.8)
            app.audio.stop_pads(2500)
            app.music.intensity = 0
            self.over_timer = 2.6
            self.record(True)

    # Drawing ------------------------------------------------------------------------
    def draw(self, surface):
        g = self.game
        ox = int(math.sin(self.t * 70) * 8 * self.shake)
        layer = surface if ox == 0 else surface.copy()
        if ox:
            self.app.bg.draw(layer)

        self.draw_hud(layer)
        # Banner
        k = ui.ease_out_back(min(1.0, self.banner_t * 3.5))
        size = max(10, int(64 * (0.6 + 0.4 * k)))
        ui.draw_text(layer, self.banner, size, WHITE, (WIDTH // 2, 200), glow=self.banner_color,
                     glow_strength=2 if self.banner_t < 0.4 else 1)
        if self.sub:
            ui.draw_text(layer, self.sub, 22, SOFT, (WIDTH // 2, 254), shadow=False)

        # Sequence dots
        n = len(g.sequence)
        spacing = min(40, 900 // max(1, n))
        x0 = WIDTH // 2 - (n - 1) * spacing / 2
        for i in range(n):
            lit = i < self.dots_lit
            c = (int(x0 + i * spacing), 300)
            if lit:
                col = GOLD if g.state == "input" or g.state == "success" else ACCENT
                ui.glow(layer, c, 22, ui.scale_color(col, 0.6), 2)
                pygame.draw.circle(layer, col, c, 9)
            else:
                pygame.draw.circle(layer, (60, 66, 110), c, 9, 2)

        # Time bar for each key
        if g.state == "input":
            frac = g.time_left_fraction
            bar = pygame.Rect(WIDTH // 2 - 300, 332, 600, 12)
            pygame.draw.rect(layer, (30, 34, 70), bar, border_radius=6)
            col = GOOD if frac > 0.5 else (GOLD if frac > 0.25 else BAD)
            fill = bar.copy()
            fill.w = int(bar.w * frac)
            if fill.w > 0:
                pygame.draw.rect(layer, col, fill, border_radius=6)

        self.keyboard.draw(layer)
        self.particles.draw(layer)
        self.popups.draw(layer)

        ui.draw_text(layer, "Fingers rest on  A S D F    J K L ;   - thumbs on the space bar", 18, DIM,
                     (WIDTH // 2, 600), shadow=False)
        ui.draw_text(layer, "Esc pause  ·  M music", 16, DIM, (24, HEIGHT - 14), anchor="bottomleft", shadow=False)

        if self.round_flash > 0:
            ui.draw_text(layer, f"ROUND {g.round}", int(110 + 40 * (1 - self.round_flash)), WHITE,
                         (WIDTH // 2, HEIGHT // 2 - 40), glow=GOLD, alpha=int(200 * self.round_flash), shadow=False)

        if ox:
            surface.blit(layer, (ox, 0))
        if self.paused:
            self.draw_pause(surface)

    def draw_hud(self, surface):
        g = self.game
        ui.panel(surface, (24, 14, WIDTH - 48, 76), radius=20)
        ui.draw_text(surface, "SCORE", 16, SOFT, (60, 26), anchor="topleft", shadow=False)
        ui.draw_text(surface, f"{g.score}", 38, WHITE, (60, 40), anchor="topleft", glow=ACCENT)
        hi = max(self.high, g.score)
        ui.draw_text(surface, "HIGH SCORE", 16, SOFT, (WIDTH - 60, 26), anchor="topright", shadow=False)
        ui.draw_text(surface, f"{hi}", 38, GOLD, (WIDTH - 60, 40), anchor="topright", glow=GOLD)
        ui.draw_text(surface, f"ROUND {g.round}", 34, WHITE, (WIDTH // 2, 42), glow=GOLD)
        for i in range(SEQUENCES_PER_ROUND):
            c = (WIDTH // 2 - 36 + i * 24, 74)
            if i < g.done_in_round:
                pygame.draw.circle(surface, GOLD, c, 7)
            else:
                pygame.draw.circle(surface, (90, 96, 140), c, 7, 2)

        for i in range(MAX_MISTAKES):
            alive = i < g.lives
            c = (52 + i * 40, 118)
            if alive:
                beat = 1 + 0.08 * self.keyboard.pulse
                ui.glow(surface, c, 26, (90, 20, 40), 2)
                ui.heart(surface, c, 30 * beat, (255, 80, 110))
            else:
                ui.heart(surface, c, 30, (55, 48, 82))
        label = DIFFICULTIES[self.difficulty]["label"]
        ui.draw_text(surface, f"{label}  ·  {g.bpm} BPM", 18, SOFT, (WIDTH - 50, 118), anchor="midright",
                     shadow=False)

    def draw_pause(self, surface):
        ui.fade(surface, 0.55)
        rect = pygame.Rect(0, 0, 520, 240)
        rect.center = (WIDTH // 2, HEIGHT // 2)
        ui.panel(surface, rect, radius=24, alpha=235)
        ui.draw_text(surface, "PAUSED", 56, WHITE, (WIDTH // 2, rect.y + 60), glow=ACCENT)
        ui.draw_text(surface, "Enter or Esc - keep playing", 22, SOFT, (WIDTH // 2, rect.y + 130))
        ui.draw_text(surface, "Q - quit to the title screen", 22, SOFT, (WIDTH // 2, rect.y + 170))


# Game over / name entry -----------------------------------------------------------------
class GameOverScene(Scene):
    def __init__(self, app, game):
        super().__init__(app)
        self.game = game
        self.summary = game.summary()
        self.difficulty = game.difficulty
        self.entering = storage.qualifies(app.scores, self.difficulty, game.score)
        self.text_input = self.entering
        self.name = app.settings.get("last_name", "")
        app.music.clear()

    def handle(self, event):
        if self.clicked_back(event):
            self.app.goto(TitleScene(self.app))
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.entering:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.save()
            elif event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
                self.app.audio.play("type", 0.4)
            elif event.key == pygame.K_ESCAPE:
                self.name = self.name or "PLAYER"
                self.save()
            elif event.unicode and len(self.name) < NAME_LENGTH and (
                    event.unicode.isalnum() or event.unicode in " -_."):
                self.name += event.unicode.upper()
                self.app.audio.play("type", 0.4)
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.app.audio.play("start", 0.8)
            self.app.goto(PlayScene(self.app, self.difficulty))
        elif event.key == pygame.K_ESCAPE:
            self.app.goto(TitleScene(self.app))

    def save(self):
        name = self.name.strip() or "PLAYER"
        place = storage.add_score(self.app.scores, self.difficulty, name, self.game.score, self.game.round)
        self.app.settings["last_name"] = name
        storage.save_settings(self.app.settings)
        self.app.audio.play("select", 0.7)
        self.app.goto(TopTenScene(self.app, self.difficulty, highlight=place))

    def draw(self, surface):
        g, s = self.game, self.summary
        ui.draw_text(surface, "GAME OVER", 72, WHITE, (WIDTH // 2, 80), glow=BAD)
        ui.draw_text(surface, f"{g.score}", 96, GOLD, (WIDTH // 2, 185), glow=GOLD)
        ui.draw_text(surface, "points", 22, SOFT, (WIDTH // 2, 245), shadow=False)

        rect = pygame.Rect(WIDTH // 2 - 420, 280, 840, 150)
        ui.panel(surface, rect)
        stats = [
            ("Round reached", f"{g.round}"),
            ("Sequences", f"{s['sequences']}"),
            ("Longest", f"{s['longest']} keys"),
            ("Accuracy", f"{s['accuracy']:.0f}%"),
        ]
        for i, (label, value) in enumerate(stats):
            x = rect.x + 105 + i * 210
            ui.draw_text(surface, value, 40, WHITE, (x, rect.y + 58), glow=ACCENT)
            ui.draw_text(surface, label, 18, SOFT, (x, rect.y + 108), shadow=False)
        if g.key_errors:
            worst = max(g.key_errors, key=g.key_errors.get)
            ui.draw_text(surface, f"Key to practise: {key_label(worst)}  ({FINGERS[worst]})", 22, GOLD,
                         (WIDTH // 2, 462), shadow=False)

        if self.entering:
            ui.draw_text(surface, "NEW TOP 10 SCORE!  Type your name:", 30, WHITE, (WIDTH // 2, 520), glow=GOOD)
            box = pygame.Rect(WIDTH // 2 - 220, 552, 440, 64)
            ui.panel(surface, box, edge=GOOD, radius=14)
            cursor = "_" if int(self.t * 2.5) % 2 == 0 else " "
            ui.draw_text(surface, self.name + cursor, 38, WHITE, box.center)
            ui.draw_text(surface, "Enter to save", 18, DIM, (WIDTH // 2, 640), shadow=False)
        else:
            ui.draw_text(surface, "Enter - play again", 28, WHITE, (WIDTH // 2, 548), glow=ACCENT)
            ui.draw_text(surface, "Esc - title screen", 22, SOFT, (WIDTH // 2, 596))
            self.draw_back(surface, "")


# Top 10 ---------------------------------------------------------------------------------
class TopTenScene(Scene):
    def __init__(self, app, difficulty=None, highlight=None):
        super().__init__(app)
        self.difficulty = difficulty or app.settings["difficulty"]
        self.highlight = highlight
        self.tab_rects = {}

    def handle(self, event):
        if self.clicked_back(event):
            self.app.goto(TitleScene(self.app))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for diff, rect in self.tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.switch(diff)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                order = DIFFICULTY_ORDER
                step = -1 if event.key == pygame.K_LEFT else 1
                self.switch(order[(order.index(self.difficulty) + step) % len(order)])
            elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE):
                self.app.audio.play("move", 0.5)
                self.app.goto(TitleScene(self.app))

    def switch(self, diff):
        if diff != self.difficulty:
            self.difficulty = diff
            self.highlight = None
            self.app.audio.play("move", 0.5)

    def draw(self, surface):
        self.heading(surface, "TOP 10", GOLD)
        self.tab_rects = draw_tabs(surface, self, [(d, DIFFICULTIES[d]["label"]) for d in DIFFICULTY_ORDER],
                                   self.difficulty, 122)
        rect = pygame.Rect(WIDTH // 2 - 430, 160, 860, 470)
        ui.panel(surface, rect)
        cols = [(rect.x + 60, "#", "center"), (rect.x + 120, "NAME", "midleft"), (rect.x + 520, "SCORE", "midright"),
                (rect.x + 640, "ROUND", "center"), (rect.right - 50, "DATE", "midright")]
        for x, text, anchor in cols:
            ui.draw_text(surface, text, 17, SOFT, (x, rect.y + 28), anchor=anchor, shadow=False)
        rows = self.app.scores.get(self.difficulty, [])
        if not rows:
            ui.draw_text(surface, "No scores yet - be the first!", 28, SOFT, rect.center)
        for i, row in enumerate(rows):
            y = rect.y + 68 + i * 40
            hl = i == self.highlight
            if hl:
                bar = pygame.Rect(rect.x + 16, y - 18, rect.w - 32, 36)
                k = 0.5 + 0.5 * math.sin(self.t * 5)
                ui.panel(surface, bar, color=(60, 60, 20), edge=ui.mix(GOLD, WHITE, k * 0.5), radius=10)
            medal = [GOLD, (210, 215, 235), (220, 150, 90)][i] if i < 3 else WHITE
            ui.draw_text(surface, f"{i + 1}", 24, medal, (cols[0][0], y))
            ui.draw_text(surface, row["name"], 24, WHITE, (cols[1][0], y), anchor="midleft")
            ui.draw_text(surface, f"{row['score']}", 24, GOLD if hl else WHITE, (cols[2][0], y), anchor="midright")
            ui.draw_text(surface, f"{row['round']}", 24, WHITE, (cols[3][0], y))
            ui.draw_text(surface, row.get("date", ""), 18, SOFT, (cols[4][0], y), anchor="midright", shadow=False)
        self.draw_back(surface, "Left / Right - difficulty    Esc - back")


def draw_tabs(surface, scene, tabs, current, y):
    rects = {}
    width = 230
    x = WIDTH // 2 - (len(tabs) * width + (len(tabs) - 1) * 12) // 2
    for key, label in tabs:
        rect = pygame.Rect(x, y - 20, width, 40)
        on = key == current
        ui.panel(surface, rect, color=(50, 60, 140) if on else (20, 24, 60), edge=ACCENT if on else (60, 70, 130),
                 radius=12)
        ui.draw_text(surface, label, 21, WHITE if on else SOFT, rect.center, shadow=False)
        rects[key] = rect
        x += width + 12
    return rects


# For Parents ---------------------------------------------------------------------------
def fmt_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


class ParentsScene(Scene):
    TABS = [("progress", "Progress"), ("mistakes", "What went wrong")]

    def __init__(self, app):
        super().__init__(app)
        self.tab = "progress"
        self.confirm_reset = False
        self.tab_rects = {}

    def handle(self, event):
        if self.clicked_back(event):
            self.app.goto(TitleScene(self.app))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.tab = key
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.confirm_reset:
            if event.key == pygame.K_y:
                self.app.stats = storage.reset_stats()
                self.app.audio.play("select", 0.6)
            self.confirm_reset = False
            return
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
            self.tab = "mistakes" if self.tab == "progress" else "progress"
            self.app.audio.play("move", 0.5)
        elif event.key in (pygame.K_DELETE, pygame.K_r):
            self.confirm_reset = True
        elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE):
            self.app.audio.play("move", 0.5)
            self.app.goto(TitleScene(self.app))

    def draw(self, surface):
        self.heading(surface, "FOR PARENTS", GOOD)
        self.tab_rects = draw_tabs(surface, self, self.TABS, self.tab, 122)
        st = self.app.stats
        if self.tab == "progress":
            self.draw_progress(surface, st)
        else:
            self.draw_mistakes(surface, st)
        self.draw_back(surface, "Left / Right - page    Del - reset statistics    Esc - back")
        if self.confirm_reset:
            ui.fade(surface, 0.6)
            rect = pygame.Rect(0, 0, 620, 200)
            rect.center = (WIDTH // 2, HEIGHT // 2)
            ui.panel(surface, rect, edge=BAD, alpha=240)
            ui.draw_text(surface, "Erase all statistics?", 36, WHITE, (WIDTH // 2, rect.y + 60), glow=BAD)
            ui.draw_text(surface, "Y - yes, erase      any other key - cancel", 22, SOFT, (WIDTH // 2, rect.y + 130))
            ui.draw_text(surface, "(The Top 10 tables are kept.)", 17, DIM, (WIDTH // 2, rect.y + 166), shadow=False)

    def tile(self, surface, rect, label, value, color=WHITE):
        ui.panel(surface, rect, radius=14)
        ui.draw_text(surface, value, 32, color, (rect.centerx, rect.y + 34), glow=ui.scale_color(color, 0.5))
        ui.draw_text(surface, label, 16, SOFT, (rect.centerx, rect.bottom - 18), shadow=False)

    def draw_progress(self, surface, st):
        total_keys = st["keys_correct"] + st["keys_wrong"] + st["timeouts"]
        accuracy = f"{100 * st['keys_correct'] / total_keys:.0f}%" if total_keys else "-"
        best_round = max((b.get("round", 0) for b in st["best"].values()), default=0)
        today = st["daily"].get(storage.today(), 0)
        tiles = [
            ("Total time played", fmt_duration(st["total_seconds"]), ACCENT),
            ("Played today", fmt_duration(today), ACCENT),
            ("Games played", f"{st['games']}", WHITE),
            ("Key accuracy", accuracy, GOOD),
            ("Best round reached", f"{best_round}", GOLD),
            ("Typing errors", f"{st['keys_wrong']}", BAD),
            ("Too slow (time-outs)", f"{st['timeouts']}", BAD),
            ("Sequence failures", f"{st['failures']}", BAD),
            ("Sequences completed", f"{st['sequences']}", GOOD),
            ("Game overs", f"{st['game_overs']}", WHITE),
        ]
        for i, (label, value, color) in enumerate(tiles):
            r = pygame.Rect(40 + (i % 5) * 242, 158 + (i // 5) * 96, 230, 86)
            self.tile(surface, r, label, value, color)

        # Minutes per day, last 7 days
        left = pygame.Rect(40, 362, 590, 262)
        ui.panel(surface, left)
        ui.draw_text(surface, "Minutes played - last 7 days", 19, WHITE, (left.x + 20, left.y + 22),
                     anchor="midleft", shadow=False)
        days = [datetime.date.today() - datetime.timedelta(days=6 - i) for i in range(7)]
        minutes = [st["daily"].get(d.isoformat(), 0) / 60 for d in days]
        top = max(5.0, max(minutes))
        bw = 56
        for i, (d, m) in enumerate(zip(days, minutes)):
            x = left.x + 40 + i * 76
            h = int(150 * m / top)
            base = left.bottom - 44
            if h:
                pygame.draw.rect(surface, ACCENT, (x, base - h, bw, h), border_radius=6)
            else:
                pygame.draw.line(surface, (60, 70, 120), (x, base), (x + bw, base), 2)
            ui.draw_text(surface, f"{m:.0f}" if m >= 1 or m == 0 else "<1", 16, WHITE, (x + bw // 2, base - h - 14),
                         shadow=False)
            ui.draw_text(surface, d.strftime("%a"), 16, SOFT, (x + bw // 2, base + 18), shadow=False)

        # Score per game, last 15
        right = pygame.Rect(650, 362, 590, 262)
        ui.panel(surface, right)
        ui.draw_text(surface, "Score - last 15 games", 19, WHITE, (right.x + 20, right.y + 22),
                     anchor="midleft", shadow=False)
        colors = {"easy": GOOD, "medium": ACCENT, "hard": (255, 140, 200)}
        lx = right.right - 20
        for diff in reversed(DIFFICULTY_ORDER):
            r = ui.draw_text(surface, DIFFICULTIES[diff]["label"], 15, colors[diff], (lx, right.y + 22),
                             anchor="midright", shadow=False)
            lx = r.x - 16
        games = st["history"][-15:]
        if not games:
            ui.draw_text(surface, "Play a game to see progress here", 20, SOFT, right.center, shadow=False)
        top = max([100] + [g["score"] for g in games])
        for i, g in enumerate(games):
            x = right.x + 30 + i * 36
            h = int(150 * g["score"] / top)
            base = right.bottom - 44
            pygame.draw.rect(surface, colors.get(g["difficulty"], WHITE), (x, base - max(2, h), 26, max(2, h)),
                             border_radius=5)
            ui.draw_text(surface, f"R{g['round']}", 13, SOFT, (x + 13, base + 16), shadow=False)

        line = "   ".join(f"{DIFFICULTIES[d]['label']}: best {st['best'][d]['score']} (round {st['best'][d]['round']})"
                          for d in DIFFICULTY_ORDER)
        ui.draw_text(surface, line, 18, GOLD, (WIDTH // 2, 642), shadow=False)
        if st.get("first_played"):
            ui.draw_text(surface, f"Playing since {st['first_played']}", 15, DIM, (WIDTH - 40, HEIGHT - 38),
                         anchor="midright", shadow=False)

    def draw_mistakes(self, surface, st):
        top = pygame.Rect(40, 152, 1200, 190)
        ui.panel(surface, top)
        ui.draw_text(surface, "Keys missed most (all games)", 19, WHITE, (top.x + 20, top.y + 22), anchor="midleft",
                     shadow=False)
        errors = st["key_errors"]
        worst = max(errors.values(), default=0)
        size, gap = 80, 16
        x0 = WIDTH // 2 - (10 * size + 9 * gap) // 2
        for i, key in enumerate(HOME_ROW):
            n = errors.get(key, 0)
            heat = n / worst if worst else 0
            rect = pygame.Rect(x0 + i * (size + gap), top.y + 50, size, size)
            col = ui.mix((40, 46, 96), (255, 80, 100), heat) if n else (40, 46, 96)
            if heat > 0.5:
                ui.glow(surface, rect.center, 70, ui.scale_color((255, 60, 80), heat * 0.5), 2)
            pygame.draw.rect(surface, col, rect, border_radius=14)
            pygame.draw.rect(surface, ui.mix(col, WHITE, 0.3), rect, 2, border_radius=14)
            ui.draw_text(surface, key_label(key), 34, WHITE, rect.center)
            ui.draw_text(surface, f"{n}", 17, BAD if n else DIM, (rect.centerx, rect.bottom + 16), shadow=False)

        left = pygame.Rect(40, 356, 520, 266)
        ui.panel(surface, left)
        ui.draw_text(surface, "Most common mix-ups", 19, WHITE, (left.x + 20, left.y + 22), anchor="midleft",
                     shadow=False)
        pairs = sorted(st["confusions"].items(), key=lambda kv: -kv[1])[:6]
        if not pairs:
            ui.draw_text(surface, "No mix-ups yet", 20, SOFT, left.center, shadow=False)
        for i, (pair, count) in enumerate(pairs):
            want, got = pair.split(">", 1)
            if want not in FINGERS or got not in FINGERS:
                continue
            y = left.y + 62 + i * 33
            ui.draw_text(surface, f"Wanted {key_label(want)}   pressed {key_label(got)}", 19, WHITE,
                         (left.x + 24, y), anchor="midleft", shadow=False)
            ui.draw_text(surface, f"{FINGERS[want]} / {FINGERS[got]}", 15, DIM, (left.x + 290, y),
                         anchor="midleft", shadow=False)
            ui.draw_text(surface, f"x{count}", 19, BAD, (left.right - 24, y), anchor="midright", shadow=False)

        right = pygame.Rect(576, 356, 664, 266)
        ui.panel(surface, right)
        ui.draw_text(surface, "Recent games", 19, WHITE, (right.x + 20, right.y + 22), anchor="midleft", shadow=False)
        cols = [("When", 20, "midleft"), ("Level", 178, "midleft"), ("Score", 312, "midright"),
                ("Round", 370, "center"), ("Wrong", 438, "center"), ("Slow", 504, "center"),
                ("Accuracy", 630, "midright")]
        for label, dx, anchor in cols:
            ui.draw_text(surface, label, 15, SOFT, (right.x + dx, right.y + 52), anchor=anchor, shadow=False)
        games = list(reversed(st["history"][-6:]))
        if not games:
            ui.draw_text(surface, "No games yet", 20, SOFT, (right.centerx, right.centery + 20), shadow=False)
        for i, g in enumerate(games):
            y = right.y + 84 + i * 30
            values = [g.get("date", "")[5:], DIFFICULTIES.get(g["difficulty"], {}).get("label", "?"),
                      f"{g['score']}", f"{g['round']}", f"{g['keys_wrong']}", f"{g['timeouts']}",
                      f"{g['accuracy']:.0f}%"]
            for (label, dx, anchor), value in zip(cols, values):
                col = BAD if label in ("Wrong", "Slow") and value != "0" else WHITE
                ui.draw_text(surface, value, 17, col, (right.x + dx, y), anchor=anchor, shadow=False)

        if worst:
            key = max(errors, key=errors.get)
            tip = (f"Tip: {key_label(key)} is missed most. It belongs to the {FINGERS[key].replace('L ', 'left ').replace('R ', 'right ')}"
                   " finger - a few slow games on Easy help build the habit.")
        else:
            tip = "Tip: short, regular sessions build memory and touch-typing best."
        ui.draw_text(surface, tip, 17, GOLD, (WIDTH // 2, 642), shadow=False)


# Credits -------------------------------------------------------------------------------
class CreditsScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.links = {}

    def handle(self, event):
        if self.clicked_back(event):
            self.app.goto(TitleScene(self.app))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for url, rect in self.links.items():
                if rect.collidepoint(event.pos):
                    try:
                        webbrowser.open(url)
                    except Exception:  # noqa: BLE001 - a browser problem must never stop the game
                        pass
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN,
                                                            pygame.K_KP_ENTER, pygame.K_BACKSPACE):
            self.app.audio.play("move", 0.5)
            self.app.goto(TitleScene(self.app))

    def draw(self, surface):
        self.heading(surface, "CREDITS", (190, 110, 255))
        date = datetime.date.fromisoformat(RELEASE_DATE)
        rect = pygame.Rect(WIDTH // 2 - 440, 112, 880, 522)
        ui.panel(surface, rect)
        cx = WIDTH // 2
        ui.draw_text(surface, f"KEY RUSH  v{__version__}", 36, WHITE, (cx, 152), glow=ACCENT)
        ui.draw_text(surface, f"Released {date.strftime('%B')} {date.day}, {date.year}", 20, SOFT, (cx, 190), shadow=False)

        ui.draw_text(surface, "Created by", 18, DIM, (cx, 232), shadow=False)
        ui.draw_text(surface, CREATOR, 34, GOLD, (cx, 264), glow=GOLD)
        ui.draw_text(surface, "Made with", 18, DIM, (cx, 306), shadow=False)
        ui.draw_text(surface, "Claude Code", 28, WHITE, (cx, 334), glow=(255, 150, 90))

        self.links = {}
        for y, label, text, url in ((384, "Website", WEBSITE, WEBSITE), (420, "Email", EMAIL, f"mailto:{EMAIL}")):
            ui.draw_text(surface, label, 18, DIM, (cx - 20, y), anchor="midright", shadow=False)
            r = ui.draw_text(surface, text, 22, ACCENT, (cx, y), anchor="midleft", shadow=False)
            hover = r.collidepoint(self.app.mouse)
            pygame.draw.line(surface, ACCENT if hover else (60, 100, 140), (r.x, r.bottom), (r.right, r.bottom), 2)
            self.links[url] = r

        ui.draw_text(surface, f"Licensed under the {LICENSE_NAME}", 20, WHITE, (cx, 470), shadow=False)
        notice = ["This program is free software: you can redistribute it and/or modify it under the",
                  "terms of the GNU GPL as published by the Free Software Foundation, version 3 or later.",
                  "It comes with ABSOLUTELY NO WARRANTY. See the LICENSE file for details."]
        for i, line in enumerate(notice):
            ui.draw_text(surface, line, 15, SOFT, (cx, 502 + i * 22), shadow=False)
        ui.draw_text(surface, "Font: M PLUS 1p (SIL Open Font License)   ·   All music and sound made in code",
                     15, DIM, (cx, 584), shadow=False)
        ui.draw_text(surface, f"Recommended for ages {RECOMMENDED_AGE}", 18, GOOD, (cx, 612), shadow=False)
        self.draw_back(surface, "Click a link to open it    Esc - back")
