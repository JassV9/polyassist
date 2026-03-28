import json
import os


class TribeStrategy:
    def __init__(self, name: str, data: dict[str]):
        self.name = name
        self.opening_sequence: list[str] = data.get("opening_sequence", [])
        self.ideal_star_income: dict[str, int] = data.get("ideal_star_income", {})
        self.tech_paths: dict[str, list[str]] = data.get("tech_paths", {})
        self.key_decisions: dict[str, str] = data.get("key_decisions", {})

class StrategyKnowledge:
    def __init__(self):
        self.strategies: dict[str, TribeStrategy] = {}
        self._load()

    def _load(self):
        data_path = os.path.join(os.path.dirname(__file__), "data", "tribe_strategies.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            for name, strategy_data in data.items():
                self.strategies[name] = TribeStrategy(name, strategy_data)

    def get_strategy(self, name: str) -> TribeStrategy | None:
        return self.strategies.get(name)

strategy_knowledge = StrategyKnowledge()
