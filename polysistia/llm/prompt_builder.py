from ..state.models import GameState
from ..state.serializer import GameStateSerializer
from ..knowledge.strategies import strategy_knowledge


class PromptBuilder:
    def __init__(self):
        self.system_prompt = (
            "You are Polysistia, an expert AI coach for The Battle of Polytopia. "
            "Your goal is to analyze the current game state and provide tactical advice, "
            "economic optimizations, and strategic tech paths for the player. "
            "Be concise, data-driven, and prioritize immediate actions."
        )

    def build_advisory_prompt(self, state: GameState, question: str | None = None) -> str:
        """
        Build a prompt including game state and relevant strategy context.
        """
        compact_state = GameStateSerializer.to_compact_text(state)

        # Add strategy context if available for the player's tribe
        strategy = strategy_knowledge.get_strategy(state.player_tribe)
        strategy_context = ""
        if strategy:
            strategy_context = (
                f"\nStrategic Heuristics for {state.player_tribe.capitalize()}:\n"
                f"- Opening: {', '.join(strategy.opening_sequence[:3])}\n"
                f"- Key Decisions: {strategy.key_decisions}\n"
            )

        prompt = (
            f"{self.system_prompt}\n\n"
            f"Current Game State:\n{compact_state}\n"
            f"{strategy_context}\n"
            "Analyze this state and provide 3 key recommendations for this turn."
        )

        if question:
            prompt += f"\n\nPlayer Question: {question}"

        return prompt
