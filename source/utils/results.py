
class SolverResult(dict):
    def __init__(self, solved=False, moves=None, expanded=0, time=0.0, memory_mb=0.0, **kwargs):
        moves = moves if moves is not None else []

        solution_length = len(moves)
        
        super().__init__(
            solved=solved,
            moves=moves,
            expanded=expanded,
            time=time,
            memory_mb=memory_mb,
            solution_length=solution_length,
            **kwargs # Hỗ trợ truyền thêm các tham số phụ như 'algorithm', 'error', 'status_text'
        )