"""Tkinter-based maze game with optional shortest-path guidance.

The player uses the arrow keys (or WASD) to move from the entrance (top-left)
to the exit (bottom-right). The maze is generated randomly each time and can
be reset. An optional green guide line shows the current shortest route.
"""

from __future__ import annotations

import random
import tkinter as tk
from collections import deque
from dataclasses import dataclass, field
from tkinter import messagebox
from typing import Deque, Dict, List, Tuple


DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


@dataclass
class Cell:
    x: int
    y: int
    walls: Dict[str, bool] = field(
        default_factory=lambda: {"N": True, "S": True, "E": True, "W": True}
    )


class Maze:
    def __init__(self, width: int, height: int) -> None:
        if width < 2 or height < 2:
            raise ValueError("Maze dimensions must be at least 2x2.")
        self.width = width
        self.height = height
        self.grid: List[List[Cell]] = [
            [Cell(x, y) for x in range(width)] for y in range(height)
        ]
        self._generate()

    def _generate(self) -> None:
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]
        stack: List[Tuple[int, int]] = []
        current_x, current_y = 0, 0
        visited[current_y][current_x] = True
        visited_cells = 1
        total_cells = self.width * self.height

        while visited_cells < total_cells:
            neighbors = []
            for direction, (dx, dy) in DIRECTIONS.items():
                nx, ny = current_x + dx, current_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not visited[ny][nx]:
                        neighbors.append((direction, nx, ny))

            if neighbors:
                direction, next_x, next_y = random.choice(neighbors)
                current_cell = self.grid[current_y][current_x]
                next_cell = self.grid[next_y][next_x]
                current_cell.walls[direction] = False
                next_cell.walls[OPPOSITE[direction]] = False
                stack.append((current_x, current_y))
                current_x, current_y = next_x, next_y
                visited[current_y][current_x] = True
                visited_cells += 1
            elif stack:
                current_x, current_y = stack.pop()

    def has_wall(self, x: int, y: int, direction: str) -> bool:
        return self.grid[y][x].walls[direction]


class MazeGame:
    def __init__(self, width: int = 15, height: int = 15, cell_size: int = 32) -> None:
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.padding = 20

        self.root = tk.Tk()
        self.root.title("迷宫小冒险")
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
            buttons, text="显示路径", command=self.toggle_path
        )
        self.toggle_path_btn.pack(side=tk.LEFT, padx=4)
        tk.Button(buttons, text="Reset Maze", command=self.reset_game).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(buttons, text="Quit", command=self.root.destroy).pack(
            side=tk.LEFT, padx=4
        )

        self.status = tk.StringVar(value="Use the arrow keys to reach the green goal.")
        tk.Label(self.root, textvariable=self.status).pack(pady=(0, 12))

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
        self.toggle_path_btn.config(text="隐藏路径" if self.show_path else "显示路径")
        if self.show_path:
            self.status.set("路径提示已开启。")
        else:
            self.status.set("路径提示已关闭。")
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
            self.status.set("Bumped into a wall!")
            return

        dx, dy = DIRECTIONS[direction]
        nx, ny = x + dx, y + dy
        if not (0 <= nx < self.width and 0 <= ny < self.height):
            return

        self.player_pos = (nx, ny)
        self.place_player()
        self.status.set("Keep going!")
        self.update_path_display()

        if self.player_pos == self.goal_pos:
            self.status.set("You escaped! Press Reset for another maze.")
            messagebox.showinfo("Maze", "恭喜通关！")

    def reset_game(self) -> None:
        self.maze = Maze(self.width, self.height)
        self.player_pos = (0, 0)
        self.goal_pos = (self.width - 1, self.height - 1)
        self.draw_maze()
        self.place_goal()
        self.place_player()
        self.status.set("New maze! Reach the green goal.")
        self.update_path_display()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    MazeGame().run()
