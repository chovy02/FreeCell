# solvers/A_star.py
"""
A* solver for FreeCell.
Uses same State/move_generator as BFS/DFS for full compatibility.
Heuristic is admissible and consistent.
"""

import time
import tracemalloc
import heapq
from core.move_generator import get_valid_moves, apply_move, auto_to_foundation
from core.rules import Rules

RV = Rules.RANK_VALUES


def _heuristic(state):
    """
    Admissible & consistent heuristic.
    
    h(n) = cards_not_on_foundation + penalties
    
    Admissible: each card not on foundation needs AT LEAST 1 move.
    Penalties only count extra moves that are definitely required:
      - A card buried under out-of-order cards needs those cards moved first.
    
    Consistent: h(n) <= cost(n,n') + h(n') because:
      - Each move costs 1
      - Each move moves at most 1 card to foundation (reducing h by at most 1)
      - Penalties can only decrease or stay same after a move
    """
    h = 0
    
    # Base: every card not on foundation needs at least 1 move
    cards_on_fnd = state.foundation_count()
    h = 52 - cards_on_fnd
    
    # Penalty: cards in free cells need at least 1 extra move each
    # (they must go somewhere before they can go to foundation)
    for c in state.free_cells:
        if c is not None:
            h += 1
    
    # Penalty: out-of-order pairs in cascades
    # If card[i] should go to foundation BEFORE card[i+1] but is below it,
    # card[i+1] must be moved out of the way first = at least 1 extra move
    for cas in state.cascades:
        for i in range(len(cas) - 1):
            below = cas[i]
            above = cas[i + 1]
            # Check if they form a valid descending alternating sequence
            if not (below.color != above.color and 
                    RV[below.rank] == RV[above.rank] + 1):
                # Out of order = at least 1 extra move needed
                h += 1
    
    return h


def solve_astar(initial_state, node_limit=500_000):
    """
    A* solver using same format as BFS/DFS.
    Returns same result dict.
    """
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
    
    # Priority queue: (f_score, counter, state_key)
    counter = 0
    open_set = []
    heapq.heappush(open_set, (_heuristic(root), 0, counter, root_key))
    
    # g_score[key] = cost from start
    g_score = {root_key: 0}
    
    # parent[key] = (parent_key, move)
    parent = {root_key: None}
    
    # key -> state mapping
    key_to_state = {root_key: root}
    
    closed = set()
    expanded = 0
    found_key = None

    while open_set:
        if expanded >= node_limit:
            break

        f, g, _, current_key = heapq.heappop(open_set)
        
        if current_key in closed:
            continue
        
        closed.add(current_key)
        
        if current_key not in key_to_state:
            continue
        current_state = key_to_state.pop(current_key)
        expanded += 1

        moves = get_valid_moves(current_state)

        for move in moves:
            new_state, _ = apply_move(current_state, move)
            new_key = new_state.get_key()
            
            if new_key in closed:
                continue

            new_g = g_score[current_key] + 1

            if new_g < g_score.get(new_key, float('inf')):
                g_score[new_key] = new_g
                parent[new_key] = (current_key, move)
                
                if new_state.is_goal():
                    found_key = new_key
                    break
                
                key_to_state[new_key] = new_state
                f_score = new_g + _heuristic(new_state)
                counter += 1
                heapq.heappush(open_set, (f_score, new_g, counter, new_key))

        if found_key:
            break

    elapsed = time.time() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if found_key:
        path = []
        k = found_key
        while parent[k] is not None:
            pk, m = parent[k]
            path.append(m)
            k = pk
        path.reverse()
        return {
            'solved': True,
            'moves': path,
            'expanded': expanded,
            'time': elapsed,
            'memory_mb': peak / 1024 / 1024,
            'solution_length': len(path)
        }

    return {
        'solved': False, 'moves': [], 'expanded': expanded,
        'time': elapsed, 'memory_mb': peak / 1024 / 1024,
        'solution_length': 0
    }