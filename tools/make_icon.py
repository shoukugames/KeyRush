#!/usr/bin/env python3
"""Draws the app icon, a glowing K keycap: assets/icon.png and assets/icon.ico.

Run this only when the design changes. Needs Pillow for the .ico file.
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from keyrush import ui  # noqa: E402

pygame.init()
pygame.display.set_mode((16, 16))
SIZE = 512
BIG = SIZE * 2

canvas = pygame.Surface((BIG, BIG), pygame.SRCALPHA)
back = pygame.Surface((1, 128))
for y in range(128):
    back.set_at((0, y), ui.mix((34, 24, 110), (8, 46, 80), y / 127))
back = pygame.transform.smoothscale(back, (BIG, BIG)).convert_alpha()
glow = ui.radial(520, (90, 60, 200), 1.6)
back.blit(glow, (BIG // 2 - 520, BIG // 2 - 560), special_flags=pygame.BLEND_RGB_ADD)
mask = pygame.Surface((BIG, BIG), pygame.SRCALPHA)
pygame.draw.rect(mask, (255, 255, 255, 255), (16, 16, BIG - 32, BIG - 32), border_radius=200)
back.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
canvas.blit(back, (0, 0))

color = (255, 170, 70)
cap = pygame.Rect(0, 0, 640, 640)
cap.center = (BIG // 2, BIG // 2 - 30)
halo = ui.radial(560, (180, 100, 30), 1.8)
layer = pygame.Surface((BIG, BIG))
layer.blit(halo, halo.get_rect(center=cap.center))
canvas.blit(layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
pygame.draw.rect(canvas, ui.mix((20, 14, 40), color, 0.5), cap.move(0, 60), border_radius=120)
pygame.draw.rect(canvas, color, cap, border_radius=120)
pygame.draw.rect(canvas, ui.mix(color, (255, 255, 255), 0.25), cap.inflate(-90, -90), border_radius=90)
pygame.draw.rect(canvas, (255, 235, 200), cap, 14, border_radius=120)
font = pygame.font.Font(ui.FONT_PATH, 470)
letter = font.render("K", True, (40, 24, 60))
canvas.blit(letter, letter.get_rect(center=(cap.centerx, cap.centery - 20)))
pygame.draw.rect(canvas, (40, 24, 60), (cap.centerx - 70, cap.bottom - 110, 140, 26), border_radius=13)

icon = pygame.transform.smoothscale(canvas, (SIZE, SIZE))
png = os.path.join(ROOT, "assets", "icon.png")
pygame.image.save(icon, png)
Image.open(png).save(os.path.join(ROOT, "assets", "icon.ico"),
                     sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote assets/icon.png and assets/icon.ico")
