import time
import heapq

class AStarSolver:
    def __init__(self, initial_state, cap=200000):
        self.initial_state = initial_state
        self.cap = cap

        self.suits_order = ['hearts', 'diamonds', 'clubs', 'spades']

        self.rank_vals = {
            'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13
        }

    # ========================
    # STATE → HASHABLE
    # ========================
    def to_hashable(self, state):
        founds = tuple(len(state.foundations[s]) for s in self.suits_order)

        fc = tuple(
            (c.rank, c.suit, c.color) if c else None
            for c in state.free_cells
        )

        cascs = tuple(
            tuple((c.rank, c.suit, c.color) for c in cascade)
            for cascade in state.cascades
        )

        return (founds, fc, cascs)

    def is_won(self, h_state):
        return sum(h_state[0]) == 52

    # ========================
    # HEURISTIC (CHUẨN A*)
    # ========================
    def heuristic(self, h_state):
        founds, fc, cascs = h_state

        # lower bound chuẩn
        h = 52 - sum(founds)

        # penalty nhẹ cho sai thứ tự (vẫn admissible)
        for cascade in cascs:
            for i in range(len(cascade) - 1):
                below = cascade[i]
                above = cascade[i + 1]

                if not (
                    below[2] != above[2] and
                    self.rank_vals[below[0]] == self.rank_vals[above[0]] + 1
                ):
                    h += 1

        return h

    # ========================
    # MOVE GENERATION
    # ========================
    def get_moves_and_children(self, h_state):
        founds, fc, cascs = h_state
        moves = []

        empty_fc = sum(1 for c in fc if c is None)
        empty_casc = sum(1 for c in cascs if not c)

        def make_child(nf, nfc, nc):
            return (tuple(nf), tuple(nfc), tuple(tuple(c) for c in nc))

        # ===== FREECELL =====
        for i, card in enumerate(fc):
            if not card:
                continue

            rank, suit, color = card
            val = self.rank_vals[rank]
            suit_idx = self.suits_order.index(suit)

            # → foundation
            if founds[suit_idx] == val - 1:
                nf = list(founds); nf[suit_idx] += 1
                nfc = list(fc); nfc[i] = None
                moves.append((make_child(nf, nfc, cascs), ('freecell', i, 'foundation', suit, 1)))

            # → cascade
            for j, cascade in enumerate(cascs):
                if not cascade:
                    nfc = list(fc); nfc[i] = None
                    nc = [list(c) for c in cascs]
                    nc[j].append(card)
                    moves.append((make_child(founds, nfc, nc), ('freecell', i, 'cascade', j, 1)))
                else:
                    t = cascade[-1]
                    if color != t[2] and val == self.rank_vals[t[0]] - 1:
                        nfc = list(fc); nfc[i] = None
                        nc = [list(c) for c in cascs]
                        nc[j].append(card)
                        moves.append((make_child(founds, nfc, nc), ('freecell', i, 'cascade', j, 1)))

        # ===== CASCADE =====
        for i, cascade in enumerate(cascs):
            if not cascade:
                continue

            b = cascade[-1]
            val = self.rank_vals[b[0]]
            suit_idx = self.suits_order.index(b[1])

            # → foundation
            if founds[suit_idx] == val - 1:
                nf = list(founds); nf[suit_idx] += 1
                nc = [list(c) for c in cascs]
                nc[i].pop()
                moves.append((make_child(nf, fc, nc), ('cascade', i, 'foundation', b[1], 1)))

            # → freecell
            if empty_fc > 0:
                for f_idx in range(4):
                    if fc[f_idx] is None:
                        nfc = list(fc); nfc[f_idx] = b
                        nc = [list(c) for c in cascs]
                        nc[i].pop()
                        moves.append((make_child(founds, nfc, nc), ('cascade', i, 'freecell', f_idx, 1)))
                        break

            # sequence detection
            seq_len = 1
            for k in range(len(cascade) - 2, -1, -1):
                c1, c2 = cascade[k], cascade[k+1]
                if c1[2] != c2[2] and self.rank_vals[c1[0]] == self.rank_vals[c2[0]] + 1:
                    seq_len += 1
                else:
                    break

            for j, target in enumerate(cascs):
                if i == j:
                    continue

                max_move = (empty_fc + 1) * (2 ** (empty_casc - (1 if not target else 0)))
                max_p = min(seq_len, max_move)

                if not target:
                    if max_p > 0:
                        nc = [list(c) for c in cascs]
                        moving = nc[i][-max_p:]
                        nc[i] = nc[i][:-max_p]
                        nc[j].extend(moving)
                        moves.append((make_child(founds, fc, nc), ('cascade', i, 'cascade', j, max_p)))
                else:
                    t = target[-1]
                    for p in range(1, max_p + 1):
                        m = cascade[-p]
                        if m[2] != t[2] and self.rank_vals[m[0]] == self.rank_vals[t[0]] - 1:
                            nc = [list(c) for c in cascs]
                            moving = nc[i][-p:]
                            nc[i] = nc[i][:-p]
                            nc[j].extend(moving)
                            moves.append((make_child(founds, fc, nc), ('cascade', i, 'cascade', j, p)))
                            break

        return moves

    # ========================
    # A* SOLVER
    # ========================
    def solve(self):
        print("\n--- A* SOLVER START ---")
        start_time = time.time()

        start = self.to_hashable(self.initial_state)

        open_set = []
        counter = 0

        heapq.heappush(open_set, (self.heuristic(start), 0, counter, start))

        came_from = {}
        g_score = {start: 0}
        closed_set = set()

        steps = 0

        while open_set:
            f, g, _, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            closed_set.add(current)
            steps += 1

            if steps % 5000 == 0:
                print(f"Checked: {steps} | Time: {time.time()-start_time:.2f}s")

            if self.is_won(current):
                print(f"WIN in {time.time()-start_time:.2f}s | {steps} states")

                path = []
                while current in came_from:
                    current, move = came_from[current]
                    path.append(move)

                return path[::-1]

            if steps >= self.cap:
                print("CAP LIMIT HIT")
                return []

            for child, move in self.get_moves_and_children(current):
                if child in closed_set:
                    continue

                tentative_g = g_score[current] + 1

                if tentative_g < g_score.get(child, float('inf')):
                    came_from[child] = (current, move)
                    g_score[child] = tentative_g

                    f_score = tentative_g + self.heuristic(child)

                    counter += 1
                    heapq.heappush(open_set, (f_score, tentative_g, counter, child))

        print("NO SOLUTION")
        return []