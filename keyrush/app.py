"""Window, main loop and command line."""
import argparse
import os
import sys
import traceback

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from . import __version__, i18n, storage, ui  # noqa: E402
from .audio import Audio, Music  # noqa: E402
from .config import DIFFICULTIES, FPS, HEIGHT, TITLE, WIDTH  # noqa: E402
from .scenes import BeatClock, TitleScene  # noqa: E402

MENU_BPM = 66


class App:
    def __init__(self, autoplay=False, seed=None):
        pygame.init()
        pygame.display.set_caption(f"{TITLE} v{__version__}")
        try:
            pygame.display.set_icon(pygame.image.load(ui.resource("assets", "icon.png")))
        except (pygame.error, FileNotFoundError):
            pass
        self.settings = storage.load_settings()
        if self.settings.get("language") not in (i18n.ENGLISH, i18n.JAPANESE):
            self.settings["language"] = i18n.detect_language()
        i18n.set_language(self.settings["language"])
        flags = pygame.SCALED | pygame.RESIZABLE
        if self.settings.get("fullscreen"):
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.scores = storage.load_scores()
        self.stats = storage.load_stats()
        self.audio = Audio(music=self.settings["music"], sound=self.settings["sound"])
        self.music = Music(self.audio)
        self.menu_clock = BeatClock(MENU_BPM)
        self.bg = ui.Background()
        self.autoplay = autoplay
        self.autoplay_error_rate = 0.04
        self.seed = seed
        self.mouse = (0, 0)
        self.running = True
        self.fade = 1.0
        self.scene = TitleScene(self)
        self.was_menu = False

    def difficulty_keys(self):
        return DIFFICULTIES[self.settings["difficulty"]]["keys"]

    def goto(self, scene):
        self.scene = scene
        self.fade = 0.8

    def toggle_music(self):
        self.settings["music"] = not self.settings["music"]
        self.audio.set_music(self.settings["music"])
        if self.settings["music"]:
            self.music.start()
        storage.save_settings(self.settings)

    def toggle_language(self):
        self.settings["language"] = i18n.toggle_language()
        storage.save_settings(self.settings)
        self.audio.play("select", 0.5)

    def toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()
        self.settings["fullscreen"] = not self.settings.get("fullscreen")
        storage.save_settings(self.settings)

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            self.mouse = event.pos
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
                return
            if event.key == pygame.K_m and not self.scene.text_input:
                self.toggle_music()
                return
        self.scene.handle(event)

    def step(self, dt):
        self.audio.poll()
        menu = self.scene.menu_music
        if menu and not self.was_menu:
            self.music.start()
            self.music.intensity = 0
            self.music.sparkles = True
        self.was_menu = menu
        if menu:
            for index in self.menu_clock.update(dt):
                self.music.on_beat(index, self.menu_clock.beat_len)
                self.scene.on_menu_beat(index)
                self.bg.pulse(0.35)
            self.music.update(dt)
        self.bg.update(dt)
        self.scene.update(dt)
        self.fade = max(0.0, self.fade - dt * 3.5)

    def draw(self):
        self.bg.draw(self.screen)
        self.scene.draw(self.screen)
        ui.fade(self.screen, self.fade)

    def shutdown(self):
        from .scenes import PlayScene
        if isinstance(self.scene, PlayScene):
            self.scene.record(self.scene.game.over)

    def run(self):
        while self.running:
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            for event in pygame.event.get():
                self.handle(event)
            self.step(dt)
            self.draw()
            pygame.display.flip()
        self.shutdown()
        pygame.quit()


def smoke_test(path):
    """Plays every screen and a full automatic game without a person. Used by the
    build scripts to prove a packaged copy really runs."""
    from .scenes import (CreditsScene, GameOverScene, ParentsScene, PlayScene, TitleScene, TopTenScene)
    app = App(autoplay=True, seed=1)
    app.audio.wait_ready()
    dt = 1 / 60
    frames = 0

    def run(seconds, until=None):
        nonlocal frames
        for _ in range(int(seconds / dt)):
            app.step(dt)
            app.draw()
            pygame.display.flip()
            frames += 1
            if until and until():
                return

    run(1.0)
    for language in (i18n.JAPANESE, i18n.ENGLISH):   # every screen in both languages
        i18n.set_language(language)
        for scene in (TitleScene(app), TopTenScene(app), ParentsScene(app), CreditsScene(app)):
            app.goto(scene)
            run(0.3)
        for tab in ("progress", "mistakes"):
            app.goto(ParentsScene(app))
            app.scene.tab = tab
            run(0.2)
    app.settings["difficulty"] = "easy"
    play = PlayScene(app, "easy")
    app.goto(play)
    run(240, until=lambda: not isinstance(app.scene, PlayScene))
    game = first_game = play.game
    if not isinstance(app.scene, GameOverScene):
        raise RuntimeError("the automatic game never reached game over")
    if app.scene.entering:
        for ch in "SMOKE":
            app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode=ch, mod=0))
        app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0))
        run(0.3)
    app.goto(ParentsScene(app))
    app.scene.tab = "mistakes"
    run(0.2)
    i18n.set_language(i18n.JAPANESE)   # a second game in Japanese, with mistakes
    play = PlayScene(app, "medium")
    app.goto(play)
    run(240, until=lambda: not isinstance(app.scene, PlayScene))
    run(0.3)
    app.goto(ParentsScene(app))
    app.scene.tab = "mistakes"
    run(0.2)
    result = (f"ok version={__version__} frames={frames} score={first_game.score} round={first_game.round} "
              f"sequences={first_game.sequences_done} japanese_game_score={play.game.score} audio={'ready' if app.audio.ready else 'off'}")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(result + "\n")
    pygame.quit()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="keyrush", description="Key Rush - a home-row memory typing game")
    parser.add_argument("--version", action="version", version=f"Key Rush {__version__}")
    parser.add_argument("--smoke-test", metavar="FILE", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.smoke_test:
            return smoke_test(args.smoke_test)
        App().run()
        return 0
    except Exception:
        text = traceback.format_exc()
        storage.log_crash(text)
        print(text, file=sys.stderr)
        return 1
