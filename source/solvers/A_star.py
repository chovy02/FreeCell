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

def _move_cost(auto_moves_count):
                    
    return 1.0 + (0.5 * auto_moves_count)

def _heuristic(state):
    """
    Heuristic: Đếm số lượng chuỗi bài hợp lệ đè lên các lá mục tiêu.
    Đã tối ưu (Cách 2): Truy xuất trực tiếp thuộc tính color và RANK_VALUES,
    KHÔNG tạo list trung gian để tối đa hóa tốc độ duyệt của A*.
    """
    cards_on_fnd = state.foundation_count()
    base_h = 0.5 * (52 - cards_on_fnd)
    
    # 1. Thu thập tất cả các lá bài mục tiêu đang cần tìm
    target_cards = []
    for suit in ['hearts', 'diamonds', 'clubs', 'spades']:
        next_needed_val = len(state.foundations[suit]) + 1
        if next_needed_val <= 13:
            target_cards.append((suit, next_needed_val))

    total_sequences = 0
    
    # 2. Duyệt từng cột để đếm số chuỗi ngáng đường
    for cas in state.cascades:
        deepest_target_pos = -1
        
        # Tìm lá mục tiêu bị chôn sâu nhất trong cột này
        for pos, card in enumerate(cas):
            if any(card.suit == t_suit and Rules.RANK_VALUES[card.rank] == t_val for t_suit, t_val in target_cards):
                deepest_target_pos = pos
                break 
        
        if deepest_target_pos != -1:
            covering_len = len(cas) - 1 - deepest_target_pos
            if covering_len > 0:
                # Có bài đè lên -> Khởi điểm là có 1 chuỗi ngáng đường
                seq_count = 1 
                
                # Quét từ dưới lên trên để tìm các "điểm đứt gãy"
                for i in range(deepest_target_pos + 1, len(cas) - 1):
                    parent_card = cas[i]
                    child_card = cas[i+1]
                    
                    # --- CÁCH 2: TỐI ƯU HIỆU NĂNG ---
                    # Dùng thẳng property .color và dictionary RANK_VALUES 
                    # để so sánh trực tiếp, bỏ qua việc gọi hàm Rules.is_valid_sequence
                    diff_color = parent_card.color != child_card.color
                    right_rank = Rules.RANK_VALUES[child_card.rank] == Rules.RANK_VALUES[parent_card.rank] - 1
                    
                    if not (diff_color and right_rank):
                        # Bị đứt gãy (sai màu hoặc sai thứ tự) -> tính là 1 chuỗi mới
                        seq_count += 1
                        
                total_sequences += seq_count

    penalty_h = 0.5 * total_sequences
    
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
    root_h = _heuristic(root)
    heapq.heappush(open_set, (root_h, 0.0, counter, root_key))
    
    g_score = {root_key: 0.0}
    parent = {root_key: (None, None, 0.0, root_h)} #(parent_key, move, g_score, h_score)
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
            new_state, auto_moves_list = apply_move(current_state, move)
            new_key = new_state.get_key()
            
            if new_key in closed:
                continue

            cost = _move_cost(len(auto_moves_list))
            new_g = g_score[current_key] + cost

            if new_g < g_score.get(new_key, float('inf')):
                g_score[new_key] = new_g
                h_score = _heuristic(new_state)
                f_score = new_g + h_score
                parent[new_key] = (current_key, move, new_g, h_score)
                
                if new_state.is_goal():
                    found_key = new_key
                    break
                
                key_to_state[new_key] = new_state
                
                counter += 1
                heapq.heappush(open_set, (f_score, new_g, counter, new_key))

        if found_key:
            break

    elapsed = time.time() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if found_key:
        path = []
        log = []
        k = found_key
        while parent[k][0] is not None:
            pk, m, step_g, step_h = parent[k]
            path.append(m)
            step_f = step_g + step_h
            
            # Làm gọn string move cho dễ đọc trên console
            src_type, src_idx, dst_type, dst_idx, num = m
            m_str = f"{src_type[:3]}_{src_idx} -> {dst_type[:3]}_{dst_idx} (x{num})"
            
            log.append(f"Move: {m_str:<25} | g: {step_g:4.1f} | h: {step_h:4.1f} | f: {step_f:4.1f}")
            k = pk
            
        path.reverse()
        log.reverse()
        
        # --- IN LOG RA CONSOLE ---
        print("\n" + "="*60)
        print(" A* PATH TRACKING (f = g + h) ")
        print("="*60)
        root_h = parent[k][3]
        print(f"Root state {' ':>24} | g:  0.0 | h: {root_h:4.1f} | f: {root_h:4.1f}")
        for i, line in enumerate(log, 1):
            print(f"Step {i:02d} | {line}")
        print("="*60 + "\n")
        # -------------------------

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