"""Tkinter-based maze game with optional shortest-path guidance.

The player uses the arrow keys (or WASD) to move from the entrance (top-left)
to the exit (bottom-right). The maze is generated randomly each time and can
be reset. An optional green guide line shows the current shortest route.
"""

from __future__ import annotations

import tkinter as tk
from collections import deque
from tkinter import messagebox
from typing import Any, Deque, Dict, List, Tuple

from localization import DEFAULT_DIFFICULTY, DIFFICULTY_SETTINGS, translate_text
from maze_core import DIRECTIONS, Maze

class MazeGame:
    def __init__(self, width: int = 15, height: int = 15, cell_size: int = 32) -> None:
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.padding = 20
        self.lang = "zh"
        self.current_status_key: Tuple[str, Dict[str, Any]] = ("status_start", {})
        if (self.width, self.height) not in DIFFICULTY_SETTINGS.values():
            self.width, self.height = DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]
        initial_difficulty = next(
            (
                name
                for name, dims in DIFFICULTY_SETTINGS.items()
                if dims == (self.width, self.height)
            ),
            DEFAULT_DIFFICULTY,
        )

        self.root = tk.Tk()
        self.root.title(self.translate("window_title"))
        self.root.resizable(False, False)

        canvas_width = self.padding * 2 + self.width * self.cell_size
        canvas_height = self.padding * 2 + self.height * self.cell_size

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="#fdfcf8",
            highlightthickness=0,
        )
        self.canvas.pack(padx=16, pady=(16, 4))

        buttons = tk.Frame(self.root)
        buttons.pack(pady=(0, 16))
        self.toggle_path_btn = tk.Button(
            buttons, text=self.translate("toggle_path_show"), command=self.toggle_path
        )
        self.toggle_path_btn.pack(side=tk.LEFT, padx=4)
        self.reset_btn = tk.Button(
            buttons, text=self.translate("btn_reset"), command=self.reset_game
        )
        self.reset_btn.pack(side=tk.LEFT, padx=4)
        self.quit_btn = tk.Button(
            buttons, text=self.translate("btn_quit"), command=self.root.destroy
        )
        self.quit_btn.pack(side=tk.LEFT, padx=4)
        self.toggle_lang_btn = tk.Button(
            buttons,
            text=self.translate("switch_to_english"),
            command=self.toggle_language,
        )
        self.toggle_lang_btn.pack(side=tk.LEFT, padx=4)

        difficulty_frame = tk.Frame(self.root)
        difficulty_frame.pack(pady=(0, 12))
        self.difficulty_label = tk.Label(
            difficulty_frame, text=self.translate("difficulty_label")
        )
        self.difficulty_label.pack(side=tk.LEFT, padx=(0, 8))
        self.difficulty_var = tk.StringVar(value=initial_difficulty)
        self.difficulty_buttons: Dict[str, tk.Radiobutton] = {}
        for key in DIFFICULTY_SETTINGS:
            button = tk.Radiobutton(
                difficulty_frame,
                text=self.translate(f"difficulty_{key}"),
                value=key,
                variable=self.difficulty_var,
                command=lambda choice=key: self.change_difficulty(choice),
            )
            button.pack(side=tk.LEFT, padx=4)
            self.difficulty_buttons[key] = button
        self.difficulty_buttons[self.difficulty_var.get()].select()

        self.status = tk.StringVar()
        self.step_var = tk.StringVar()
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=(0, 12), padx=16, fill=tk.X)
        self.status_label = tk.Label(info_frame, textvariable=self.status, anchor="w")
        self.status_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.step_label = tk.Label(info_frame, textvariable=self.step_var, anchor="e")
        self.step_label.pack(side=tk.RIGHT)
        self.set_status("status_start")
        self.step_count = 0
        self.update_step_label()

        self.maze = Maze(self.width, self.height)
        self.player_pos = (0, 0)
        self.goal_pos = (self.width - 1, self.height - 1)
        self.player_item: int | None = None
        self.goal_item: int | None = None
        self.path_item: int | None = None
        self.show_path = False

        self.draw_maze()
        self.place_player()
        self.place_goal()
        self.update_path_display()

        self.root.bind("<Up>", lambda e: self.handle_move("N"))
        self.root.bind("<Down>", lambda e: self.handle_move("S"))
        self.root.bind("<Left>", lambda e: self.handle_move("W"))
        self.root.bind("<Right>", lambda e: self.handle_move("E"))
        # Support WASD as well
        self.root.bind("w", lambda e: self.handle_move("N"))
        self.root.bind("s", lambda e: self.handle_move("S"))
        self.root.bind("a", lambda e: self.handle_move("W"))
        self.root.bind("d", lambda e: self.handle_move("E"))

    def translate(self, key: str, **kwargs: Any) -> str:
        return translate_text(self.lang, key, **kwargs)

    def set_status(self, key: str, **kwargs: Any) -> None:
        self.current_status_key = (key, dict(kwargs))
        self.status.set(self.translate(key, **kwargs))

    def update_step_label(self) -> None:
        self.step_var.set(self.translate("steps_label", count=self.step_count))

    def refresh_texts(self) -> None:
        self.root.title(self.translate("window_title"))
        toggle_key = "toggle_path_hide" if self.show_path else "toggle_path_show"
        self.toggle_path_btn.config(text=self.translate(toggle_key))
        lang_key = "switch_to_chinese" if self.lang == "en" else "switch_to_english"
        self.toggle_lang_btn.config(text=self.translate(lang_key))
        self.reset_btn.config(text=self.translate("btn_reset"))
        self.quit_btn.config(text=self.translate("btn_quit"))
        self.difficulty_label.config(text=self.translate("difficulty_label"))
        for key, button in self.difficulty_buttons.items():
            button.config(text=self.translate(f"difficulty_{key}"))
        self.update_step_label()
        status_key, params = self.current_status_key
        self.status.set(self.translate(status_key, **params))

    def toggle_language(self) -> None:
        self.lang = "en" if self.lang == "zh" else "zh"
        self.refresh_texts()

    def update_canvas_size(self) -> None:
        canvas_width = self.padding * 2 + self.width * self.cell_size
        canvas_height = self.padding * 2 + self.height * self.cell_size
        self.canvas.config(width=canvas_width, height=canvas_height)
        self.root.geometry("")

    def change_difficulty(self, choice: str | None = None) -> None:
        selected = choice or self.difficulty_var.get()
        if selected not in DIFFICULTY_SETTINGS:
            return
        self.difficulty_var.set(selected)
        button = self.difficulty_buttons.get(selected)
        if button is not None:
            button.select()
        new_width, new_height = DIFFICULTY_SETTINGS[selected]
        if (self.width, self.height) == (new_width, new_height):
            return
        self.width, self.height = new_width, new_height
        self.reset_game()

    def draw_maze(self) -> None:
        self.canvas.delete("maze")
        for y, row in enumerate(self.maze.grid):
            for x, cell in enumerate(row):
                x1 = self.padding + x * self.cell_size
                y1 = self.padding + y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                if cell.walls["N"]:
                    self.canvas.create_line(x1, y1, x2, y1, fill="#444", width=2, tags="maze")
                if cell.walls["S"]:
                    self.canvas.create_line(x1, y2, x2, y2, fill="#444", width=2, tags="maze")
                if cell.walls["E"]:
                    self.canvas.create_line(x2, y1, x2, y2, fill="#444", width=2, tags="maze")
                if cell.walls["W"]:
                    self.canvas.create_line(x1, y1, x1, y2, fill="#444", width=2, tags="maze")

    def place_player(self) -> None:
        if self.player_item is not None:
            self.canvas.delete(self.player_item)
        x, y = self.player_pos
        x1 = self.padding + x * self.cell_size + 6
        y1 = self.padding + y * self.cell_size + 6
        x2 = x1 + self.cell_size - 12
        y2 = y1 + self.cell_size - 12
        self.player_item = self.canvas.create_oval(
            x1, y1, x2, y2, fill="#2979ff", outline="#15426a", width=2, tags="player"
        )

    def place_goal(self) -> None:
        if self.goal_item is not None:
            self.canvas.delete(self.goal_item)
        x, y = self.goal_pos
        x1 = self.padding + x * self.cell_size + 8
        y1 = self.padding + y * self.cell_size + 8
        x2 = x1 + self.cell_size - 16
        y2 = y1 + self.cell_size - 16
        self.goal_item = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill="#2ecc71", outline="#1B5E20", width=2, tags="goal"
        )

    def toggle_path(self) -> None:
        self.show_path = not self.show_path
        label_key = "toggle_path_hide" if self.show_path else "toggle_path_show"
        self.toggle_path_btn.config(text=self.translate(label_key))
        status_key = "status_path_on" if self.show_path else "status_path_off"
        self.set_status(status_key)
        self.update_path_display()

    def compute_shortest_path(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        if start == goal:
            return [start]
        queue: Deque[Tuple[int, int]] = deque([start])
        parents: Dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}

        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                break
            for direction, (dx, dy) in DIRECTIONS.items():
                if self.maze.has_wall(x, y, direction):
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in parents:
                        parents[(nx, ny)] = (x, y)
                        queue.append((nx, ny))
        else:
            return []

        path: List[Tuple[int, int]] = []
        node: Tuple[int, int] | None = goal
        while node is not None:
            path.append(node)
            node = parents.get(node)

        path.reverse()
        return path

    def update_path_display(self) -> None:
        if self.path_item is not None:
            self.canvas.delete(self.path_item)
            self.path_item = None

        if not self.show_path or self.player_pos == self.goal_pos:
            return

        path = self.compute_shortest_path(self.player_pos, self.goal_pos)
        if len(path) < 2:
            return

        coords: List[float] = []
        for x, y in path:
            cx = self.padding + x * self.cell_size + self.cell_size / 2
            cy = self.padding + y * self.cell_size + self.cell_size / 2
            coords.extend([cx, cy])

        self.path_item = self.canvas.create_line(
            *coords,
            fill="#2ecc71",
            width=4,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            tags="path",
        )

    def handle_move(self, direction: str) -> None:
        if self.player_pos == self.goal_pos:
            return

        x, y = self.player_pos
        if self.maze.has_wall(x, y, direction):
            self.set_status("status_wall")
            return

        dx, dy = DIRECTIONS[direction]
        nx, ny = x + dx, y + dy
        if not (0 <= nx < self.width and 0 <= ny < self.height):
            return

        self.player_pos = (nx, ny)
        self.step_count += 1
        self.update_step_label()
        self.place_player()
        self.set_status("status_move")
        self.update_path_display()

        if self.player_pos == self.goal_pos:
            self.set_status("status_win")
            messagebox.showinfo(
                self.translate("win_title"), self.translate("win_message")
            )

    def reset_game(self) -> None:
        self.update_canvas_size()
        self.maze = Maze(self.width, self.height)
        self.player_pos = (0, 0)
        self.goal_pos = (self.width - 1, self.height - 1)
        self.step_count = 0
        self.update_step_label()
        self.draw_maze()
        self.place_goal()
        self.place_player()
        self.set_status("status_new_maze")
        self.update_path_display()

    def run(self) -> None:
        self.root.mainloop()
