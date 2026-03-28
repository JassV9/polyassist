from pydantic import BaseModel, Field
from enum import Enum


class TileType(str, Enum):
    GROUND = "ground"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    WATER = "water"
    OCEAN = "ocean"
    ICE = "ice"
    FUNGUS = "fungus"
    FIELDS = "fields"

class ResourceType(str, Enum):
    FRUIT = "fruit"
    CROP = "crop"
    ANIMAL = "animal"
    FISH = "fish"
    WHALE = "whale"
    METAL = "metal"
    STARFISH = "starfish"

class UnitType(str, Enum):
    # Standard Units
    WARRIOR = "warrior"
    RIDER = "rider"
    ARCHER = "archer"
    DEFENDER = "defender"
    KNIGHT = "knight"
    CATAPULT = "catapult"
    SWORDSMAN = "swordsman"
    MIND_BENDER = "mind_bender"
    GIANT = "giant"
    # Naval Units
    BOAT = "boat"
    SHIP = "ship"
    BATTLESHIP = "battleship"
    BOMBER = "bomber"
    SCOUT = "scout"
    RAMMER = "rammer"
    # Special Tribe Units
    CLOAK = "cloak"
    DAGGER = "dagger"
    POLYTAUR = "polytaur"
    NAVALON = "navalon"
    TRIDENTION = "tridention"
    BATTLE_SLED = "battle_sled"
    ICE_ARCHER = "ice_archer"
    MOONI = "mooni"
    ICE_FORTRESS = "ice_fortress"
    GAAMI = "gaami"
    HEXAPOD = "hexapod"
    KITON = "kiton"
    PHYCHI = "phychi"
    RAYCHI = "raychi"
    DOOMUX = "doomux"
    SHAMAN = "shaman"
    EXIDA = "exida"
    CENTIPEDE = "centipede"
    SEGMENT = "segment"
    DRAGON_EGG = "dragon_egg"
    BABY_DRAGON = "baby_dragon"
    FIRE_DRAGON = "fire_dragon"
    NATURE_BUNNY = "nature_bunny"

class Position(BaseModel):
    x: int
    y: int

class Tile(BaseModel):
    position: Position
    tile_type: TileType
    resource: ResourceType | None = None
    improvement: str | None = None
    owner_tribe: str | None = None
    has_road: bool = False
    in_city_borders: bool = False

class Unit(BaseModel):
    unit_type: UnitType
    position: Position
    owner_tribe: str
    health: float          # 0.0 - 1.0 from health bar
    is_veteran: bool = False
    has_moved: bool = False

class City(BaseModel):
    name: str
    position: Position
    owner_tribe: str
    level: int
    population: int
    buildings: list[str]
    has_wall: bool = False

class GameState(BaseModel):
    turn: int
    stars: int
    star_income: int
    score: int
    player_tribe: str
    cities: list[City]
    units: list[Unit]
    enemy_units: list[Unit]
    enemy_cities: list[City]
    visible_tiles: list[Tile]
    fog_tiles: list[Position]
    researched_techs: list[str]
    game_mode: str           # "perfection" or "domination" or "creative"
    confidence: float        # overall extraction confidence 0.0-1.0
