"""Drawing helpers: fonts, glowing text, soft glows, panels and the background.

Glows are drawn additively (BLEND_RGB_ADD) from surfaces rendered on black,
which gives a bright neon look cheaply. Anything expensive is cached.
"""
import math
import os
import random
import sys

import pygame

from .config import BG_BOTTOM, BG_TOP, HEIGHT, PANEL, PANEL_EDGE, WIDTH


def resource(*parts):
    base = getattr(sys, "_MEIPASS", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    return os.path.join(base, *parts)


FONT_PATH = resource("assets", "fonts", "MPLUS1p-Bold.ttf")
_fonts = {}
_text_cache = {}
_glow_cache = {}


def font(size):
    if size not in _fonts:
        try:
            _fonts[size] = pygame.font.Font(FONT_PATH, size)
        except (OSError, FileNotFoundError):
            _fonts[size] = pygame.font.Font(None, int(size * 1.3))
    return _fonts[size]


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scale_color(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def blur(surface, amount=4):
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // amount), max(1, h // amount)))
    return pygame.transform.smoothscale(small, (w, h))


def render(text, size, color):
    key = (text, size, color)
    surf = _text_cache.get(key)
    if surf is None:
        surf = font(size).render(text, True, color)
        if len(_text_cache) > 600:
            _text_cache.clear()
        _text_cache[key] = surf
    return surf


def glow_text_surface(text, size, color, spread=None):
    """The glow behind a piece of text, rendered on black for additive blending."""
    key = ("glowtext", text, size, color)
    surf = _glow_cache.get(key)
    if surf is None:
        spread = spread or max(6, size // 3)
        label = font(size).render(text, True, color, (0, 0, 0))
        w, h = label.get_size()
        surf = pygame.Surface((w + spread * 4, h + spread * 4))
        surf.fill((0, 0, 0))
        surf.blit(label, (spread * 2, spread * 2))
        surf = blur(blur(surf, max(2, spread // 2)), 2)
        if len(_glow_cache) > 400:
            _glow_cache.clear()
        _glow_cache[key] = surf
    return surf


def draw_text(surface, text, size, color, pos, anchor="center", glow=None, glow_strength=1,
              shadow=True, alpha=255):
    label = render(text, size, color)
    rect = label.get_rect(**{anchor: pos})
    if glow:
        g = glow_text_surface(text, size, glow)
        grect = g.get_rect(center=rect.center)
        for _ in range(glow_strength):
            surface.blit(g, grect, special_flags=pygame.BLEND_RGB_ADD)
    if shadow:
        sh = render(text, size, (0, 0, 10))
        if alpha < 255:
            sh = sh.copy()
            sh.set_alpha(alpha // 2)
        surface.blit(sh, rect.move(0, max(2, size // 18)))
    if alpha < 255:
        label = label.copy()
        label.set_alpha(alpha)
    surface.blit(label, rect)
    return rect


def radial(radius, color, falloff=2.0):
    """A soft round glow on black, for additive blending."""
    key = ("radial", radius, color, falloff)
    surf = _glow_cache.get(key)
    if surf is None:
        size = radius * 2
        small = 64
        base = pygame.Surface((small, small))
        base.fill((0, 0, 0))
        for r in range(small // 2, 0, -1):
            t = 1 - r / (small / 2)
            k = t ** falloff
            pygame.draw.circle(base, scale_color(color, k), (small // 2, small // 2), r)
        surf = pygame.transform.smoothscale(base, (size, size))
        _glow_cache[key] = surf
    return surf


def glow(surface, center, radius, color, falloff=2.0):
    g = radial(int(radius), color, falloff)
    surface.blit(g, g.get_rect(center=(int(center[0]), int(center[1]))),
                 special_flags=pygame.BLEND_RGB_ADD)


def panel(surface, rect, color=PANEL, edge=PANEL_EDGE, radius=18, alpha=210, width=2):
    rect = pygame.Rect(rect)
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (*color, alpha), surf.get_rect(), border_radius=radius)
    pygame.draw.line(surf, (255, 255, 255, 40), (radius, 2), (rect.w - radius, 2), 1)
    if width:
        pygame.draw.rect(surf, (*edge, 200), surf.get_rect(), width, border_radius=radius)
    surface.blit(surf, rect)


def heart(surface, center, size, color, outline=None):
    x, y = center
    r = size * 0.28
    pts = [(x, y + size * 0.42), (x - size * 0.5, y - size * 0.02), (x + size * 0.5, y - size * 0.02)]
    pygame.draw.circle(surface, color, (int(x - r * 0.95), int(y - r * 0.55)), int(r + 1))
    pygame.draw.circle(surface, color, (int(x + r * 0.95), int(y - r * 0.55)), int(r + 1))
    pygame.draw.polygon(surface, color, pts)


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    t = max(0.0, min(1.0, t))
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class Background:
    """A deep gradient with slowly drifting soft lights and twinkling stars.
    `pulse()` brightens it a touch on each beat."""

    COLORS = [(60, 40, 160), (20, 110, 170), (120, 50, 150), (30, 140, 140), (70, 70, 190)]

    def __init__(self, seed=7):
        rng = random.Random(seed)
        grad = pygame.Surface((1, 256))
        for y in range(256):
            grad.set_at((0, y), mix(BG_TOP, BG_BOTTOM, y / 255))
        self.base = pygame.transform.smoothscale(grad, (WIDTH, HEIGHT)).convert()
        self.orbs = []
        for i in range(9):
            self.orbs.append({
                "x": rng.uniform(0, WIDTH), "y": rng.uniform(0, HEIGHT),
                "r": rng.randint(160, 320), "c": self.COLORS[i % len(self.COLORS)],
                "sx": rng.uniform(-14, 14), "sy": rng.uniform(-8, 8),
                "ph": rng.uniform(0, 6.28), "k": rng.uniform(0.25, 0.45),
            })
        self.stars = [(rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT), rng.uniform(0, 6.28),
                       rng.uniform(0.6, 2.0)) for _ in range(110)]
        self.time = 0.0
        self.beat = 0.0
        self.tint = None
        self.tint_t = 0.0

    def pulse(self, amount=1.0):
        self.beat = max(self.beat, amount)

    def flash(self, color):
        self.tint = color
        self.tint_t = 1.0

    def update(self, dt):
        self.time += dt
        self.beat = max(0.0, self.beat - dt * 3.0)
        self.tint_t = max(0.0, self.tint_t - dt * 2.2)
        for o in self.orbs:
            o["x"] = (o["x"] + o["sx"] * dt) % (WIDTH + 600)
            o["y"] = (o["y"] + o["sy"] * dt) % (HEIGHT + 600)

    def draw(self, surface):
        surface.blit(self.base, (0, 0))
        for o in self.orbs:
            k = o["k"] * (0.75 + 0.25 * math.sin(self.time * 0.4 + o["ph"])) * (1 + 0.35 * self.beat)
            color = scale_color(o["c"], k)
            glow(surface, (o["x"] - 300, o["y"] - 300), o["r"], color, 1.6)
        t = self.time
        for x, y, ph, sp in self.stars:
            b = 0.5 + 0.5 * math.sin(t * sp + ph)
            c = int(70 + 150 * b)
            surface.fill((c, c, min(255, c + 30)), (int(x), int(y), 2, 2))
        if self.tint_t > 0 and self.tint:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill(scale_color(self.tint, 0.35 * self.tint_t))
            surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


class Particles:
    def __init__(self):
        self.items = []
        self.rng = random.Random()

    def burst(self, x, y, color, count=24, speed=260, life=0.9, size=5):
        r = self.rng
        for _ in range(count):
            a = r.uniform(0, math.tau)
            s = r.uniform(0.3, 1.0) * speed
            self.items.append([x, y, math.cos(a) * s, math.sin(a) * s - 60, life * r.uniform(0.6, 1.0),
                               life, color, r.uniform(0.6, 1.0) * size])

    def update(self, dt):
        alive = []
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.96
            p[3] = p[3] * 0.96 + 220 * dt
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
        self.items = alive

    def draw(self, surface):
        for x, y, _, _, life, total, color, size in self.items:
            k = life / total
            glow(surface, (x, y), max(4, int(size * 3)), scale_color(color, k * 0.9), 2.2)
            pygame.draw.circle(surface, mix((255, 255, 255), color, 0.4), (int(x), int(y)),
                               max(1, int(size * k)))


class Popups:
    """Floating "+100" style text."""

    def __init__(self):
        self.items = []

    def add(self, text, pos, color, size=34):
        self.items.append([text, pos[0], pos[1], color, size, 1.2])

    def update(self, dt):
        for p in self.items:
            p[2] -= 50 * dt
            p[5] -= dt
        self.items = [p for p in self.items if p[5] > 0]

    def draw(self, surface):
        for text, x, y, color, size, life in self.items:
            draw_text(surface, text, size, color, (x, y), glow=color, alpha=int(255 * min(1, life * 2)))


def fade(surface, amount):
    if amount <= 0:
        return
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((4, 4, 16))
    overlay.set_alpha(int(255 * min(1.0, amount)))
    surface.blit(overlay, (0, 0))
