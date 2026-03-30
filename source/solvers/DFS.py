# solvers/DFS.py
import time
import tracemalloc
from core.move_generator import get_valid_moves, apply_move, auto_to_foundation

from utils.results import SolverResult


def solve_dfs(initial_state, depth_limit=300, node_limit=2_000_000):
    tracemalloc.start()
    start_time = time.time()

    root = initial_state.clone()
    auto_to_foundation(root)

    if root.is_goal():
        elapsed = time.time() - start_time
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return SolverResult(
            solved = True, moves = [], expanded = 0,
            time = elapsed, memory_mb = peak / 1024 / 1024
        )

    # Stack: (state, path, depth)
    stack = [(root, [], 0)]
    visited = {root.get_key()}
    expanded = 0

    while stack:
        if expanded >= node_limit:
            break

        state, path, depth = stack.pop()
        expanded += 1

        if depth >= depth_limit:
            continue

        # Generate all valid moves, no scoring, no reordering
        moves = get_valid_moves(state)

        for move in moves:
            new_state, _ = apply_move(state, move)
            key = new_state.get_key()

            if key in visited:
                continue
            visited.add(key)

            new_path = path + [move]

            if new_state.is_goal():
                elapsed = time.time() - start_time
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return SolverResult(
                    solved = True,
                    moves = new_path,
                    expanded = expanded,
                    time = elapsed,
                    memory_mb = peak / 1024 / 1024
                )

            stack.append((new_state, new_path, depth + 1))

    elapsed = time.time() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return SolverResult(
        solved = False, moves = [], expanded = expanded,
        time = elapsed, memory_mb = peak / 1024 / 1024
    )