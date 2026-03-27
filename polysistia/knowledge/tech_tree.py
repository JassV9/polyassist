import json
import os


class TechNode:
    def __init__(self, name: str, data: dict[str]):
        self.name = name
        self.tier: int = data["tier"]
        self.branch: str = data["branch"]
        self.cost_formula: str = data["cost_formula"]
        self.prerequisites: list[str] = data["prerequisites"]
        self.unlocks: list[str] = data["unlocks"]
        self.leads_to: list[str] = data["leads_to"]
        self.starting_tech_of: list[str] = data["starting_tech_of"]

class TechTree:
    def __init__(self):
        self.techs: dict[str, TechNode] = {}
        self._load()

    def _load(self):
        data_path = os.path.join(os.path.dirname(__file__), "data", "tech_tree.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            for name, tech_data in data.items():
                self.techs[name] = TechNode(name, tech_data)

    def get_tech(self, name: str) -> TechNode | None:
        return self.techs.get(name)

    def get_unlocks(self, name: str) -> list[str]:
        tech = self.get_tech(name)
        return tech.unlocks if tech else []

tech_tree = TechTree()
