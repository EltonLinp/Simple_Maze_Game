"""Localization data and helpers for the maze game."""

from __future__ import annotations

from typing import Any, Dict, Tuple


LANG_STRINGS: Dict[str, Dict[str, str]] = {
    "zh": {
        "window_title": "迷宫小冒险",
        "toggle_path_show": "显示路径",
        "toggle_path_hide": "隐藏路径",
        "switch_to_english": "切换到英文",
        "switch_to_chinese": "切换到中文",
        "btn_reset": "重置迷宫",
        "btn_quit": "退出",
        "status_start": "使用方向键或WASD找到绿色出口！",
        "status_path_on": "路径提示已开启。",
        "status_path_off": "路径提示已关闭。",
        "status_wall": "撞到墙啦！",
        "status_move": "继续前进！",
        "status_win": "你逃出迷宫啦！点击重置再来一局。",
        "status_new_maze": "新的迷宫生成了，快找到出口！",
        "win_title": "迷宫",
        "win_message": "恭喜通关！",
        "difficulty_label": "难度：",
        "difficulty_easy": "简单",
        "difficulty_medium": "普通",
        "difficulty_hard": "困难",
        "steps_label": "步数：{count}",
    },
    "en": {
        "window_title": "Maze Escape",
        "toggle_path_show": "Show Path",
        "toggle_path_hide": "Hide Path",
        "switch_to_english": "Switch to English",
        "switch_to_chinese": "Switch to Chinese",
        "btn_reset": "Reset Maze",
        "btn_quit": "Quit",
        "status_start": "Use the arrow keys or WASD to reach the green goal.",
        "status_path_on": "Path hints enabled.",
        "status_path_off": "Path hints disabled.",
        "status_wall": "Bumped into a wall!",
        "status_move": "Keep going!",
        "status_win": "You escaped! Press Reset for another maze.",
        "status_new_maze": "New maze! Reach the green goal.",
        "win_title": "Maze",
        "win_message": "Congratulations, you escaped!",
        "difficulty_label": "Difficulty:",
        "difficulty_easy": "Easy",
        "difficulty_medium": "Normal",
        "difficulty_hard": "Hard",
        "steps_label": "Steps: {count}",
    },
}

DEFAULT_DIFFICULTY = "medium"
DIFFICULTY_SETTINGS: Dict[str, Tuple[int, int]] = {
    "easy": (10, 10),
    "medium": (15, 15),
    "hard": (20, 20),
}


def translate_text(lang: str, key: str, **kwargs: Any) -> str:
    """Return the translated string for the given key and language."""
    table = LANG_STRINGS.get(lang, LANG_STRINGS["en"])
    template = table.get(key) or LANG_STRINGS["en"].get(key) or key
    return template.format(**kwargs)


__all__ = [
    "DEFAULT_DIFFICULTY",
    "DIFFICULTY_SETTINGS",
    "LANG_STRINGS",
    "translate_text",
]
