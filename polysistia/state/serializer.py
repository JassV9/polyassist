import json
from .models import GameState, Tile, Unit, City


class GameStateSerializer:
    @staticmethod
    def to_json(state: GameState) -> str:
        return state.model_dump_json(indent=2)

    @staticmethod
    def to_compact_text(state: GameState) -> str:
        """
        Produce a compact text representation for LLM prompts.
        """
        summary = []
        summary.append(f"Turn: {state.turn}")
        summary.append(f"Stars: {state.stars} (+{state.star_income})")
        summary.append(f"Score: {state.score}")
        summary.append(f"Tribe: {state.player_tribe}")
        summary.append(f"Cities ({len(state.cities)}): " + ", ".join([f"{c.name} (Lvl {c.level})" for c in state.cities]))
        summary.append(f"Units ({len(state.units)}): " + ", ".join([f"{u.unit_type.value}@{u.position.x},{u.position.y}" for u in state.units]))
        summary.append(f"Enemy Units ({len(state.enemy_units)}): " + ", ".join([f"{u.unit_type.value}@{u.position.x},{u.position.y}" for u in state.enemy_units]))

        return "\n".join(summary)

    @staticmethod
    def to_summary(state: GameState) -> str:
        """
        Human-readable summary of the current game state.
        """
        return f"Turn {state.turn} | {state.stars} Stars | {len(state.units)} Units | {len(state.cities)} Cities"
