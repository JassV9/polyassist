import json
import os


class UnitStats:
    def __init__(self, name: str, data: dict[str]):
        self.name = name
        self.attack: float = data["attack"]
        self.defense: float = data["defense"]
        self.movement: int = data["movement"]
        self.range: int = data["range"]
        self.max_health: int = data["max_health"]
        self.cost: int = data["cost"]
        self.skills: list[str] = data["skills"]
        self.unlocked_by: str | None = data.get("unlocked_by")
        self.notes: str | None = data.get("notes")

class UnitKnowledge:
    def __init__(self):
        self.units: dict[str, UnitStats] = {}
        self._load()

    def _load(self):
        data_path = os.path.join(os.path.dirname(__file__), "data", "units.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            for name, stats in data.items():
                self.units[name] = UnitStats(name, stats)

    def get_unit(self, name: str) -> UnitStats | None:
        return self.units.get(name)

unit_knowledge = UnitKnowledge()
