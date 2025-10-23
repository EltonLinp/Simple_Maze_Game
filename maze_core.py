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
    SUPPORTED_ALGORITHMS = ("dfs", "prim", "kruskal")

    def __init__(
        self,
        width: int,
        height: int,
        algorithm: str = "dfs",
        braid_factor: float = 0.0,
        dead_end_bias: float = 0.0,
    ) -> None:
        if width < 2 or height < 2:
            raise ValueError("Maze dimensions must be at least 2x2.")
        self.width = width
        self.height = height
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            algorithm = "dfs"
        self.algorithm = algorithm
        self.braid_factor = min(max(braid_factor, 0.0), 1.0)
        self.dead_end_bias = min(max(dead_end_bias, -1.0), 1.0)
        self.grid: List[List[Cell]] = []
        self.dead_end_ratio: float = 0.0
        self._build_maze()

    def _build_maze(self) -> None:
        attempts = 1
        if self.dead_end_bias > 0:
            attempts = min(10, 3 + int(self.dead_end_bias * 10))
        elif self.dead_end_bias < 0:
            attempts = min(10, 3 + int(-self.dead_end_bias * 10))

        best_grid: List[List[Cell]] | None = None
        best_ratio: float | None = None

        for _ in range(attempts):
            self.grid = [
                [Cell(x, y) for x in range(self.width)] for y in range(self.height)
            ]
            self._generate()
            ratio = self._dead_end_ratio(self.grid)
            if self.dead_end_bias > 0:
                if best_ratio is None or ratio > best_ratio:
                    best_grid = self._clone_grid(self.grid)
                    best_ratio = ratio
            elif self.dead_end_bias < 0:
                if best_ratio is None or ratio < best_ratio:
                    best_grid = self._clone_grid(self.grid)
                    best_ratio = ratio
            else:
                best_grid = self._clone_grid(self.grid)
                best_ratio = ratio
                break

        if best_grid is None:
            best_grid = self._clone_grid(self.grid)
            best_ratio = self._dead_end_ratio(best_grid)

        self.grid = best_grid
        if self.braid_factor > 0:
            self._apply_braid(self.grid, self.braid_factor)
            best_ratio = self._dead_end_ratio(self.grid)
        self.dead_end_ratio = best_ratio

    def _generate(self) -> None:
        generators = {
            "dfs": self._generate_dfs,
            "prim": self._generate_prim,
            "kruskal": self._generate_kruskal,
        }
        generators.get(self.algorithm, self._generate_dfs)()

    def _generate_dfs(self) -> None:
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

    def _generate_prim(self) -> None:
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]
        frontier: List[Tuple[int, int, str, int, int]] = []

        def add_frontier(x: int, y: int) -> None:
            for direction, (dx, dy) in DIRECTIONS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not visited[ny][nx]:
                        frontier.append((x, y, direction, nx, ny))

        visited[0][0] = True
        add_frontier(0, 0)

        while frontier:
            index = random.randrange(len(frontier))
            x, y, direction, nx, ny = frontier.pop(index)
            if visited[ny][nx]:
                continue
            current_cell = self.grid[y][x]
            next_cell = self.grid[ny][nx]
            current_cell.walls[direction] = False
            next_cell.walls[OPPOSITE[direction]] = False
            visited[ny][nx] = True
            add_frontier(nx, ny)

    def _generate_kruskal(self) -> None:
        parent = [i for i in range(self.width * self.height)]
        rank = [0 for _ in parent]

        def find(idx: int) -> int:
            while parent[idx] != idx:
                parent[idx] = parent[parent[idx]]
                idx = parent[idx]
            return idx

        def union(a: int, b: int) -> bool:
            root_a = find(a)
            root_b = find(b)
            if root_a == root_b:
                return False
            if rank[root_a] < rank[root_b]:
                parent[root_a] = root_b
            elif rank[root_a] > rank[root_b]:
                parent[root_b] = root_a
            else:
                parent[root_b] = root_a
                rank[root_a] += 1
            return True

        edges: List[Tuple[int, int, str]] = []
        for y in range(self.height):
            for x in range(self.width):
                cell_index = y * self.width + x
                for direction in ("E", "S"):
                    dx, dy = DIRECTIONS[direction]
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        neighbor_index = ny * self.width + nx
                        edges.append((cell_index, neighbor_index, direction))

        random.shuffle(edges)

        for cell_index, neighbor_index, direction in edges:
            if union(cell_index, neighbor_index):
                y, x = divmod(cell_index, self.width)
                ny, nx = divmod(neighbor_index, self.width)
                current_cell = self.grid[y][x]
                next_cell = self.grid[ny][nx]
                current_cell.walls[direction] = False
                next_cell.walls[OPPOSITE[direction]] = False

    def _clone_grid(self, grid: List[List[Cell]]) -> List[List[Cell]]:
        return [
            [Cell(cell.x, cell.y, dict(cell.walls)) for cell in row]
            for row in grid
        ]

    def _dead_end_ratio(self, grid: List[List[Cell]]) -> float:
        dead_ends = 0
        for row in grid:
            for cell in row:
                openings = sum(1 for wall_open in cell.walls.values() if not wall_open)
                if openings == 1:
                    dead_ends += 1
        return dead_ends / float(self.width * self.height)

    def _apply_braid(self, grid: List[List[Cell]], braid_factor: float) -> None:
        cells: List[Tuple[int, int]] = []
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                openings = sum(1 for wall_open in cell.walls.values() if not wall_open)
                if openings == 1:
                    cells.append((x, y))
        random.shuffle(cells)
        for x, y in cells:
            if random.random() > braid_factor:
                continue
            cell = grid[y][x]
            candidates: List[Tuple[str, Cell]] = []
            for direction, (dx, dy) in DIRECTIONS.items():
                if not cell.walls[direction]:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbor = grid[ny][nx]
                    if neighbor.walls[OPPOSITE[direction]]:
                        candidates.append((direction, neighbor))
            if not candidates:
                continue
            direction, neighbor = random.choice(candidates)
            cell.walls[direction] = False
            neighbor.walls[OPPOSITE[direction]] = False

    def has_wall(self, x: int, y: int, direction: str) -> bool:
        return self.grid[y][x].walls[direction]


__all__ = ["DIRECTIONS", "Maze"]
