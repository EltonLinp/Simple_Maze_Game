"""Core maze generation data structures and helpers."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


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


__all__ = ["DIRECTIONS", "Maze"]
