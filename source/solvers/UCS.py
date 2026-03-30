# solvers/UCS.py
import time
import tracemalloc
import heapq
from core.move_generator import get_valid_moves, apply_move, auto_to_foundation, is_safe_auto

from utils.results import SolverResult

def _move_cost(current_state, new_state):
    """
    - Cost = 0.1: Nước đi auto-safe lên Foundation.
    - Cost = 1.0: Nước đi lên Foundation nhưng không an toàn, hoặc các nước đi thông thường.
    """
    if new_state.foundation_count() > current_state.foundation_count():
        # Tìm xem cọc foundation nào vừa được thêm bài
        for suit in ['hearts', 'diamonds', 'clubs', 'spades']:
            if len(new_state.foundations[suit]) > len(current_state.foundations[suit]):
                card_moved = new_state.foundations[suit][-1]
                
                # Truyền lại vào hàm is_safe_auto để check độ an toàn
                if is_safe_auto(current_state, card_moved):
                    return 0.1
                else:
                    return 1.0
                    
    return 1.0


def solve_ucs(initial_state, node_limit=2_000_000):
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

    root_key = root.get_key()
    
    pq = []
    counter = 0
    heapq.heappush(pq, (0.0, counter, root_key)) # Khởi tạo cost dạng float (0.0)
    
    # parent lưu: (parent_key, move_from_parent, cost_to_reach_this_node)
    parent = {root_key: (None, None, 0.0)}
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
            
            # Tính toán Cost động thay vì fix cứng là 1
            cost = _move_cost(current_state, new_state)
            new_cost = current_cost + cost

            if new_key not in explored:
                # Cập nhật nếu tìm thấy đường đi rẻ hơn đến node này
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
        return SolverResult(
            solved = True,
            moves = moves_path,
            expanded = expanded,
            time = elapsed,
            memory_mb = peak / 1024 / 1024
        )

    return SolverResult(
        solved = False, moves = [], expanded = expanded,
        time = elapsed, memory_mb = peak / 1024 / 1024
    )