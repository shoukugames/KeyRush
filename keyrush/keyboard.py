"""The on-screen home row: chunky 3D keycaps that light, press, ripple and shake."""
import math

import pygame

from . import ui
from .config import FINGER_COLORS, FINGERS, HOME_ROW, SOFT, WIDTH, key_label

KEY_SIZE = 98
KEY_GAP = 12
DEPTH = 10


class KeyboardView:
    def __init__(self, active_keys=HOME_ROW, top=410, size=KEY_SIZE, gap=KEY_GAP, show_fingers=True):
        self.size = size
        self.gap = gap
        self.top = top
        self.show_fingers = show_fingers
        self.active = set(active_keys)
        total = len(HOME_ROW) * size + (len(HOME_ROW) - 1) * gap
        x0 = (WIDTH - total) // 2
        self.rects = {}
        for i, key in enumerate(HOME_ROW):
            # A small gap between the hands, like a real keyboard's G|H divide
            self.rects[key] = pygame.Rect(x0 + i * (size + gap), top, size, size)
        self.light = {k: 0.0 for k in HOME_ROW}
        self.light_hold = {k: 0.0 for k in HOME_ROW}
        self.press = {k: 0.0 for k in HOME_ROW}
        self.wrong = {k: 0.0 for k in HOME_ROW}
        self.hint = {k: 0.0 for k in HOME_ROW}
        self.ripples = []
        self.pulse = 0.0
        self.time = 0.0

    def center(self, key):
        return self.rects[key].center

    def flash(self, key, duration):
        self.light[key] = 1.0
        self.light_hold[key] = duration
        self.ripples.append([key, 0.0, FINGER_COLORS[key]])

    def tap(self, key, good=True):
        self.press[key] = 1.0
        self.light[key] = max(self.light[key], 0.9)
        self.light_hold[key] = 0.08
        if good:
            self.ripples.append([key, 0.0, FINGER_COLORS[key]])
        else:
            self.wrong[key] = 1.0

    def show_hint(self, key, seconds=1.2):
        self.hint[key] = seconds

    def beat(self):
        self.pulse = 1.0

    def update(self, dt):
        self.time += dt
        self.pulse = max(0.0, self.pulse - dt * 3)
        for k in HOME_ROW:
            if self.light_hold[k] > 0:
                self.light_hold[k] -= dt
            else:
                self.light[k] = max(0.0, self.light[k] - dt * 4.5)
            self.press[k] = max(0.0, self.press[k] - dt * 6)
            self.wrong[k] = max(0.0, self.wrong[k] - dt * 2.2)
            self.hint[k] = max(0.0, self.hint[k] - dt)
        for r in self.ripples:
            r[1] += dt
        self.ripples = [r for r in self.ripples if r[1] < 0.6]

    def draw(self, surface):
        s = self.size
        for key in HOME_ROW:
            rect = self.rects[key]
            active = key in self.active
            color = FINGER_COLORS[key] if active else (90, 95, 120)
            light = self.light[key]
            hint = self.hint[key] > 0 and (int(self.hint[key] * 6) % 2 == 0)
            if hint:
                light = max(light, 0.7)
            press = self.press[key]
            shake = math.sin(self.time * 60) * 7 * self.wrong[key]
            dy = int(press * (DEPTH - 2) + light * 3)
            x = rect.x + int(shake)

            if light > 0.02:
                ui.glow(surface, (x + s // 2, rect.y + s // 2 + dy), int(s * (0.95 + 0.45 * light)),
                        ui.scale_color(color, 0.85 * light), 1.8)

            # Shadow, then the side of the cap, then the top face
            shadow = pygame.Surface((s + 12, s + 12), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 110), shadow.get_rect(), border_radius=22)
            surface.blit(shadow, (x - 6, rect.y + DEPTH + 4))
            side = ui.mix((18, 18, 40), color, 0.45 if active else 0.25)
            pygame.draw.rect(surface, side, (x, rect.y + DEPTH, s, s), border_radius=18)

            base_mix = 0.22 + 0.06 * self.pulse if active else 0.12
            face_col = ui.mix((28, 30, 66), color, base_mix + (1 - base_mix) * light)
            if self.wrong[key] > 0:
                face_col = ui.mix(face_col, (255, 70, 90), self.wrong[key])
            face = pygame.Rect(x, rect.y + dy, s, s)
            pygame.draw.rect(surface, face_col, face, border_radius=18)
            inner = face.inflate(-14, -14)
            pygame.draw.rect(surface, ui.mix(face_col, (255, 255, 255), 0.10), inner, border_radius=14)
            hi = pygame.Rect(inner.x + 4, inner.y + 3, inner.w - 8, inner.h // 3)
            hl = pygame.Surface(hi.size, pygame.SRCALPHA)
            pygame.draw.rect(hl, (255, 255, 255, 34 + int(40 * light)), hl.get_rect(), border_radius=10)
            surface.blit(hl, hi)
            edge = ui.mix(color, (255, 255, 255), 0.4 * light) if active else (70, 75, 100)
            pygame.draw.rect(surface, edge, face, 3, border_radius=18)

            text_col = ui.mix((235, 238, 255), (20, 16, 40), light * 0.85) if active else (130, 135, 160)
            ui.draw_text(surface, key_label(key), int(s * 0.46), text_col,
                         (face.centerx, face.centery - 4), shadow=light < 0.5)
            if key in ("f", "j") and s >= 70:   # the little bumps you can feel
                pygame.draw.rect(surface, text_col, (face.centerx - 12, face.bottom - 22, 24, 5),
                                 border_radius=3)

            if self.show_fingers:
                ui.draw_text(surface, FINGERS[key], 15, SOFT if active else (90, 96, 130),
                             (rect.centerx, rect.bottom + DEPTH + 22), shadow=False)

        for key, t, color in self.ripples:
            rect = self.rects[key]
            k = t / 0.6
            radius = int(self.size * (0.55 + 0.6 * k))
            ring = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*color, int(200 * (1 - k))), (radius + 4, radius + 4), radius,
                               max(1, int(6 * (1 - k))))
            surface.blit(ring, ring.get_rect(center=rect.center))
