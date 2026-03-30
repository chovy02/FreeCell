# solvers/A_star.py
"""
A* solver for FreeCell.
Uses separated cost and heuristic functions.
Implements 'Covering Next Foundation Cards' heuristic compatible with core/state.py.
"""

import time
import tracemalloc
import heapq
from core.move_generator import get_valid_moves, apply_move, auto_to_foundation, is_safe_auto
from core.rules import Rules

from utils.results import SolverResult

RV = Rules.RANK_VALUES

def _move_cost(current_state, new_state):
    """
    - Cost = 0.5: Nước đi auto-safe lên Foundation (tận dụng is_safe_auto từ move_generator).
    - Cost = 1.0: Nước đi lên Foundation nhưng không an toàn, hoặc các nước đi thông thường.
    """
    if new_state.foundation_count() > current_state.foundation_count():
        # Tìm xem cọc foundation nào vừa được thêm bài
        for suit in ['hearts', 'diamonds', 'clubs', 'spades']:
            if len(new_state.foundations[suit]) > len(current_state.foundations[suit]):
                # Lấy trực tiếp object Card vừa được đưa lên đích
                card_moved = new_state.foundations[suit][-1]
                
                # Truyền lại vào hàm is_safe_auto để check độ an toàn
                if is_safe_auto(current_state, card_moved):
                    return 0.5
                else:
                    return 1.0
                    
    return 1.0

def _heuristic(state):
    """
    Heuristic: Covering Next Foundation Cards
    Dựa trực tiếp vào state.foundations để xác định mục tiêu cấp bách.
    """
    cards_on_fnd = state.foundation_count()
    base_h = 0.5 * (52 - cards_on_fnd)
    
    covering_cards = set()
    
    # Duyệt qua 4 chất dựa theo định nghĩa trong State
    for suit in ['hearts', 'diamonds', 'clubs', 'spades']:
        # Chiều dài mảng foundation + 1 chính là Rank Value của lá bài tiếp theo cần tìm
        # Ví dụ: list rỗng (len=0) -> cần Át (RV=1)
        next_needed_val = len(state.foundations[suit]) + 1
        
        if next_needed_val > 13:
            continue # Chất này đã hoàn thành xong
            
        # Truy tìm vị trí của lá bài mục tiêu này trong các cột Cascades
        found = False
        for cas in state.cascades:
            for pos, card in enumerate(cas):
                if card.suit == suit and RV[card.rank] == next_needed_val:
                    # Đã tìm thấy! Thêm TẤT CẢ các lá bài nằm đè lên nó vào danh sách phạt
                    for i in range(pos + 1, len(cas)):
                        covering_cards.add(cas[i])
                    found = True
                    break # Dừng tìm kiếm trong cột này
            if found:
                break # Dừng tìm kiếm trong các cột khác (vì mỗi lá bài là duy nhất)

    # Mỗi lá bài ngáng đường bắt buộc phải tốn 1 nước đi (cost = 1.0) để dọn dẹp
    penalty_h = 1.0 * len(covering_cards)
    
    return base_h + penalty_h

def solve_astar(initial_state, node_limit=500_000):
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
    
    counter = 0
    open_set = []
    heapq.heappush(open_set, (_heuristic(root), 0.0, counter, root_key))
    
    g_score = {root_key: 0.0}
    parent = {root_key: None}
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

            cost = _move_cost(current_state, new_state)
            new_g = g_score[current_key] + cost

            if new_g < g_score.get(new_key, float('inf')):
                g_score[new_key] = new_g
                parent[new_key] = (current_key, move)
                
                if new_state.is_goal():
                    found_key = new_key
                    break
                
                key_to_state[new_key] = new_state
                f_score = new_g +  _heuristic(new_state)
                
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
        return SolverResult(
            solved = True,
            moves = path,
            expanded = expanded,
            time = elapsed,
            memory_mb = peak / 1024 / 1024
        )

    return SolverResult(
        solved = False, moves = [], expanded = expanded,
        time = elapsed, memory_mb = peak / 1024 / 1024
    )