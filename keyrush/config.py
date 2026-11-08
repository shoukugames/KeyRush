"""Game constants: screen, rules, difficulty curves and colours."""

TITLE = "Key Rush"
WIDTH, HEIGHT = 1280, 720
FPS = 60

CREATOR = "Shawn Rapaz"
WEBSITE = "https://shoukugames.org/"
EMAIL = "info@shoukugames.org"
LICENSE_NAME = "GNU General Public License v3.0"
RECOMMENDED_AGE = "8+"

# The home row, left to right. Fingers rest on A S D F and J K L ;
HOME_ROW = ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";"]
FINGERS = {
    "a": "L pinky", "s": "L ring", "d": "L middle", "f": "L index", "g": "L index",
    "h": "R index", "j": "R index", "k": "R middle", "l": "R ring", ";": "R pinky",
}
FINGER_COLORS = {
    "a": (190, 110, 255), "s": (90, 150, 255), "d": (60, 215, 190), "f": (255, 170, 70),
    "g": (255, 205, 110), "h": (255, 205, 110),
    "j": (255, 170, 70), "k": (60, 215, 190), "l": (90, 150, 255), ";": (190, 110, 255),
}


def key_label(key):
    return key.upper()


# Rules
MAX_MISTAKES = 3
POINTS_PER_SEQUENCE = 100
PENALTY_PER_WRONG_KEY = 10
SEQUENCES_PER_ROUND = 4
TOP_SCORES = 10
NAME_LENGTH = 10

# Each round the tempo rises, the time allowed per key shrinks and, every
# `len_every` rounds, sequences start one key longer. Within a round the
# sequence grows by one key each time, just like classic Simon.
DIFFICULTIES = {
    "easy": {
        "label": "Easy", "keys": "dfjk",
        "start_len": 2, "len_every": 2, "max_start": 9,
        "bpm": 72, "bpm_step": 4, "bpm_max": 150,
        "timeout": 4.5, "timeout_step": 0.15, "timeout_min": 1.6,
        "blurb": "4 keys: D F J K",
    },
    "medium": {
        "label": "Medium", "keys": "asdfjkl;",
        "start_len": 3, "len_every": 2, "max_start": 12,
        "bpm": 84, "bpm_step": 5, "bpm_max": 172,
        "timeout": 3.5, "timeout_step": 0.15, "timeout_min": 1.2,
        "blurb": "8 keys: A S D F  J K L ;",
    },
    "hard": {
        "label": "Hard", "keys": "asdfghjkl;",
        "start_len": 4, "len_every": 2, "max_start": 16,
        "bpm": 96, "bpm_step": 6, "bpm_max": 200,
        "timeout": 3.0, "timeout_step": 0.15, "timeout_min": 0.9,
        "blurb": "The whole home row, G and H too",
    },
}
DIFFICULTY_ORDER = ["easy", "medium", "hard"]

# Palette
BG_TOP = (14, 12, 44)
BG_BOTTOM = (8, 40, 64)
WHITE = (245, 246, 255)
SOFT = (170, 180, 220)
DIM = (100, 108, 150)
ACCENT = (110, 230, 255)
GOLD = (255, 210, 90)
GOOD = (110, 240, 150)
BAD = (255, 95, 110)
PANEL = (20, 24, 60)
PANEL_EDGE = (70, 90, 170)
