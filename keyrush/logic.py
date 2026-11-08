"""The rules of Key Rush, free of any drawing or sound so they can be tested.

Everything runs on a beat clock. The game shows one key per beat, waits a
beat or two between sequences and changes tempo on the beat, so the music and
the keys always line up. The scene reads `events` each frame to play sounds
and animations, then clears the list.

Events (tuples):
    ("beat", index, beat_length)
    ("flash", key, duration, position)     a key of the sequence being shown
    ("your_turn",)
    ("ok", key, position)
    ("wrong", expected, pressed_or_None)    None means the time ran out
    ("sequence_done", points)
    ("round_up", round)
    ("off_row", key)                        a key that isn't on the home row
    ("early", key)                          a key pressed while watching
    ("game_over",)
"""
import random
from collections import Counter

from .config import (DIFFICULTIES, HOME_ROW, MAX_MISTAKES, PENALTY_PER_WRONG_KEY,
                     POINTS_PER_SEQUENCE, SEQUENCES_PER_ROUND)

INTRO_BEATS = 3
SUCCESS_BEATS = 2
ROUND_UP_BEATS = 3
FAIL_BEATS = 3
FLASH_FRACTION = 0.72


class Game:
    def __init__(self, difficulty="medium", rng=None):
        self.difficulty = difficulty
        self.cfg = DIFFICULTIES[difficulty]
        self.keys = list(self.cfg["keys"])
        self.rng = rng or random.Random()

        self.score = 0
        self.round = 1
        self.done_in_round = 0
        self.mistakes = 0
        self.sequence = []
        self.show_pos = 0
        self.input_pos = 0
        self.state = "intro"
        self.wait_beats = INTRO_BEATS
        self.time = 0.0
        self.beat_index = 0
        self.beat_len = 60.0 / self.bpm
        self.next_beat = 0.25
        self.input_deadline = None
        self.input_started = 0.0
        self.events = []

        # What the For Parents page needs
        self.keys_correct = 0
        self.keys_wrong = 0
        self.timeouts = 0
        self.sequences_done = 0
        self.sequence_failures = 0
        self.key_errors = Counter()
        self.confusions = Counter()
        self.longest_sequence = 0

        self._new_sequence()

    # Difficulty curve -------------------------------------------------------
    @property
    def bpm(self):
        c = self.cfg
        return min(c["bpm_max"], c["bpm"] + (self.round - 1) * c["bpm_step"])

    @property
    def timeout(self):
        c = self.cfg
        return max(c["timeout_min"], c["timeout"] - (self.round - 1) * c["timeout_step"])

    @property
    def start_length(self):
        c = self.cfg
        return min(c["max_start"], c["start_len"] + (self.round - 1) // c["len_every"])

    @property
    def expected_key(self):
        if self.state == "input" and self.input_pos < len(self.sequence):
            return self.sequence[self.input_pos]
        return None

    @property
    def over(self):
        return self.state == "over"

    @property
    def lives(self):
        return MAX_MISTAKES - self.mistakes

    @property
    def time_left_fraction(self):
        if self.state != "input" or self.input_deadline is None:
            return 1.0
        return max(0.0, min(1.0, (self.input_deadline - self.time) / self.timeout))

    # Sequence building ------------------------------------------------------
    def _random_key(self):
        """A random key, but never three of the same in a row."""
        while True:
            key = self.rng.choice(self.keys)
            if len(self.sequence) >= 2 and self.sequence[-1] == self.sequence[-2] == key:
                continue
            return key

    def _new_sequence(self):
        self.sequence = []
        for _ in range(self.start_length):
            self.sequence.append(self._random_key())

    def _extend_sequence(self):
        self.sequence.append(self._random_key())

    # Clock ------------------------------------------------------------------
    def update(self, dt):
        if self.state == "over":
            return
        self.time += dt
        while self.time >= self.next_beat and self.state != "over":
            self._on_beat()
            self.next_beat += self.beat_len
        if self.state == "input" and self.time >= self.input_deadline:
            self._mistake(None)

    def _on_beat(self):
        self.events.append(("beat", self.beat_index, self.beat_len))
        self.beat_index += 1
        if self.state in ("intro", "success", "fail"):
            self.wait_beats -= 1
            if self.wait_beats > 0:
                return
            self.state = "show"
            self.show_pos = 0
        if self.state == "show":
            if self.show_pos < len(self.sequence):
                key = self.sequence[self.show_pos]
                self.events.append(("flash", key, self.beat_len * FLASH_FRACTION, self.show_pos))
                self.show_pos += 1
            else:
                self.state = "input"
                self.input_pos = 0
                self.input_started = self.time
                # The first key gets an extra beat, while the player's eyes move
                self.input_deadline = self.time + self.timeout + self.beat_len
                self.events.append(("your_turn",))

    # Player input -----------------------------------------------------------
    def press(self, key):
        if self.state == "over":
            return
        if key not in HOME_ROW:
            self.events.append(("off_row", key))
            return
        if self.state != "input":
            self.events.append(("early", key))
            return
        expected = self.sequence[self.input_pos]
        if key != expected:
            self._mistake(key)
            return
        self.keys_correct += 1
        self.events.append(("ok", key, self.input_pos))
        self.input_pos += 1
        self.input_deadline = self.time + self.timeout
        if self.input_pos >= len(self.sequence):
            self._complete()

    def _complete(self):
        self.score += POINTS_PER_SEQUENCE
        self.sequences_done += 1
        self.done_in_round += 1
        self.longest_sequence = max(self.longest_sequence, len(self.sequence))
        self.events.append(("sequence_done", POINTS_PER_SEQUENCE))
        self.state = "success"
        if self.done_in_round >= SEQUENCES_PER_ROUND:
            self.round += 1
            self.done_in_round = 0
            self.beat_len = 60.0 / self.bpm   # takes effect from the next beat
            self._new_sequence()
            self.wait_beats = ROUND_UP_BEATS
            self.events.append(("round_up", self.round))
        else:
            self._extend_sequence()
            self.wait_beats = SUCCESS_BEATS

    def _mistake(self, pressed):
        expected = self.sequence[self.input_pos]
        self.mistakes += 1
        self.sequence_failures += 1
        self.key_errors[expected] += 1
        if pressed is None:
            self.timeouts += 1
        else:
            self.keys_wrong += 1
            self.confusions[f"{expected}>{pressed}"] += 1
        self.score = max(0, self.score - PENALTY_PER_WRONG_KEY)
        self.events.append(("wrong", expected, pressed))
        self.input_deadline = None
        if self.mistakes >= MAX_MISTAKES:
            self.state = "over"
            self.events.append(("game_over",))
        else:
            # Watch the same sequence again
            self.state = "fail"
            self.wait_beats = FAIL_BEATS

    def take_events(self):
        events, self.events = self.events, []
        return events

    def summary(self):
        """The finished game, as stored in the parents' history."""
        total = self.keys_correct + self.keys_wrong + self.timeouts
        return {
            "difficulty": self.difficulty,
            "score": self.score,
            "round": self.round,
            "sequences": self.sequences_done,
            "longest": self.longest_sequence,
            "keys_correct": self.keys_correct,
            "keys_wrong": self.keys_wrong,
            "timeouts": self.timeouts,
            "failures": self.sequence_failures,
            "accuracy": round(100 * self.keys_correct / total, 1) if total else 0.0,
            "seconds": round(self.time, 1),
            "key_errors": dict(self.key_errors),
            "confusions": dict(self.confusions),
        }
