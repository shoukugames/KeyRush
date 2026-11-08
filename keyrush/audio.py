"""All sound is synthesised in code: key bells, effects and the ambient music.

The samples are built on a background thread so the title screen appears at
once; sounds simply start once they're ready. If there is no audio device the
game carries on silently, because every public method checks `self.enabled`.

The music follows a beat clock supplied by the caller (the game's own clock
during play), so drums, chord changes and the key bells all land together.
"""
import array
import itertools
import math
import operator
import random
import threading

import pygame

SAMPLE_RATE = 22050
TABLE_SIZE = 8192
TWO_PI = 2 * math.pi
SINE = [math.sin(TWO_PI * i / TABLE_SIZE) for i in range(TABLE_SIZE)]
# A soft, organ-like wave for the pads: a sine with a few quiet harmonics
WARM = [math.sin(TWO_PI * i / TABLE_SIZE) + 0.22 * math.sin(2 * TWO_PI * i / TABLE_SIZE)
        + 0.08 * math.sin(3 * TWO_PI * i / TABLE_SIZE) for i in range(TABLE_SIZE)]

# C major pentatonic across the home row, so any sequence sounds musical
KEY_NOTES = {
    "a": 261.63, "s": 293.66, "d": 329.63, "f": 392.00, "g": 440.00,
    "h": 523.25, "j": 587.33, "k": 659.25, "l": 783.99, ";": 880.00,
}
# Dreamy seventh chords: pad voicing and bass root
CHORDS = [
    ([130.81, 164.81, 196.00, 246.94, 329.63], 65.41),   # Cmaj7
    ([110.00, 130.81, 164.81, 196.00, 261.63], 55.00),   # Am7
    ([87.31, 110.00, 130.81, 164.81, 220.00], 43.65),    # Fmaj7
    ([98.00, 123.47, 146.83, 164.81, 293.66], 49.00),    # G6
]
SPARKLE_NOTES = [[1046.5, 1318.5, 1568.0, 783.99], [880.0, 1046.5, 1318.5, 1568.0],
                 [880.0, 1046.5, 1318.5, 1760.0], [783.99, 1174.7, 1568.0, 987.77]]
PAD_SECONDS = 4.0


# Synthesis helpers (plain lists of floats) ----------------------------------
def _osc(freq, n, table=SINE, offset=0):
    inc = freq * TABLE_SIZE / SAMPLE_RATE
    return [table[int(i * inc + offset) % TABLE_SIZE] for i in range(n)]


_DECAYS = {}


def _decay(rate, n):
    """exp(-rate * t) for n samples, built by repeated multiplication (fast)."""
    key = (rate, n)
    if key not in _DECAYS:
        step = math.exp(-rate / SAMPLE_RATE)
        _DECAYS[key] = list(itertools.accumulate(itertools.repeat(step, n - 1), operator.mul,
                                                 initial=1.0))
    return _DECAYS[key]


def _bell(freq, dur=1.6, vol=0.5, partials=((1.0, 1.0, 3.2), (2.0, 0.32, 6.5),
                                             (3.0, 0.10, 10.0), (4.17, 0.05, 14.0))):
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    for ratio, amp, decay in partials:
        inc = freq * ratio * TABLE_SIZE / SAMPLE_RATE
        env = _decay(decay, n)
        out = [o + amp * e * SINE[int(i * inc) % TABLE_SIZE]
               for i, (o, e) in enumerate(zip(out, env))]
    attack = int(0.004 * SAMPLE_RATE)
    for i in range(attack):
        out[i] *= i / attack
    fade = int(0.05 * SAMPLE_RATE)
    for i in range(fade):
        out[n - 1 - i] *= i / fade
    return _scale(out, vol)


def _sweep(f0, f1, dur, vol, decay=6.0, table=SINE):
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        t = i / n
        phase += (f0 * (f1 / f0) ** t) * TABLE_SIZE / SAMPLE_RATE
        out[i] = table[int(phase) % TABLE_SIZE] * math.exp(-decay * t) * (1 - t ** 4)
    return _scale(out, vol, normalise=False)


def _noise(dur, vol, brightness=0.5, decay=30.0, highpass=True, seed=3):
    rng = random.Random(seed)
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    low = 0.0
    for i in range(n):
        x = rng.uniform(-1, 1)
        low += brightness * (x - low)
        v = (x - low) if highpass else low
        out[i] = v * math.exp(-decay * i / SAMPLE_RATE)
    return _scale(out, vol)


def _scale(samples, vol, normalise=True):
    peak = (max(max(samples, default=0), -min(samples, default=0))) if normalise else 1.0
    if peak <= 0:
        return samples
    k = vol / peak
    return [v * k for v in samples]


def _mix(*parts, offsets=None):
    offsets = offsets or [0] * len(parts)
    n = max(len(p) + int(o * SAMPLE_RATE) for p, o in zip(parts, offsets))
    out = [0.0] * n
    for part, off in zip(parts, offsets):
        start = int(off * SAMPLE_RATE)
        for i, v in enumerate(part):
            out[start + i] += v
    return out


def _echo(samples, delay, feedback, repeats=4, tail=0.0):
    d = int(delay * SAMPLE_RATE)
    out = samples + [0.0] * (d * repeats + int(tail * SAMPLE_RATE))
    for i in range(d, len(out)):
        out[i] += out[i - d] * feedback
    return out


def _pcm(samples, n):
    data = array.array("h", [int(32000 * (1.0 if v > 1.0 else (-1.0 if v < -1.0 else v)))
                             for v in samples])
    if len(data) < n:
        data.extend([0] * (n - len(data)))
    return data


def _stereo(left, right=None):
    right = left if right is None else right
    n = max(len(left), len(right))
    buf = array.array("h", [0]) * (2 * n)
    buf[0::2] = _pcm(left, n)
    buf[1::2] = _pcm(right, n)
    return buf.tobytes()


def _spacious(mono, vol=1.0):
    """A dry sound with a different echo in each ear, for width."""
    left = _echo(mono, 0.19, 0.28, tail=0.2)
    right = _echo(mono, 0.27, 0.24, tail=0.2)
    return _stereo(_scale(left, vol), _scale(right, vol))


def _pad(freqs):
    """A seamless 4 second loop. Every frequency, detune and wobble is rounded to
    whole cycles per loop, so it repeats without a click."""
    n = int(PAD_SECONDS * SAMPLE_RATE)
    step = 1.0 / PAD_SECONDS
    lfo = [0.62 + 0.38 * math.sin(TWO_PI * i / n) for i in range(n)]
    left = [0.0] * n
    right = [0.0] * n
    for idx, f in enumerate(freqs):
        f = round(f / step) * step
        amp = 0.5 if idx == len(freqs) - 1 else 1.0
        shift = idx * n // len(freqs)
        for chan, detune in ((left, -step), (right, step)):
            wave = _osc(f + detune, n, WARM)
            env = lfo[shift:] + lfo[:shift]
            chan[:] = [c + w * e * amp for c, w, e in zip(chan, wave, env)]
    peak = max(max(left), -min(left), max(right), -min(right))
    return _stereo([v * 0.8 / peak for v in left], [v * 0.8 / peak for v in right])


def build_all():
    """Every sample as raw stereo bytes, keyed by name."""
    s = {}
    for key, freq in KEY_NOTES.items():
        s[f"key_{key}"] = _spacious(_bell(freq, 1.5, 0.9), 0.95)
    s["kick"] = _stereo(_mix(_sweep(120, 40, 0.42, 0.9, decay=6.5), _noise(0.02, 0.15, 0.9, 120)))
    s["shaker"] = _stereo(_noise(0.08, 0.6, 0.35, 45, seed=5))
    s["hat"] = _stereo(_noise(0.05, 0.5, 0.2, 70, seed=9))
    for i, (_, root) in enumerate(CHORDS):
        s[f"bass_{i}"] = _stereo(_sweep(root * 2, root * 2, 2.6, 0.9, decay=2.2))
    for i, row in enumerate(SPARKLE_NOTES):
        for j, freq in enumerate(row):
            s[f"sparkle_{i}_{j}"] = _spacious(_bell(freq, 1.8, 0.8,
                                                    ((1.0, 1.0, 2.5), (2.0, 0.15, 6.0))), 0.9)
    s["success"] = _spacious(_mix(*[_bell(f, 1.2, 0.6) for f in (523.25, 659.25, 783.99, 1046.5)],
                                  offsets=[0, 0.07, 0.14, 0.21]), 0.9)
    s["round_up"] = _spacious(_mix(*[_bell(f, 1.4, 0.55) for f in
                                     (392.0, 523.25, 659.25, 783.99, 1046.5, 1318.5)],
                                   _noise(0.9, 0.18, 0.08, 3.5, highpass=False, seed=7),
                                   offsets=[0, 0.06, 0.12, 0.18, 0.24, 0.30, 0]), 0.95)
    s["wrong"] = _stereo(_mix(_sweep(220, 110, 0.38, 0.55, decay=5.0,
                                     table=[abs(v) * 2 - 0.6 for v in SINE]),
                              _noise(0.15, 0.25, 0.1, 25, highpass=False)))
    s["game_over"] = _spacious(_mix(*[_bell(f, 1.6, 0.6) for f in (392.0, 329.63, 261.63, 196.0)],
                                    offsets=[0, 0.24, 0.48, 0.72]), 0.9)
    s["start"] = _spacious(_mix(_noise(0.6, 0.25, 0.05, 4.0, highpass=False, seed=11),
                                *[_bell(f, 1.2, 0.5) for f in (261.63, 392.0, 523.25)],
                                offsets=[0, 0.05, 0.12, 0.19]), 0.9)
    s["move"] = _stereo(_bell(1318.5, 0.12, 0.35, ((1.0, 1.0, 30.0),)))
    s["select"] = _spacious(_mix(_bell(783.99, 0.6, 0.5), _bell(1174.7, 0.6, 0.5),
                                 offsets=[0, 0.06]), 0.7)
    s["type"] = _stereo(_noise(0.03, 0.4, 0.6, 120, seed=13))
    s["off_row"] = _stereo(_bell(330.0, 0.15, 0.3, ((1.0, 1.0, 25.0),)))
    for i, (voicing, _) in enumerate(CHORDS):
        s[f"pad_{i}"] = _pad(voicing)
    return s


class Audio:
    PAD_VOLUME = 0.32

    def __init__(self, music=True, sound=True):
        self.music_on = music
        self.sound_on = sound
        self.enabled = False
        self.ready = False
        self.sounds = {}
        self._raw = None
        try:
            pygame.mixer.quit()
            pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.set_num_channels(32)
            pygame.mixer.set_reserved(2)
            self.pad_channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
            self.enabled = True
        except pygame.error:
            return
        threading.Thread(target=self._build, daemon=True).start()

    def _build(self):
        self._raw = build_all()

    def poll(self):
        """Turns finished samples into Sounds, on the main thread."""
        if self.enabled and not self.ready and self._raw is not None:
            self.sounds = {name: pygame.mixer.Sound(buffer=data) for name, data in self._raw.items()}
            self._raw = None
            self.ready = True

    def wait_ready(self, timeout=60.0):
        """Blocks until the samples exist (used by tests and the smoke test)."""
        import time
        end = time.time() + timeout
        while self.enabled and not self.ready and time.time() < end:
            self.poll()
            time.sleep(0.02)

    def play(self, name, volume=1.0, music=False):
        if not (self.enabled and self.ready):
            return
        if not (self.music_on if music else self.sound_on):
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        channel = sound.play()
        if channel is not None:
            channel.set_volume(volume)

    def key(self, key, volume=0.8):
        self.play(f"key_{key}", volume)

    def play_pad(self, index, fade_ms=1800):
        if not (self.enabled and self.ready):
            return
        old, new = self.pad_channels
        old.fadeout(fade_ms)
        if self.music_on:
            new.play(self.sounds[f"pad_{index}"], loops=-1, fade_ms=fade_ms)
            new.set_volume(self.PAD_VOLUME)
        self.pad_channels = [new, old]

    def stop_pads(self, fade_ms=800):
        if self.enabled:
            for channel in self.pad_channels:
                channel.fadeout(fade_ms)

    def set_music(self, on):
        self.music_on = on
        if not on:
            self.stop_pads(300)


class Music:
    """Ambient pads, bass, drums and sparkles that follow a beat clock.

    Intensity 0 is pads only; each level up adds a layer of soft percussion.
    """

    def __init__(self, audio, seed=None):
        self.audio = audio
        self.rng = random.Random(seed)
        self.chord = -1
        self.beats_on_chord = 999
        self.time = 0.0
        self.pending = []
        self.intensity = 0
        self.sparkles = True

    def start(self):
        self.chord = -1
        self.beats_on_chord = 999

    def on_beat(self, index, beat_len):
        a = self.audio
        chord_beats = max(4, int(round(6.5 / beat_len / 4.0)) * 4)
        if self.beats_on_chord >= chord_beats and index % 4 == 0:
            self.chord = (self.chord + 1) % len(CHORDS)
            self.beats_on_chord = 0
            a.play_pad(self.chord)
            a.play(f"bass_{self.chord}", 0.38, music=True)
        self.beats_on_chord += 1
        bar = index % 4
        level = self.intensity
        if level >= 1 and bar == 0:
            a.play("kick", 0.42, music=True)
        if level >= 2 and bar == 2:
            a.play("kick", 0.34, music=True)
        if level >= 3:
            self._later(beat_len / 2, "shaker", 0.16)
        if level >= 4 and bar in (1, 3):
            a.play("hat", 0.14, music=True)
        if level >= 5:
            self._later(beat_len * 0.75, "shaker", 0.09)
        if self.sparkles and self.chord >= 0 and self.rng.random() < 0.4:
            note = self.rng.randrange(4)
            when = self.rng.choice((0.0, beat_len / 2))
            self._later(when, f"sparkle_{self.chord}_{note}", 0.13)

    def _later(self, delay, name, volume):
        self.pending.append((self.time + delay, name, volume))

    def update(self, dt):
        self.time += dt
        if not self.pending:
            return
        due = [p for p in self.pending if p[0] <= self.time]
        if due:
            self.pending = [p for p in self.pending if p[0] > self.time]
            for _, name, volume in due:
                self.audio.play(name, volume, music=True)

    def clear(self):
        self.pending = []
