# solvers/UCS.py
import time
import tracemalloc
import heapq
from core.move_generator import get_valid_moves, apply_move, auto_to_foundation

def solve_ucs(initial_state, node_limit=2_000_000):
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
    
    pq = []
    counter = 0
    heapq.heappush(pq, (0, counter, root_key))
    
    parent = {root_key: (None, None, 0)}
    key_to_state = {root_key: root}
    
    explored = set()
    
    expanded = 0
    found_key = None

    while pq:
        if expanded >= node_limit:
            break

        current_cost, _, current_key = heapq.heappop(pq)
        
        if current_key in explored:
            continue
            
        explored.add(current_key)

        if current_key in key_to_state:
            current_state = key_to_state.pop(current_key)
        else:
            continue

        expanded += 1

        if current_state.is_goal():
            found_key = current_key
            break

        moves = get_valid_moves(current_state)

        for move in moves:
            new_state, _ = apply_move(current_state, move)
            new_key = new_state.get_key()
            
            # Chi phí di chuyển trong Freecell luôn là 1
            new_cost = current_cost + 1

            if new_key not in explored:
                if new_key not in parent or new_cost < parent[new_key][2]:
                    parent[new_key] = (current_key, move, new_cost)
                    key_to_state[new_key] = new_state
                    counter += 1
                    heapq.heappush(pq, (new_cost, counter, new_key))

    elapsed = time.time() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if found_key:
        moves_path = []
        k = found_key
        while parent[k][0] is not None:
            pk, m, _ = parent[k]
            moves_path.append(m)
            k = pk
        moves_path.reverse()
        return {
            'solved': True,
            'moves': moves_path,
            'expanded': expanded,
            'time': elapsed,
            'memory_mb': peak / 1024 / 1024,
            'solution_length': len(moves_path)
        }

    return {
        'solved': False, 'moves': [], 'expanded': expanded,
        'time': elapsed, 'memory_mb': peak / 1024 / 1024,
        'solution_length': 0
    }