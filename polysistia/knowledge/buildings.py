import json
import os


class BuildingStats:
    def __init__(self, name: str, data: dict[str]):
        self.name = name
        self.population: int = data["population"]
        self.star_income: int = data["star_income"]
        self.cost: int = data["cost"]
        self.required_tech: str = data["required_tech"]
        self.adjacency_bonus: dict[str | None] = data.get("adjacency_bonus")

class BuildingKnowledge:
    def __init__(self):
        self.buildings: dict[str, BuildingStats] = {}
        self._load()

    def _load(self):
        data_path = os.path.join(os.path.dirname(__file__), "data", "buildings.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            for name, stats in data.items():
                self.buildings[name] = BuildingStats(name, stats)

    def get_building(self, name: str) -> BuildingStats | None:
        return self.buildings.get(name)

building_knowledge = BuildingKnowledge()
