# gui/solver_runner.py
"""Runs solvers in background threads."""
import threading


class SolverRunner:
    def __init__(self):
        self.solving = False
        self._result = None
        self._algorithm = ""

    def run(self, algorithm, initial_state, callback):
        if self.solving:
            return
        self.solving = True
        self._algorithm = algorithm.upper().replace('STAR', '*')
        self._result = None
        solve_state = initial_state.clone()

        def _work():
            try:
                if algorithm == 'bfs':
                    from solvers.BFS import solve_bfs
                    result = solve_bfs(solve_state, node_limit=2_000_000)
                elif algorithm == 'dfs':
                    from solvers.DFS import solve_dfs
                    result = solve_dfs(solve_state, depth_limit=300, node_limit=2_000_000)
                elif algorithm == 'ucs':
                    from solvers.UCS import solve_ucs
                    result = solve_ucs(solve_state, node_limit=2_000_000)
                elif algorithm == 'astar':
                    from solvers.A_star import solve_astar
                    result = solve_astar(solve_state, node_limit=500_000)
                else:
                    result = {'solved': False, 'moves': [], 'expanded': 0,
                              'time': 0, 'memory_mb': 0, 'solution_length': 0}

                result['algorithm'] = self._algorithm
                self._result = result
                callback(result)
            except Exception as e:
                import traceback; traceback.print_exc()
                result = {'algorithm': self._algorithm, 'solved': False, 'error': str(e),
                          'moves': [], 'expanded': 0, 'time': 0, 'memory_mb': 0, 'solution_length': 0}
                self._result = result; callback(result)
            finally:
                self.solving = False

        threading.Thread(target=_work, daemon=True).start()

    def cancel(self):
        self.solving = False

    def get_status(self):
        return {'algorithm': self._algorithm, 'solved': False, 'status_text': 'Solving...',
                'time': 0, 'memory_mb': 0, 'expanded': 0, 'solution_length': 0}