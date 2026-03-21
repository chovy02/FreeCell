import copy
# gui/solution_player.py
"""Animates solver solution moves on the board."""

from core.move_generator import compute_animation_steps, describe_move, _apply_inplace


class SolutionPlayer:
    def __init__(self):
        self.steps = []          # flat list of all moves (including auto-foundation)
        self.current_step = 0
        self.playing = False
        self.timer = 0
        self.delay = 20          # frames between moves (lower = faster)
        self.move_log = []       # human-readable log
        self.initial_state = None

    def start(self, initial_state, solver_moves, is_astar=False):
        """Compute animation steps and start playback."""
        self.initial_state = initial_state.clone()
        
        # Nếu là A*, dùng thẳng kết quả (không qua auto_move nữa)
        if is_astar:
            self.steps = solver_moves
        else:
            self.steps = compute_animation_steps(initial_state, solver_moves)
            
        self.current_step = 0
        self.playing = True
        self.timer = 0
        self.move_log = []

    def stop(self):
        self.playing = False

    def update(self, state):
        """Called every frame. Apply next move when timer fires."""
        if not self.playing:
            return

        self.timer += 1
        if self.timer < self.delay:
            return
        self.timer = 0

        if self.current_step < len(self.steps):
            move = self.steps[self.current_step]
            _apply_inplace(state, move)
            desc = describe_move(move)
            self.move_log.append(f"{self.current_step + 1}. {desc}")
            self.current_step += 1
        else:
            self.playing = False

    def get_info(self):
        return {
            'playing': self.playing,
            'current_step': self.current_step,
            'total_steps': len(self.steps),
        }