"""Saves the Top 10 tables, the parents' statistics and settings as JSON.

Files live in the per-user data folder, so they survive updates and the game
works when installed somewhere read-only. A damaged file is set aside with a
`.corrupt` suffix and replaced, rather than stopping the game.
"""
import datetime
import json
import os
import sys
import tempfile

from .config import DIFFICULTY_ORDER, NAME_LENGTH, TOP_SCORES

HISTORY_LENGTH = 30
DAILY_LENGTH = 60


def data_dir():
    override = os.environ.get("KEYRUSH_DATA")
    if override:
        path = override
    elif sys.platform == "win32":
        path = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "KeyRush")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        path = os.path.join(base, "keyrush")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = os.path.join(tempfile.gettempdir(), "keyrush")
        os.makedirs(path, exist_ok=True)
    return path


def _load(name, default):
    path = os.path.join(data_dir(), name)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, type(default)):
            return data
        raise ValueError("unexpected structure")
    except FileNotFoundError:
        return default
    except (OSError, ValueError):
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return default


def _save(name, data):
    path = os.path.join(data_dir(), name)
    temp = path + ".tmp"
    try:
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(temp, path)
    except OSError as error:
        print(f"Key Rush: could not save {name}: {error}", file=sys.stderr)


def today():
    return datetime.date.today().isoformat()


# Settings -------------------------------------------------------------------
DEFAULT_SETTINGS = {"difficulty": "easy", "music": True, "sound": True, "fullscreen": False, "language": ""}


def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    settings.update(_load("settings.json", {}))
    if settings["difficulty"] not in DIFFICULTY_ORDER:
        settings["difficulty"] = "easy"
    return settings


def save_settings(settings):
    _save("settings.json", settings)


# Top 10 ---------------------------------------------------------------------
def load_scores():
    raw = _load("scores.json", {})
    scores = {}
    for diff in DIFFICULTY_ORDER:
        rows = raw.get(diff, [])
        clean = []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get("score"), int):
                    clean.append({"name": str(row.get("name", "?"))[:NAME_LENGTH],
                                  "score": row["score"], "round": int(row.get("round", 1)),
                                  "date": str(row.get("date", ""))})
        clean.sort(key=lambda r: -r["score"])
        scores[diff] = clean[:TOP_SCORES]
    return scores


def high_score(scores, difficulty):
    rows = scores.get(difficulty, [])
    return rows[0]["score"] if rows else 0


def qualifies(scores, difficulty, score):
    if score <= 0:
        return False
    rows = scores.get(difficulty, [])
    return len(rows) < TOP_SCORES or score > rows[-1]["score"]


def add_score(scores, difficulty, name, score, round_reached):
    """Adds an entry and returns its position in the table (0-based), or None."""
    rows = scores.setdefault(difficulty, [])
    entry = {"name": (name.strip() or "PLAYER")[:NAME_LENGTH], "score": score,
             "round": round_reached, "date": today()}
    rows.append(entry)
    rows.sort(key=lambda r: -r["score"])   # stable, so earlier ties stay above
    del rows[TOP_SCORES:]
    _save("scores.json", scores)
    return rows.index(entry) if entry in rows else None


# Parents' statistics --------------------------------------------------------
def empty_stats():
    return {
        "total_seconds": 0.0, "games": 0, "game_overs": 0,
        "keys_correct": 0, "keys_wrong": 0, "timeouts": 0,
        "sequences": 0, "failures": 0,
        "best": {d: {"score": 0, "round": 0} for d in DIFFICULTY_ORDER},
        "key_errors": {}, "confusions": {},
        "daily": {}, "history": [], "first_played": "",
    }


def load_stats():
    stats = empty_stats()
    raw = _load("stats.json", {})
    for key, value in raw.items():
        if key in stats and isinstance(value, type(stats[key])):
            stats[key] = value
        elif key in stats and isinstance(stats[key], float) and isinstance(value, int):
            stats[key] = float(value)
    for d in DIFFICULTY_ORDER:
        stats["best"].setdefault(d, {"score": 0, "round": 0})
    return stats


def save_stats(stats):
    _save("stats.json", stats)


def reset_stats():
    stats = empty_stats()
    save_stats(stats)
    return stats


def record_game(stats, summary, finished=True):
    """Adds one game to the statistics and saves them."""
    day = today()
    stats["first_played"] = stats.get("first_played") or day
    stats["total_seconds"] += summary["seconds"]
    stats["games"] += 1
    if finished:
        stats["game_overs"] += 1
    for key in ("keys_correct", "keys_wrong", "timeouts"):
        stats[key] += summary[key]
    stats["sequences"] += summary["sequences"]
    stats["failures"] += summary["failures"]

    best = stats["best"].setdefault(summary["difficulty"], {"score": 0, "round": 0})
    best["score"] = max(best["score"], summary["score"])
    best["round"] = max(best["round"], summary["round"])

    for key, count in summary["key_errors"].items():
        stats["key_errors"][key] = stats["key_errors"].get(key, 0) + count
    for pair, count in summary["confusions"].items():
        stats["confusions"][pair] = stats["confusions"].get(pair, 0) + count

    stats["daily"][day] = round(stats["daily"].get(day, 0) + summary["seconds"], 1)
    for old in sorted(stats["daily"])[:-DAILY_LENGTH]:
        del stats["daily"][old]

    entry = {k: v for k, v in summary.items() if k not in ("key_errors", "confusions")}
    entry["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry["finished"] = finished
    stats["history"].append(entry)
    del stats["history"][:-HISTORY_LENGTH]
    save_stats(stats)


def log_crash(text):
    try:
        with open(os.path.join(data_dir(), "crash.log"), "a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except OSError:
        pass
