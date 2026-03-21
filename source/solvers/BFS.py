# solvers/BFS.py
import time
import tracemalloc
from collections import deque
from core.move_generator import get_valid_moves, apply_move, auto_to_foundation


def solve_bfs(initial_state, node_limit=2_000_000):
    tracemalloc.start()
    start_time = time.time()

    root = initial_state.clone()
    auto_to_foundation(root)

    if root.is_goal():
        elapsed = time.time() - start_time
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            'solved': True, 'moves': [], 'expanded': 0,
            'time': elapsed, 'memory_mb': peak / 1024 / 1024,
            'solution_length': 0
        }

    root_key = root.get_key()
    # Parent pointer for path reconstruction (saves memory vs storing full path)
    parent = {root_key: None}
    key_to_state = {root_key: root}

    queue = deque()
    queue.append(root_key)
    expanded = 0
    found_key = None

    while queue:
        if expanded >= node_limit:
            break

        current_key = queue.popleft()
        current_state = key_to_state.pop(current_key)
        expanded += 1

        # Generate all valid moves, no filtering, no ordering
        moves = get_valid_moves(current_state)

        for move in moves:
            new_state, _ = apply_move(current_state, move)
            new_key = new_state.get_key()

            if new_key in parent:
                continue
            parent[new_key] = (current_key, move)

            if new_state.is_goal():
                found_key = new_key
                break

            key_to_state[new_key] = new_state
            queue.append(new_key)

        if found_key:
            break

    elapsed = time.time() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if found_key:
        moves = []
        k = found_key
        while parent[k] is not None:
            pk, m = parent[k]
            moves.append(m)
            k = pk
        moves.reverse()
        return {
            'solved': True,
            'moves': moves,
            'expanded': expanded,
            'time': elapsed,
            'memory_mb': peak / 1024 / 1024,
            'solution_length': len(moves)
        }

    return {
        'solved': False, 'moves': [], 'expanded': expanded,
        'time': elapsed, 'memory_mb': peak / 1024 / 1024,
        'solution_length': 0
    }