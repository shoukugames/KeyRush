import random

import pytest

from keyrush.config import DIFFICULTIES, HOME_ROW, MAX_MISTAKES, SEQUENCES_PER_ROUND
from keyrush.logic import Game


def run_until_input(game, limit=60.0):
    t = 0.0
    while game.state != "input":
        game.update(1 / 60)
        t += 1 / 60
        assert t < limit, f"never reached input, stuck in {game.state}"


def play_sequence(game):
    run_until_input(game)
    for key in list(game.sequence):
        game.press(key)


def new_game(diff="medium", seed=1):
    return Game(diff, rng=random.Random(seed))


def test_sequence_is_shown_one_key_per_beat():
    g = new_game()
    flashes = []
    beats = 0
    while g.state != "input":
        g.update(1 / 120)
        for e in g.take_events():
            if e[0] == "beat":
                beats += 1
            if e[0] == "flash":
                flashes.append((e[1], beats))
    assert [k for k, _ in flashes] == g.sequence
    assert [b for _, b in flashes] == list(range(flashes[0][1], flashes[0][1] + len(g.sequence)))


def test_correct_sequence_scores_100_and_grows_by_one():
    g = new_game()
    first = list(g.sequence)
    play_sequence(g)
    assert g.score == 100
    assert g.sequence[:len(first)] == first
    assert len(g.sequence) == len(first) + 1


def test_four_sequences_make_a_round_and_speed_up():
    g = new_game()
    bpm = g.bpm
    for _ in range(SEQUENCES_PER_ROUND):
        assert g.round == 1
        play_sequence(g)
    assert g.round == 2
    assert g.score == 400
    assert g.bpm > bpm
    assert g.done_in_round == 0


def test_wrong_key_costs_10_points_and_a_heart_then_replays():
    g = new_game()
    play_sequence(g)
    run_until_input(g)
    seq = list(g.sequence)
    wrong = next(k for k in g.keys if k != seq[0])
    g.press(wrong)
    assert g.score == 90
    assert g.mistakes == 1
    assert g.state == "fail"
    assert g.sequence == seq          # the same sequence is shown again
    assert g.confusions[f"{seq[0]}>{wrong}"] == 1
    play_sequence(g)
    assert g.score == 190


def test_score_never_goes_below_zero():
    g = new_game()
    run_until_input(g)
    g.press(next(k for k in g.keys if k != g.expected_key))
    assert g.score == 0


def test_three_mistakes_end_the_game():
    g = new_game()
    for i in range(MAX_MISTAKES):
        run_until_input(g)
        g.press(next(k for k in g.keys if k != g.expected_key))
    assert g.over
    assert ("game_over",) in g.take_events()
    g.press("a")      # ignored after the end
    g.update(1.0)
    assert g.mistakes == MAX_MISTAKES


def test_running_out_of_time_is_a_mistake():
    g = new_game("easy")
    run_until_input(g)
    g.update(g.timeout + g.beat_len + 0.1)
    assert g.mistakes == 1
    assert g.timeouts == 1
    assert ("wrong", g.sequence[0], None) in g.take_events()


def test_keys_off_the_home_row_are_ignored():
    g = new_game()
    run_until_input(g)
    g.press("q")
    g.press("?")
    assert g.mistakes == 0
    assert any(e[0] == "off_row" for e in g.take_events())


def test_inactive_home_row_key_counts_as_wrong_on_easy():
    g = new_game("easy")
    run_until_input(g)
    g.press("a")
    assert g.mistakes == 1


def test_pressing_while_watching_is_not_a_mistake():
    g = new_game()
    while g.state != "show":
        g.update(1 / 60)
    g.press(g.sequence[0])
    assert g.mistakes == 0


@pytest.mark.parametrize("diff", list(DIFFICULTIES))
def test_sequences_only_use_the_difficulty_keys(diff):
    g = new_game(diff, seed=9)
    for _ in range(12):
        play_sequence(g)
        assert set(g.sequence) <= set(DIFFICULTIES[diff]["keys"])
        assert set(g.sequence) <= set(HOME_ROW)


def test_never_three_identical_keys_in_a_row():
    for seed in range(40):
        g = new_game("easy", seed)
        for _ in range(8):
            play_sequence(g)
            s = g.sequence
            assert not any(s[i] == s[i + 1] == s[i + 2] for i in range(len(s) - 2))


def test_difficulty_keeps_rising_without_end():
    g = new_game("hard")
    for _ in range(200):
        g.round += 1
    assert g.bpm == DIFFICULTIES["hard"]["bpm_max"]
    assert g.timeout == DIFFICULTIES["hard"]["timeout_min"]
    assert g.start_length == DIFFICULTIES["hard"]["max_start"]


def test_easy_is_easier_than_hard():
    e, h = new_game("easy"), new_game("hard")
    assert e.bpm < h.bpm
    assert e.timeout > h.timeout
    assert e.start_length < h.start_length
    assert len(e.keys) < len(h.keys)


def test_many_rounds_in_a_row():
    g = new_game("medium", 3)
    for _ in range(SEQUENCES_PER_ROUND * 6):
        play_sequence(g)
    assert g.round == 7
    assert g.score == 100 * SEQUENCES_PER_ROUND * 6
    assert not g.over


def test_summary_fields():
    g = new_game()
    play_sequence(g)
    run_until_input(g)
    g.press(next(k for k in g.keys if k != g.expected_key))
    s = g.summary()
    assert s["sequences"] == 1
    assert s["keys_wrong"] == 1
    assert s["failures"] == 1
    assert 0 < s["accuracy"] < 100
    assert s["seconds"] > 0
