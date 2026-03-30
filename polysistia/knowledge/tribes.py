import json
import os


class TribeMetadata:
    def __init__(self, name: str, data: dict[str]):
        self.name = name
        self.starting_tech: str | None = data["starting_tech"]
        self.special_units: list[str] = data["special_units"]
        self.color_hex: str = data.get("color_hex", "#000000")
        self.color_primary_hsv: tuple[int, int, int] = tuple(data["color_primary_hsv"])
        self.color_range_hsv: tuple[list[int], list[int]] = tuple(data["color_range_hsv"])
        self.terrain_bias: str = data["terrain_bias"]
        self.t0_capable: bool = data["t0_capable"]

class TribeKnowledge:
    def __init__(self):
        self.tribes: dict[str, TribeMetadata] = {}
        self._load()

    def _load(self):
        data_path = os.path.join(os.path.dirname(__file__), "data", "tribes.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            for name, metadata in data.items():
                self.tribes[name] = TribeMetadata(name, metadata)

    def get_tribe(self, name: str) -> TribeMetadata | None:
        return self.tribes.get(name)

tribe_knowledge = TribeKnowledge()
