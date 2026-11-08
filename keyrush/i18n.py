"""English and Japanese text for the whole game.

The keys themselves (A S D F ...) stay as letters in both languages, because
they are the letters printed on the keyboard.
"""
import os
import sys

ENGLISH, JAPANESE = "en", "ja"
LANGUAGE_NAMES = {ENGLISH: "English", JAPANESE: "日本語"}

_current = ENGLISH


def get_language():
    return _current


def set_language(language):
    global _current
    _current = JAPANESE if language == JAPANESE else ENGLISH


def toggle_language():
    set_language(ENGLISH if _current == JAPANESE else JAPANESE)
    return _current


def detect_language():
    """The first-run choice: Japanese on a Japanese system, otherwise English."""
    if sys.platform == "win32":
        try:
            import ctypes
            primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            return JAPANESE if primary == 0x11 else ENGLISH
        except (AttributeError, OSError):
            return ENGLISH
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name)
        if value and value not in ("C", "POSIX"):
            return JAPANESE if value.lower().startswith("ja") else ENGLISH
    return ENGLISH


def t(string_id, **values):
    text = STRINGS[string_id][1 if _current == JAPANESE else 0]
    return text.format(**values) if values else text


def finger(key):
    return FINGER_NAMES[key][1 if _current == JAPANESE else 0]


def difficulty_label(difficulty):
    return t(f"diff.{difficulty}")


def difficulty_blurb(difficulty):
    return t(f"blurb.{difficulty}")


def praise_words():
    return PRAISE[1 if _current == JAPANESE else 0]


def weekday(date):
    return WEEKDAYS[1 if _current == JAPANESE else 0][date.weekday()]


def long_date(date):
    if _current == JAPANESE:
        return f"{date.year}年{date.month}月{date.day}日"
    return f"{date.strftime('%B')} {date.day}, {date.year}"


def duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    ja = _current == JAPANESE
    if h:
        return f"{h}時間{m:02d}分" if ja else f"{h}h {m:02d}m"
    if m:
        return f"{m}分{s:02d}秒" if ja else f"{m}m {s:02d}s"
    return f"{s}秒" if ja else f"{s}s"


FINGER_NAMES = {
    "a": ("L pinky", "左小指"), "s": ("L ring", "左薬指"), "d": ("L middle", "左中指"),
    "f": ("L index", "左人差し指"), "g": ("L index", "左人差し指"),
    "h": ("R index", "右人差し指"), "j": ("R index", "右人差し指"), "k": ("R middle", "右中指"),
    "l": ("R ring", "右薬指"), ";": ("R pinky", "右小指"),
}

PRAISE = (
    ["Great!", "Nice!", "Awesome!", "Perfect!", "Super!", "Brilliant!", "Yes!", "Fantastic!"],
    ["すごい！", "いいね！", "やったね！", "パーフェクト！", "さすが！", "天才！", "その調子！", "最高！"],
)

WEEKDAYS = (
    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ["月", "火", "水", "木", "金", "土", "日"],
)

STRINGS = {
    # Difficulty
    "diff.easy": ("Easy", "かんたん"),
    "diff.medium": ("Medium", "ふつう"),
    "diff.hard": ("Hard", "むずかしい"),
    "blurb.easy": ("4 keys: D F J K", "4つのキー: D F J K"),
    "blurb.medium": ("8 keys: A S D F  J K L ;", "8つのキー: A S D F  J K L ;"),
    "blurb.hard": ("The whole home row, G and H too", "ホームポジション全部（G と H も）"),

    # Title
    "title.tagline": ("Watch.  Remember.  Type it back!", "見て、覚えて、打ち返そう！"),
    "menu.play": ("PLAY", "プレイ"),
    "menu.top10": ("TOP 10", "トップ10"),
    "menu.parents": ("FOR PARENTS", "保護者の方へ"),
    "menu.credits": ("CREDITS", "クレジット"),
    "menu.music": ("MUSIC: {state}", "音楽: {state}"),
    "menu.language": ("LANGUAGE: {name}", "言語: {name}"),
    "menu.quit": ("QUIT", "終了"),
    "on": ("ON", "オン"),
    "off": ("OFF", "オフ"),
    "title.fingers": ("Rest your fingers on  A S D F    J K L ;", "指を  A S D F    J K L ;  に置こう"),
    "title.high": ("HIGH SCORE  {n}", "ハイスコア  {n}"),
    "title.age": ("Recommended ages 8+", "対象年齢 8歳以上"),
    "title.help": ("Arrows + Enter, or the mouse  ·  M music  ·  F11 full screen",
                   "矢印キー + Enter またはマウス  ·  M 音楽  ·  F11 全画面"),
    "title.loading": ("Tuning instruments...", "楽器を準備中..."),

    # Play
    "play.ready": ("Get ready...", "準備して..."),
    "play.ready_sub": ("Put your fingers on the home row", "指をホームポジションに置こう"),
    "play.watch": ("WATCH", "よく見て！"),
    "play.watch_sub": ("Remember the keys that light up", "光るキーを覚えよう"),
    "play.turn": ("YOUR TURN", "きみの番！"),
    "play.turn_sub": ("Type the keys in the same order", "同じ順番でキーを打とう"),
    "play.slow": ("Too slow!", "時間切れ！"),
    "play.oops": ("Oops!", "おっと！"),
    "play.it_was": ("It was {key}  ({finger}).", "正解は {key}（{finger}）。"),
    "play.hearts_left": ("{n} hearts left - watch again", "残りハート {n} - もう一度見よう"),
    "play.heart_left": ("1 heart left - watch again", "残りハート 1 - もう一度見よう"),
    "play.game_over": ("GAME OVER", "ゲームオーバー"),
    "play.round": ("ROUND {n}", "ラウンド {n}"),
    "play.round_sub": ("Faster and longer - you can do it!", "もっと速く、もっと長く。がんばれ！"),
    "play.home_row": ("Keep your fingers on the home row", "指はホームポジションに置いたままで"),
    "play.wait": ("Wait - watch first, then type", "まずは見てから打とう"),
    "play.footer": ("Fingers rest on  A S D F    J K L ;   - thumbs on the space bar",
                    "指は  A S D F    J K L ;  に、親指はスペースキーに"),
    "play.keys": ("Esc pause  ·  M music", "Esc 一時停止  ·  M 音楽"),
    "hud.score": ("SCORE", "スコア"),
    "hud.high": ("HIGH SCORE", "ハイスコア"),
    "pause.title": ("PAUSED", "一時停止中"),
    "pause.resume": ("Enter or Esc - keep playing", "Enter または Esc - 続ける"),
    "pause.quit": ("Q - quit to the title screen", "Q - タイトルにもどる"),

    # Game over
    "over.points": ("points", "点"),
    "over.round": ("Round reached", "到達ラウンド"),
    "over.sequences": ("Sequences", "クリアした問題"),
    "over.longest": ("Longest", "最長"),
    "over.keys": ("{n} keys", "{n}キー"),
    "over.accuracy": ("Accuracy", "正確さ"),
    "over.practise": ("Key to practise: {key}  ({finger})", "練習したいキー: {key}（{finger}）"),
    "over.new_top": ("NEW TOP 10 SCORE!  Type your name:", "トップ10入り！ 名前を入力してね（英数字）:"),
    "over.save": ("Enter to save", "Enter で保存"),
    "over.again": ("Enter - play again", "Enter - もう一度"),
    "over.title": ("Esc - title screen", "Esc - タイトルへ"),
    "back": ("< Back", "< もどる"),

    # Top 10
    "top.heading": ("TOP 10", "トップ10"),
    "top.name": ("NAME", "名前"),
    "top.score": ("SCORE", "スコア"),
    "top.round": ("ROUND", "ラウンド"),
    "top.date": ("DATE", "日付"),
    "top.empty": ("No scores yet - be the first!", "まだ記録がありません。一番乗りしよう！"),
    "top.hint": ("Left / Right - difficulty    Esc - back", "← / → 難易度    Esc もどる"),

    # For Parents
    "parents.heading": ("FOR PARENTS", "保護者の方へ"),
    "parents.progress": ("Progress", "進み具合"),
    "parents.mistakes": ("What went wrong", "まちがえたところ"),
    "parents.hint": ("Left / Right - page    Del - reset statistics    Esc - back",
                     "← / → ページ    Del 記録を消す    Esc もどる"),
    "tile.total": ("Total time played", "合計プレイ時間"),
    "tile.today": ("Played today", "今日のプレイ時間"),
    "tile.games": ("Games played", "プレイ回数"),
    "tile.accuracy": ("Key accuracy", "キーの正確さ"),
    "tile.best_round": ("Best round reached", "最高ラウンド"),
    "tile.errors": ("Typing errors", "打ちまちがい"),
    "tile.timeouts": ("Too slow (time-outs)", "時間切れ"),
    "tile.failures": ("Sequence failures", "問題の失敗"),
    "tile.sequences": ("Sequences completed", "クリアした問題"),
    "tile.game_overs": ("Game overs", "ゲームオーバー"),
    "chart.minutes": ("Minutes played - last 7 days", "プレイ時間（分）- 過去7日間"),
    "chart.scores": ("Score - last 15 games", "スコア - 直近15ゲーム"),
    "chart.empty": ("Play a game to see progress here", "プレイすると進み具合がここに表示されます"),
    "parents.best": ("{label}: best {score} (round {round})", "{label}: 最高 {score}（ラウンド {round}）"),
    "parents.since": ("Playing since {date}", "{date} からプレイ"),
    "mist.keys": ("Keys missed most (all games)", "よくまちがえるキー（全ゲーム）"),
    "mist.mixups": ("Most common mix-ups", "よくある打ちまちがい"),
    "mist.no_mixups": ("No mix-ups yet", "打ちまちがいはまだありません"),
    "mist.pair": ("Wanted {want}   pressed {got}", "{want} のところで {got}"),
    "mist.recent": ("Recent games", "最近のゲーム"),
    "col.when": ("When", "日時"),
    "col.level": ("Level", "難易度"),
    "col.score": ("Score", "スコア"),
    "col.round": ("Round", "ラウンド"),
    "col.wrong": ("Wrong", "ミス"),
    "col.slow": ("Slow", "時間切れ"),
    "col.accuracy": ("Accuracy", "正確さ"),
    "mist.no_games": ("No games yet", "まだゲームがありません"),
    "mist.tip_key": ("Tip: {key} is missed most. It belongs to the {finger} finger - "
                     "a few slow games on Easy help build the habit.",
                     "ヒント: いちばんまちがえるのは {key}（{finger}）です。"
                     "「かんたん」でゆっくり練習すると身につきます。"),
    "mist.tip": ("Tip: short, regular sessions build memory and touch-typing best.",
                 "ヒント: 短い時間でも毎日続けると、記憶力とタッチタイピングが伸びます。"),
    "reset.question": ("Erase all statistics?", "すべての記録を消しますか？"),
    "reset.keys": ("Y - yes, erase      any other key - cancel", "Y - 消す      ほかのキー - キャンセル"),
    "reset.note": ("(The Top 10 tables are kept.)", "（トップ10の記録は残ります）"),

    # Credits
    "credits.heading": ("CREDITS", "クレジット"),
    "credits.released": ("Released {date}", "リリース日 {date}"),
    "credits.created": ("Created by", "制作"),
    "credits.made_with": ("Made with", "開発ツール"),
    "credits.website": ("Website", "ウェブサイト"),
    "credits.email": ("Email", "メール"),
    "credits.license": ("Licensed under the GNU General Public License v3.0",
                        "ライセンス: GNU General Public License v3.0"),
    "credits.notice1": ("This program is free software: you can redistribute it and/or modify it under the",
                        "このプログラムはフリーソフトウェアです。フリーソフトウェア財団が公開する"),
    "credits.notice2": ("terms of the GNU GPL as published by the Free Software Foundation, version 3 or later.",
                        "GNU GPL バージョン3（またはそれ以降）の条件のもとで再配布・改変できます。"),
    "credits.notice3": ("It comes with ABSOLUTELY NO WARRANTY. See the LICENSE file for details.",
                        "まったくの無保証です。詳しくは LICENSE ファイルをご覧ください。"),
    "credits.font": ("Font: M PLUS 1p (SIL Open Font License)   ·   All music and sound made in code",
                     "フォント: M PLUS 1p（SIL Open Font License）  ·  音楽と効果音はすべてプログラムで生成"),
    "credits.age": ("Recommended for ages 8+", "対象年齢 8歳以上"),
    "credits.hint": ("Click a link to open it    Esc - back", "リンクをクリックで開く    Esc もどる"),
}
