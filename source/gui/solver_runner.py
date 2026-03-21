# gui/solver_runner.py
"""Runs solvers in background threads."""
import threading


class SolverRunner:
    def __init__(self):
        self.solving = False
        self._result = None
        self._algorithm = ""

    def run(self, algorithm, initial_state, callback):
        """Start solver in background thread."""
        if self.solving:
            return

        self.solving = True
        self._algorithm = algorithm.upper().replace('STAR', '*')
        self._result = None

        solve_state = initial_state.clone()

        def _work():
            try:
                import time, tracemalloc
                tracemalloc.start()
                t0 = time.time()

                if algorithm == 'bfs':
                    from solvers.BFS import solve_bfs
                    result = solve_bfs(solve_state, node_limit=500_000)

                elif algorithm == 'dfs':
                    from solvers.DFS import solve_dfs
                    result = solve_dfs(solve_state, depth_limit=300, node_limit=2_000_000)

                elif algorithm == 'ucs':
                    from solvers.UCS import solve_ucs
                    result = solve_ucs(solve_state, node_limit=500_000)

                elif algorithm == 'astar':
                    from solvers.A_star import AStarSolver
                    solver = AStarSolver(solve_state)
                    astar_moves = solver.solve()
                    elapsed = time.time() - t0
                    _, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()

                    converted = [self._convert_astar(m) for m in astar_moves]
                    result = {
                        'solved': len(astar_moves) > 0,
                        'moves': converted,
                        'expanded': 0,
                        'time': elapsed,
                        'memory_mb': peak / 1024 / 1024,
                        'solution_length': len(astar_moves)
                    }
                else:
                    result = {
                        'solved': False, 'moves': [], 'expanded': 0,
                        'time': 0, 'memory_mb': 0, 'solution_length': 0
                    }

                result['algorithm'] = self._algorithm
                self._result = result
                callback(result)

            except Exception as e:
                import traceback
                traceback.print_exc()
                result = {
                    'algorithm': self._algorithm,
                    'solved': False, 'error': str(e),
                    'moves': [], 'expanded': 0,
                    'time': 0, 'memory_mb': 0, 'solution_length': 0
                }
                self._result = result
                callback(result)
            finally:
                self.solving = False

        thread = threading.Thread(target=_work, daemon=True)
        thread.start()

    def cancel(self):
        self.solving = False

    def get_status(self):
        """Get current status for display while solving."""
        return {
            'algorithm': self._algorithm,
            'solved': False,
            'status_text': 'Solving...',
            'time': 0, 'memory_mb': 0,
            'expanded': 0, 'solution_length': 0
        }

    @staticmethod
    def _convert_astar(move):
        """Convert A* move format to move_generator format."""
        m_type, src, dst, count = move
        mapping = {
            'c_c': ('cascade', 'cascade'),
            'c_found': ('cascade', 'foundation'),
            'c_f': ('cascade', 'freecell'),
            'f_c': ('freecell', 'cascade'),
            'f_found': ('freecell', 'foundation'),
        }
        src_type, dst_type = mapping.get(m_type, ('cascade', 'cascade'))
        return (src_type, src, dst_type, dst, count)