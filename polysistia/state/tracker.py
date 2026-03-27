
from .models import GameState, Tile, Unit, City, Position
import logging

logger = logging.getLogger(__name__)

class GameStateTracker:
    def __init__(self):
        self.current_state: GameState | None = None
        self.history: list[GameState] = []
        self.fog_of_war_memory: dict[str, Tile] = {} # Keyed by "gx,gy"

    def update(self, new_state: GameState) -> GameState:
        """
        Merge new observations into existing state, handling fog of war.
        """
        if self.current_state is None:
            self.current_state = new_state
            # Initialize fog of war memory with visible tiles
            for tile in new_state.visible_tiles:
                key = f"{tile.position.x},{tile.position.y}"
                self.fog_of_war_memory[key] = tile
            return new_state

        # Handle turn change
        if new_state.turn > self.current_state.turn:
            self.history.append(self.current_state)
            logger.info(f"Turn changed from {self.current_state.turn} to {new_state.turn}")

        # Update fog of war memory with new visible tiles
        for tile in new_state.visible_tiles:
            key = f"{tile.position.x},{tile.position.y}"
            self.fog_of_war_memory[key] = tile

        # Reconstruct full list of tiles (including those in fog of war)
        # In this Phase 1+2, we just keep the visible tiles and current memory
        # A more complex merge would happen here

        self.current_state = new_state
        return self.current_state

    def get_tile_at(self, x: int, y: int) -> Tile | None:
        key = f"{x},{y}"
        return self.fog_of_war_memory.get(key)
