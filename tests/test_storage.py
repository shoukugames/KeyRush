import json
import os
import random

import pytest

from keyrush import storage
from keyrush.logic import Game


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv("KEYRUSH_DATA", str(tmp_path))
    return tmp_path


def test_top10_keeps_best_ten_per_difficulty(data):
    scores = storage.load_scores()
    for i in range(15):
        storage.add_score(scores, "easy", f"P{i}", i * 100, 1)
    reloaded = storage.load_scores()
    assert [r["score"] for r in reloaded["easy"]] == [1400 - i * 100 for i in range(10)]
    assert reloaded["hard"] == []
    assert storage.high_score(reloaded, "easy") == 1400


def test_qualifies():
    scores = storage.load_scores()
    assert not storage.qualifies(scores, "easy", 0)
    assert storage.qualifies(scores, "easy", 10)
    for i in range(10):
        storage.add_score(scores, "easy", "X", 500, 1)
    assert not storage.qualifies(scores, "easy", 500)
    assert storage.qualifies(scores, "easy", 510)


def test_add_score_returns_position_and_trims_name():
    scores = storage.load_scores()
    storage.add_score(scores, "medium", "A", 300, 2)
    place = storage.add_score(scores, "medium", "AVERYLONGNAMEINDEED", 900, 4)
    assert place == 0
    assert scores["medium"][0]["name"] == "AVERYLONGN"


def test_corrupt_file_is_set_aside(data):
    (data / "scores.json").write_text("{not json")
    assert storage.load_scores()["easy"] == []
    assert (data / "scores.json.corrupt").exists()


def test_record_game_builds_parent_stats(data):
    stats = storage.load_stats()
    g = Game("easy", rng=random.Random(2))
    while g.state != "input":
        g.update(1 / 60)
    g.press(next(k for k in g.keys if k != g.expected_key))
    g.update(3.0)
    storage.record_game(stats, g.summary())
    saved = json.loads((data / "stats.json").read_text())
    assert saved["games"] == 1
    assert saved["keys_wrong"] == 1
    assert saved["failures"] == 1
    assert sum(saved["key_errors"].values()) == 1
    assert len(saved["confusions"]) == 1
    assert saved["total_seconds"] > 0
    assert saved["daily"][storage.today()] > 0
    assert saved["history"][0]["difficulty"] == "easy"
    assert storage.load_stats()["games"] == 1


def test_history_is_capped(data):
    stats = storage.load_stats()
    g = Game("easy")
    for _ in range(storage.HISTORY_LENGTH + 5):
        storage.record_game(stats, g.summary())
    assert len(storage.load_stats()["history"]) == storage.HISTORY_LENGTH


def test_reset_stats_keeps_scores(data):
    scores = storage.load_scores()
    storage.add_score(scores, "easy", "KEEP", 100, 1)
    stats = storage.load_stats()
    storage.record_game(stats, Game("easy").summary())
    storage.reset_stats()
    assert storage.load_stats()["games"] == 0
    assert storage.load_scores()["easy"][0]["name"] == "KEEP"


def test_settings_round_trip(data):
    s = storage.load_settings()
    assert s["difficulty"] == "easy"
    s["difficulty"] = "hard"
    storage.save_settings(s)
    assert storage.load_settings()["difficulty"] == "hard"
    (data / "settings.json").write_text(json.dumps({"difficulty": "silly"}))
    assert storage.load_settings()["difficulty"] == "easy"


def test_data_dir_override(data):
    assert storage.data_dir() == str(data)
    assert os.path.isdir(storage.data_dir())
