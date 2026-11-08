import string

import pytest

from keyrush import i18n
from keyrush.config import DIFFICULTY_ORDER, HOME_ROW


@pytest.fixture(autouse=True)
def restore():
    yield
    i18n.set_language(i18n.ENGLISH)


def test_every_string_has_both_languages_with_the_same_placeholders():
    fmt = string.Formatter()
    for key, (en, ja) in i18n.STRINGS.items():
        assert en and ja, key
        names_en = {f for _, f, _, _ in fmt.parse(en) if f}
        names_ja = {f for _, f, _, _ in fmt.parse(ja) if f}
        assert names_en == names_ja, key


@pytest.mark.parametrize("language", [i18n.ENGLISH, i18n.JAPANESE])
def test_every_string_formats(language):
    i18n.set_language(language)
    fmt = string.Formatter()
    for key, (en, _) in i18n.STRINGS.items():
        values = {f: "X" for _, f, _, _ in fmt.parse(en) if f}
        assert i18n.t(key, **values)
    for key in HOME_ROW:
        assert i18n.finger(key)
    for diff in DIFFICULTY_ORDER:
        assert i18n.difficulty_label(diff) and i18n.difficulty_blurb(diff)
    assert i18n.duration(3725) and i18n.praise_words()


def test_toggle_and_japanese_text():
    i18n.set_language(i18n.ENGLISH)
    assert i18n.t("menu.play") == "PLAY"
    assert i18n.toggle_language() == i18n.JAPANESE
    assert i18n.t("menu.play") == "プレイ"
    assert i18n.duration(125) == "2分05秒"
    assert i18n.toggle_language() == i18n.ENGLISH


def test_font_has_every_japanese_character():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    from keyrush import ui
    pygame.init()
    f = pygame.font.Font(ui.FONT_PATH, 20)
    chars = set()
    for _, ja in i18n.STRINGS.values():
        chars |= set(ja)
    for name in i18n.FINGER_NAMES.values():
        chars |= set(name[1])
    for row in i18n.PRAISE[1] + i18n.WEEKDAYS[1]:
        chars |= set(row)
    missing = [c for c in chars if not c.isspace() and f.metrics(c)[0] is None]
    assert not missing
