# core/move_generator.py
"""
Heavily optimized move generation for FreeCell solver.
"""

from .rules import Rules

SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RV = Rules.RANK_VALUES


def _opp_suits(suit):
    return ('clubs', 'spades') if suit in ('hearts', 'diamonds') else ('hearts', 'diamonds')


def is_safe_auto(state, card):
    val = RV[card.rank]
    if val <= 1:
        return True
    for s in _opp_suits(card.suit):
        if len(state.foundations[s]) < val - 1:
            return False
    return True


def _can_fnd(state, card):
    fnd = state.foundations[card.suit]
    val = RV[card.rank]
    return (val == 1 and not fnd) or (fnd and val == RV[fnd[-1].rank] + 1)


def auto_to_foundation(state):
    moves = []
    changed = True
    while changed:
        changed = False
        for i in range(8):
            cas = state.cascades[i]
            if cas:
                card = cas[-1]
                if _can_fnd(state, card) and is_safe_auto(state, card):
                    state.foundations[card.suit].append(card)
                    cas.pop()
                    moves.append(('cascade', i, 'foundation', card.suit, 1))
                    changed = True
                    break
        if changed:
            continue
        for i in range(4):
            card = state.free_cells[i]
            if card and _can_fnd(state, card) and is_safe_auto(state, card):
                state.foundations[card.suit].append(card)
                state.free_cells[i] = None
                moves.append(('freecell', i, 'foundation', card.suit, 1))
                changed = True
                break
    return moves


def _seq_len_from_bottom(cas):
    """Length of valid descending alternating sequence from bottom of cascade."""
    if not cas:
        return 0
    n = 1
    for j in range(len(cas) - 2, -1, -1):
        top = cas[j]
        bot = cas[j + 1]
        if top.color != bot.color and RV[top.rank] == RV[bot.rank] + 1:
            n += 1
        else:
            break
    return n


def get_valid_moves(state):
    moves = []
    cascades = state.cascades
    free_cells = state.free_cells

    # 1. Foundation (unsafe only - safe ones are auto-moved)
    for i in range(8):
        cas = cascades[i]
        if cas and _can_fnd(state, cas[-1]) and not is_safe_auto(state, cas[-1]):
            moves.append(('cascade', i, 'foundation', cas[-1].suit, 1))

    for i in range(4):
        c = free_cells[i]
        if c and _can_fnd(state, c) and not is_safe_auto(state, c):
            moves.append(('freecell', i, 'foundation', c.suit, 1))

    # Find first empty cascade and freecell (symmetry breaking)
    first_empty_cas = -1
    for i in range(8):
        if not cascades[i]:
            first_empty_cas = i
            break

    first_empty_fc = -1
    for i in range(4):
        if free_cells[i] is None:
            first_empty_fc = i
            break

    empty_fc_count = sum(1 for c in free_cells if c is None)

    # 2. FC -> non-empty cascade
    for i in range(4):
        card = free_cells[i]
        if card is None:
            continue
        for j in range(8):
            cas = cascades[j]
            if not cas:
                continue
            target = cas[-1]
            if card.color != target.color and RV[card.rank] == RV[target.rank] - 1:
                moves.append(('freecell', i, 'cascade', j, 1))

    # 3. Cascade -> Cascade
    empty_cas_count = sum(1 for c in cascades if not c)
    for i in range(8):
        cas = cascades[i]
        if not cas:
            continue

        max_seq = _seq_len_from_bottom(cas)

        for length in range(1, max_seq + 1):
            start_idx = len(cas) - length
            bottom_card = cas[start_idx]

            # To non-empty
            for j in range(8):
                if i == j:
                    continue
                tcas = cascades[j]
                if not tcas:
                    continue
                target = tcas[-1]
                if bottom_card.color != target.color and RV[bottom_card.rank] == RV[target.rank] - 1:
                    # Check max movable
                    efc = empty_fc_count
                    ec = empty_cas_count
                    max_m = (efc + 1) * (2 ** ec)
                    if length <= max_m:
                        moves.append(('cascade', i, 'cascade', j, length))

            # To first empty cascade (not whole column)
            if first_empty_cas >= 0 and first_empty_cas != i and start_idx > 0:
                efc = empty_fc_count
                ec = empty_cas_count - 1  # one less empty since target is empty
                max_m = (efc + 1) * (2 ** ec)
                if length <= max_m:
                    moves.append(('cascade', i, 'cascade', first_empty_cas, length))

    # 4. FC King -> empty cascade
    if first_empty_cas >= 0:
        for i in range(4):
            c = free_cells[i]
            if c and RV[c.rank] == 13:
                moves.append(('freecell', i, 'cascade', first_empty_cas, 1))

    # 5. Cascade -> FC (last resort)
    if first_empty_fc >= 0:
        for i in range(8):
            if cascades[i]:
                moves.append(('cascade', i, 'freecell', first_empty_fc, 1))

    return moves


def apply_move(state, move):
    ns = state.clone()
    _apply_inplace(ns, move)
    auto = auto_to_foundation(ns)
    return ns, auto


def _apply_inplace(state, move):
    src_type, src_idx, dst_type, dst_idx, num = move
    if src_type == 'cascade':
        cas = state.cascades[src_idx]
        moving = cas[-num:]
        del cas[-num:]
    else:
        moving = [state.free_cells[src_idx]]
        state.free_cells[src_idx] = None

    if dst_type == 'cascade':
        state.cascades[dst_idx].extend(moving)
    elif dst_type == 'freecell':
        state.free_cells[dst_idx] = moving[0]
    else:
        state.foundations[dst_idx].append(moving[0])


def apply_move_inplace(state, move):
    _apply_inplace(state, move)
    return auto_to_foundation(state)


def compute_animation_steps(initial_state, solver_moves):
    state = initial_state.clone()
    steps = list(auto_to_foundation(state))
    for move in solver_moves:
        _apply_inplace(state, move)
        steps.append(move)
        steps.extend(auto_to_foundation(state))
    return steps


def describe_move(move):
    src_type, src_idx, dst_type, dst_idx, num = move
    sym = {'hearts': 'H', 'diamonds': 'D', 'clubs': 'C', 'spades': 'S'}
    src = f"C{src_idx+1}" if src_type == 'cascade' else f"FC{src_idx+1}"
    if dst_type == 'cascade':
        dst = f"C{dst_idx+1}"
    elif dst_type == 'freecell':
        dst = f"FC{dst_idx+1}"
    else:
        dst = f"Fnd-{sym.get(dst_idx, dst_idx)}"
    return f"{src}->{dst}({num})"