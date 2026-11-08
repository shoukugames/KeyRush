#!/usr/bin/env python3
"""Saves a PNG of every screen into the folder given (default: build/screenshots).

Uses a throwaway data folder filled with sample games, so your own scores and
statistics are never touched.
"""
import os
import random
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["KEYRUSH_DATA"] = tempfile.mkdtemp(prefix="keyrush-shots-")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from keyrush import i18n, storage  # noqa: E402
from keyrush.app import App  # noqa: E402
from keyrush.logic import Game  # noqa: E402
from keyrush.scenes import (CreditsScene, GameOverScene, ParentsScene, PlayScene,  # noqa: E402
                            TitleScene, TopTenScene)

# Usage: screenshots.py [folder] [en|ja]
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "screenshots")
LANG = sys.argv[2] if len(sys.argv) > 2 else "en"
os.makedirs(out, exist_ok=True)

# Sample history: a few simulated games on each difficulty
rng = random.Random(3)
stats = storage.load_stats()
scores = storage.load_scores()
names = ["MAYA", "LEO", "SAM", "AVA", "NOAH", "ZOE", "ELI", "MIA", "KAI", "LILY", "OWEN"]
for i in range(16):
    diff = ["easy", "medium", "hard"][i % 3]
    g = Game(diff, rng=random.Random(i))
    while not g.over:
        g.update(1 / 30)
        if g.expected_key and rng.random() < 0.12:
            key = g.expected_key if rng.random() < 0.94 - i * 0.005 else rng.choice(g.keys)
            g.press(key)
        g.take_events()
    storage.record_game(stats, g.summary())
    storage.add_score(scores, diff, names[i % len(names)], g.score, g.round)

app = App(seed=4)
i18n.set_language(LANG)
app.audio.wait_ready()
app.stats, app.scores = storage.load_stats(), storage.load_scores()


def run(seconds):
    for _ in range(int(seconds * 60)):
        app.step(1 / 60)


def shot(name):
    app.fade = 0
    app.draw()
    pygame.image.save(app.screen, os.path.join(out, f"{name}.png"))
    print("saved", name)


app.goto(TitleScene(app))
run(2.3)
shot("01_title")

app.settings["difficulty"] = "medium"
play = PlayScene(app, "medium")
app.goto(play)
g = play.game
while g.state != "show" or g.show_pos < 2:
    run(1 / 60)
run(0.05)
shot("02_play_watch")
while g.state != "input":
    run(1 / 60)
for _ in range(2):
    play.press(g.expected_key)
    run(0.12)
shot("03_play_your_turn")
play.press(next(k for k in g.keys if k != g.expected_key))
run(0.15)
shot("04_play_mistake")

app.goto(GameOverScene(app, g))
app.scene.entering = True
app.scene.name = "MAYA"
run(0.5)
shot("05_game_over_name")

app.goto(TopTenScene(app, "easy", highlight=1))
run(0.5)
shot("06_top10")
app.goto(ParentsScene(app))
run(0.5)
shot("07_parents_progress")
app.scene.tab = "mistakes"
shot("08_parents_mistakes")
app.goto(CreditsScene(app))
run(0.5)
shot("09_credits")
