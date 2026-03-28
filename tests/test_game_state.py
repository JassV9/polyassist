from polysistia.state.models import GameState, City, Unit, Position, Tile, TileType, UnitType
from polysistia.state.serializer import GameStateSerializer
import json

def test_game_state_serialization():
    state = GameState(
        turn=1,
        stars=5,
        star_income=2,
        score=100,
        player_tribe="bardur",
        cities=[
            City(name="Barduria", position=Position(x=0, y=0), owner_tribe="bardur", level=1, population=0, buildings=[])
        ],
        units=[
            Unit(unit_type=UnitType.WARRIOR, position=Position(x=1, y=1), owner_tribe="bardur", health=1.0)
        ],
        enemy_units=[],
        enemy_cities=[],
        visible_tiles=[
            Tile(position=Position(x=0, y=0), tile_type=TileType.GROUND)
        ],
        fog_tiles=[],
        researched_techs=["hunting"],
        game_mode="perfection",
        confidence=0.95
    )

    json_str = GameStateSerializer.to_json(state)
    data = json.loads(json_str)
    assert data["turn"] == 1
    assert data["player_tribe"] == "bardur"
    assert len(data["cities"]) == 1
    assert len(data["units"]) == 1

def test_compact_text_serialization():
    state = GameState(
        turn=1,
        stars=5,
        star_income=2,
        score=100,
        player_tribe="bardur",
        cities=[City(name="City1", position=Position(x=0, y=0), owner_tribe="bardur", level=1, population=0, buildings=[])],
        units=[Unit(unit_type=UnitType.WARRIOR, position=Position(x=1, y=1), owner_tribe="bardur", health=1.0)],
        enemy_units=[],
        enemy_cities=[],
        visible_tiles=[],
        fog_tiles=[],
        researched_techs=[],
        game_mode="domination",
        confidence=1.0
    )

    text = GameStateSerializer.to_compact_text(state)
    assert "Turn: 1" in text
    assert "Stars: 5 (+2)" in text
    assert "City1" in text
    assert "warrior@1,1" in text
