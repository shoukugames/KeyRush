from keyrush import audio
from keyrush.config import HOME_ROW


def test_every_sample_builds_and_is_stereo_16_bit():
    sounds = audio.build_all()
    for key in HOME_ROW:
        assert f"key_{key}" in sounds
    for name in ("kick", "success", "wrong", "round_up", "game_over", "pad_0", "pad_3"):
        assert name in sounds
    for name, data in sounds.items():
        assert len(data) % 4 == 0 and len(data) > 0, name


def test_pad_loops_without_a_click():
    import array
    pcm = array.array("h", audio._pad(audio.CHORDS[0][0]))
    left = pcm[0::2]
    biggest_step = max(abs(left[i + 1] - left[i]) for i in range(len(left) - 1))
    assert abs(left[0] - left[-1]) <= biggest_step * 1.05   # a click would be many times larger


def test_music_follows_beats_without_audio_device():
    class Silent:
        def __init__(self):
            self.played = []

        def play(self, name, volume=1.0, music=False):
            self.played.append(name)

        def play_pad(self, index, fade_ms=0):
            self.played.append(f"pad_{index}")

    a = Silent()
    m = audio.Music(a, seed=1)
    m.intensity = 5
    for i in range(32):
        m.on_beat(i, 0.5)
        m.update(0.5)
    assert "pad_0" in a.played and "pad_1" in a.played
    assert a.played.count("kick") >= 8
    assert "shaker" in a.played
