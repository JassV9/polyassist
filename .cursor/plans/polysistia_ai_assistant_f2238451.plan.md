---
name: Polysistia AI Assistant
overview: Build the foundation of Polysistia -- a real-time AI coaching overlay for The Battle of Polytopia. Phase 1+2 covers screen capture, game state extraction via CV/OCR, structured game state models, a Polytopia knowledge base, a provider-agnostic LLM interface, and a minimal proof-of-concept overlay.
todos:
  - id: project-scaffold
    content: Create project structure, README, requirements.txt, setup.py with all dependencies
    status: pending
  - id: capture-subsystem
    content: Implement screen capture with dxcam (primary) and mss (fallback) backends, window finder, and change detector
    status: pending
  - id: calibration-system
    content: Build calibration_template.json, config loader, and interactive calibration wizard tool
    status: pending
  - id: vision-ocr
    content: Implement OCR extraction for turn number, stars, star income, score from calibrated screen regions
    status: pending
  - id: vision-grid
    content: Build grid mapper for pixel-to-tile coordinate translation using calibration parameters
    status: pending
  - id: vision-tiles
    content: Implement tile classifier via OpenCV template matching for all tile types, resources, and improvements
    status: pending
  - id: vision-units
    content: Implement unit detector via template matching for all unit types with tribe color detection and health bar reading
    status: pending
  - id: vision-tech
    content: Build tech tree reader that detects researched vs unresearched technologies from the tech tree screen
    status: pending
  - id: state-models
    content: Define all Pydantic data models (GameState, Tile, Unit, City, TechTree, etc.) and JSON serializer
    status: pending
  - id: state-tracker
    content: Build stateful GameStateTracker that accumulates observations across frames with fog-of-war memory
    status: pending
  - id: knowledge-base
    content: Create comprehensive JSON data files for tech tree, units, buildings, tribes, and tribe strategies from Polytopia wiki
    status: pending
  - id: llm-interface
    content: Build provider-agnostic LLM interface with OpenAI, Anthropic, and Ollama backends plus prompt builder
    status: pending
  - id: overlay-poc
    content: Build minimal PyQt6 transparent overlay showing extracted game state debug info with F1 toggle
    status: pending
  - id: main-loop
    content: "Wire everything together in async main loop: capture -> change detect -> extract -> track -> overlay"
    status: pending
  - id: tools
    content: Build calibration wizard, template capture helper, and CLI state viewer diagnostic tools
    status: pending
isProject: false
---

# Polysistia: AI Coaching Assistant for The Battle of Polytopia

## Scope (Phase 1+2)

Screen capture, computer vision pipeline, OCR-based game state extraction, structured data models encoding Polytopia domain knowledge, a provider-agnostic LLM interface for future advisory phases, and a minimal transparent overlay that proves the system can "see" the game.

---

## Project Structure

```
polysistia/
├── README.md
├── requirements.txt
├── setup.py
├── calibration_template.json
├── polysistia/
│   ├── __init__.py
│   ├── main.py                    # Entry point, orchestrates all subsystems
│   ├── config.py                  # Settings, calibration loading, env vars
│   │
│   ├── capture/                   # Screen capture subsystem
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract CaptureBackend interface
│   │   ├── dxcam_backend.py       # Windows GPU-accelerated capture (primary)
│   │   ├── mss_backend.py         # Cross-platform fallback capture
│   │   └── window_finder.py       # Locate Polytopia window by title/class
│   │
│   ├── vision/                    # Game state extraction via CV + OCR
│   │   ├── __init__.py
│   │   ├── ocr.py                 # Tesseract OCR for text regions (turn, stars, score)
│   │   ├── tile_classifier.py     # Template matching for tile types
│   │   ├── unit_detector.py       # Template matching for unit types + tribe colors
│   │   ├── grid_mapper.py         # Pixel-to-tile coordinate mapping via calibration
│   │   ├── tech_tree_reader.py    # Detect researched techs from tech tree screen
│   │   ├── change_detector.py     # Frame diff to detect meaningful screen changes
│   │   └── templates/             # Reference images for template matching
│   │       ├── tiles/             # forest.png, mountain.png, water.png, etc.
│   │       ├── units/             # warrior.png, rider.png, archer.png, etc.
│   │       ├── buildings/         # farm.png, mine.png, lumber_hut.png, etc.
│   │       └── icons/             # tech icons, resource icons, UI elements
│   │
│   ├── state/                     # Game state data models
│   │   ├── __init__.py
│   │   ├── models.py              # Dataclasses: GameState, Tile, Unit, City, TechTree
│   │   ├── tracker.py             # Stateful tracker that accumulates state across turns
│   │   └── serializer.py          # JSON serialization for LLM prompts and logging
│   │
│   ├── knowledge/                 # Polytopia domain knowledge base
│   │   ├── __init__.py
│   │   ├── tech_tree.py           # Full tech tree graph with costs, prerequisites, unlocks
│   │   ├── units.py               # Unit stats: attack, defense, movement, range, cost, skills
│   │   ├── buildings.py           # Building stats: population, star income, adjacency bonuses
│   │   ├── tribes.py              # Tribe data: starting tech, special units, color palette
│   │   ├── strategies.py          # Encoded strategy knowledge (opening sequences, benchmarks)
│   │   └── data/                  # Raw JSON data files
│   │       ├── tech_tree.json
│   │       ├── units.json
│   │       ├── buildings.json
│   │       ├── tribes.json
│   │       └── tribe_strategies.json
│   │
│   ├── llm/                       # Provider-agnostic LLM interface (for Phase 3)
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract LLMProvider interface
│   │   ├── openai_provider.py     # OpenAI GPT-4o (text + vision)
│   │   ├── anthropic_provider.py  # Anthropic Claude (text + vision)
│   │   ├── ollama_provider.py     # Local Ollama models
│   │   └── prompt_builder.py      # Constructs prompts from GameState + knowledge base
│   │
│   ├── overlay/                   # Minimal HUD overlay (proof of concept)
│   │   ├── __init__.py
│   │   ├── overlay_window.py      # Transparent always-on-top window (PyQt6)
│   │   └── renderer.py            # Renders game state debug info on overlay
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py             # Structured logging
│       └── image_utils.py         # Common image processing helpers
│
├── tools/
│   ├── calibration_wizard.py      # Interactive tool to create calibration.json
│   ├── template_capture.py        # Helper to capture reference templates from game
│   └── state_viewer.py            # CLI tool to dump current extracted game state
│
└── tests/
    ├── test_ocr.py
    ├── test_tile_classifier.py
    ├── test_grid_mapper.py
    ├── test_game_state.py
    ├── test_knowledge.py
    └── fixtures/                  # Sample screenshots for testing
        └── screenshots/
```

---

## Dependencies (`requirements.txt`)

```
dxcam>=0.4.0
mss>=9.0.1
opencv-python>=4.8.0
pytesseract>=0.3.10
Pillow>=10.0.0
pywin32>=306
numpy>=1.24.0
PyQt6>=6.5.0
pydantic>=2.0.0
openai>=1.0.0
anthropic>=0.30.0
httpx>=0.27.0
```

---

## Subsystem Details

### 1. Screen Capture (`capture/`)

**Abstract interface** in `base.py`:

```python
from abc import ABC, abstractmethod
import numpy as np

class CaptureBackend(ABC):
    @abstractmethod
    def grab(self, region: tuple[int,int,int,int] | None = None) -> np.ndarray:
        """Capture screen region as BGR numpy array. None = full game window."""
        ...

    @abstractmethod
    def find_game_window(self) -> tuple[int,int,int,int] | None:
        """Return (x, y, w, h) of the Polytopia window, or None."""
        ...
```

**Primary backend** (`dxcam_backend.py`): Uses `dxcam` for GPU-accelerated capture at sub-15ms latency. Falls back to `mss_backend.py` for cross-platform support.

**Window finder** (`window_finder.py`): Uses `win32gui` (from `pywin32`) to locate the Polytopia window by title string "The Battle of Polytopia". Handles Steam overlay and windowed/borderless modes.

**Change detection** (`change_detector.py`): Compares consecutive frames via structural similarity (SSIM) or mean pixel diff. Only triggers full CV extraction when the screen has meaningfully changed (threshold ~5% difference). This avoids burning CPU/GPU on identical frames during opponent turns or idle states.

### 2. Vision / Game State Extraction (`vision/`)

This is the most complex subsystem. It extracts structured game state from raw screenshots.

**OCR (`ocr.py`):**

- Uses Tesseract via `pytesseract` to read text from calibrated screen regions
- Extracts: turn number, star count, star income, score, city names/levels, popup text
- Pre-processes images (grayscale, threshold, scale) for OCR accuracy
- Region coordinates come from `calibration.json`

**Tile classifier (`tile_classifier.py`):**

- Uses OpenCV template matching (`cv2.matchTemplate`) against reference tile images
- Classifies visible tiles: ground, forest, mountain, water, ocean, ice, fungus, etc.
- Detects resources on tiles: fruit, crop, fish, whale, animal, metal, starfish
- Detects improvements: farm, mine, lumber hut, sawmill, windmill, forge, port, customs house, temple variants
- Uses tribe color detection (HSV color ranges per tribe) to identify ownership
- Confidence thresholds per template to handle false matches
- Reference templates stored in `vision/templates/` -- initially manually captured, later expanded

**Unit detector (`unit_detector.py`):**

- Template matching for unit sprites: warrior, rider, archer, defender, knight, catapult, swordsman, mind bender, giant, battleship, bomber, scout, cloak, rammer
- Special tribe units: polytaur, navalon, tridention, battle sled, ice archer, mooni, ice fortress, gaami, hexapod, kiton, phychi, raychi, doomux, shaman, exida
- Detect unit health bars (color + width analysis) for current HP
- Detect veteran stars
- Determine unit ownership via tribe color of the unit base

**Grid mapper (`grid_mapper.py`):**

- Maps pixel coordinates to tile grid coordinates using calibration parameters
- Handles the isometric tile grid (Polytopia uses a square grid rendered isometrically)
- Key calibration values: grid origin (pixel pos of tile 0,0), dx/dy (tile spacing), rows/cols
- Inverse mapping: given a tile coordinate, return the screen pixel center (for overlay drawing)
- Must handle camera scroll position -- detect via known landmarks or relative positioning

**Tech tree reader (`tech_tree_reader.py`):**

- When the tech tree is open (detected by presence of the tech tree UI), capture and analyze it
- Use template matching for tech icons in researched vs. unresearched state (color difference: researched techs are highlighted/colored, unresearched are greyed/outlined)
- Map detected icons to the structured tech tree data in `knowledge/tech_tree.py`
- Update the persistent game state tracker

### 3. Game State Models (`state/`)

**Core models (`models.py`)** using Pydantic:

```python
from pydantic import BaseModel
from enum import Enum

class TileType(str, Enum):
    GROUND = "ground"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    WATER = "water"
    OCEAN = "ocean"
    ICE = "ice"
    # ...

class ResourceType(str, Enum):
    FRUIT = "fruit"
    CROP = "crop"
    ANIMAL = "animal"
    FISH = "fish"
    WHALE = "whale"
    METAL = "metal"
    STARFISH = "starfish"
    # ...

class UnitType(str, Enum):
    WARRIOR = "warrior"
    RIDER = "rider"
    ARCHER = "archer"
    DEFENDER = "defender"
    KNIGHT = "knight"
    CATAPULT = "catapult"
    SWORDSMAN = "swordsman"
    MIND_BENDER = "mind_bender"
    GIANT = "giant"
    BATTLESHIP = "battleship"
    BOMBER = "bomber"
    SCOUT = "scout"
    CLOAK = "cloak"
    RAMMER = "rammer"
    # Special tribe units...

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
```

**State tracker (`tracker.py`):**

- Maintains persistent `GameState` across frames
- Merges new observations into existing state (handles partial visibility)
- Tracks fog of war: tiles once seen but now hidden are remembered
- Detects turn changes (turn number increment) to trigger full re-analysis
- Logs state history per turn for learning system (Phase 5)

### 4. Knowledge Base (`knowledge/`)

`**tech_tree.json` -- Complete tech tree encoded as a directed graph:

```json
{
  "climbing": {
    "tier": 1,
    "branch": "climbing",
    "cost_formula": "1 * cities + 4",
    "prerequisites": [],
    "unlocks": ["mountain_movement", "mountain_defense", "see_metal"],
    "leads_to": ["mining", "meditation"],
    "starting_tech_of": ["xin-xi"]
  },
  "mining": {
    "tier": 2,
    "branch": "climbing",
    "cost_formula": "2 * cities + 4",
    "prerequisites": ["climbing"],
    "unlocks": ["mine"],
    "leads_to": ["smithery"],
    "starting_tech_of": []
  }
  // ... all 30+ technologies
}
```

`**units.json**` -- Full unit stats:

```json
{
  "warrior": {
    "attack": 2,
    "defense": 2,
    "movement": 1,
    "range": 1,
    "max_health": 10,
    "cost": 2,
    "skills": ["dash"],
    "unlocked_by": null,
    "notes": "Starting unit for all tribes"
  },
  "rider": {
    "attack": 2,
    "defense": 1,
    "movement": 2,
    "range": 1,
    "max_health": 10,
    "cost": 3,
    "skills": ["dash", "escape", "fortify"],
    "unlocked_by": "riding"
  }
  // ... all units including special tribe variants
}
```

`**tribes.json**` -- Tribe metadata including color palettes for CV detection:

```json
{
  "bardur": {
    "starting_tech": "hunting",
    "special_units": [],
    "color_primary_hsv": [20, 80, 60],
    "color_range_hsv": [
      [15, 50, 40],
      [25, 100, 80]
    ],
    "terrain_bias": "forest_heavy",
    "t0_capable": true
  }
  // ... all 16 tribes
}
```

`**tribe_strategies.json**` -- Opening sequences, benchmarks, decision heuristics:

```json
{
  "bardur": {
    "opening_sequence": [
      "Turn 0: Upgrade capital via hunting (if 2+ animals visible)",
      "Turn 1: Train warrior OR explorer depending on neighbor proximity",
      "Turn 2-3: Research forestry -> lumber huts for economy"
    ],
    "ideal_star_income": { "turn_5": 8, "turn_10": 15, "turn_15": 25 },
    "tech_paths": {
      "economy_focus": ["hunting", "forestry", "mathematics"],
      "military_rush": ["hunting", "free_spirit", "chivalry"],
      "balanced": ["hunting", "forestry", "organization", "strategy"]
    },
    "key_decisions": {
      "knights_vs_catapults": "Knights if enemy has many small units; catapults if enemy has fortified cities",
      "expand_vs_military": "Expand if no enemy contact by turn 5; military if border contact"
    }
  }
}
```

### 5. LLM Interface (`llm/`)

Provider-agnostic interface ready for Phase 3 advisory:

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def analyze_text(self, prompt: str) -> str:
        """Send text prompt, get text response."""
        ...

    @abstractmethod
    async def analyze_image(self, image: bytes, prompt: str) -> str:
        """Send image + text prompt, get text response (vision models)."""
        ...

    @property
    @abstractmethod
    def supports_vision(self) -> bool: ...
```

Three implementations: `OpenAIProvider`, `AnthropicProvider`, `OllamaProvider`. Config via env vars or `config.json`.

**Prompt builder (`prompt_builder.py`):** Serializes `GameState` + relevant knowledge context into structured prompts. Designed for Phase 3 but built now so the data contract is locked.

### 6. Overlay (`overlay/`)

Minimal PyQt6 transparent overlay as proof of concept:

- Frameless, always-on-top, click-through transparent window
- Positioned to match the Polytopia window bounds
- Renders extracted game state as debug text: turn number, stars, detected tribe, number of units/cities, tile counts
- Future phases will render move arrows, tech path highlights, threat indicators
- Toggle visibility via global hotkey (F1)
- Separate render thread to avoid blocking the CV pipeline

### 7. Calibration System

`**calibration_template.json` follows the same schema as `polytopia-bench` for compatibility:

```json
{
  "window_title": "The Battle of Polytopia",
  "tesseract_cmd": "C:/Program Files/Tesseract-OCR/tesseract.exe",
  "regions": {
    "turn": [x, y, w, h],
    "stars": [x, y, w, h],
    "score": [x, y, w, h],
    "map": [x, y, w, h]
  },
  "tile_grid": {
    "origin": [x, y],
    "dx": 64,
    "dy": 56,
    "rows": 11,
    "cols": 11
  },
  "resolution": [1920, 1080]
}
```

`**tools/calibration_wizard.py`: Interactive tool that:

1. Captures the game window
2. Asks user to click on key reference points (tile origin, UI elements)
3. Auto-detects grid spacing from click patterns
4. Saves `calibration.json`

### 8. Main Loop (`main.py`)

```python
async def main():
    config = load_config()
    capture = create_capture_backend(config)
    vision = VisionPipeline(config)
    tracker = GameStateTracker()
    overlay = OverlayWindow()
    change_detector = ChangeDetector(threshold=0.05)

    overlay.start()  # launch overlay in separate thread

    while True:
        frame = capture.grab()
        if not change_detector.has_changed(frame):
            await asyncio.sleep(0.5)
            continue

        raw_state = vision.extract(frame)
        game_state = tracker.update(raw_state)
        overlay.update(game_state)

        await asyncio.sleep(1.0)  # poll rate for turn-based game
```

---

## Key Design Decisions

- **polytopia-bench compatibility:** Use the same calibration schema so users who already have `polytopia-bench` calibrated can reuse their config
- **Stateful tracking:** The `GameStateTracker` accumulates observations across frames -- it remembers tiles you've seen even if they're now in fog of war
- **Confidence scoring:** Every extraction result carries a confidence float so downstream consumers (the LLM in Phase 3) know what the system is uncertain about
- **Template-based CV over ML:** Template matching is deterministic, debuggable, and doesn't need training data. Fine for Polytopia's consistent pixel art style. ML-based detection can be added later if needed
- **Async architecture:** The main loop, LLM calls, and overlay rendering are all async/threaded to keep the system responsive

---

## Existing Resources to Leverage

- `**polytopia-bench` (PyPI): Screen capture patterns, OCR approach, calibration schema, action schema. Don't take a dependency on it directly (it's designed as a benchmark runner, not a library), but mirror its calibration format and study its CV approach
- **GAIGResearch/Tribes (GitHub, Java):** Open-source Polytopia clone with a forward model. Useful reference for game mechanics encoding (tech tree, unit stats, combat formulas). Could be used in Phase 6 for RL training
- **Polytopia Wiki (Fandom):** Primary source for all game data (tech costs, unit stats, tribe info). The knowledge base JSON files should be comprehensive extractions from the wiki

---

## What This Phase Does NOT Include (Deferred to Later Phases)

- LLM-powered move suggestions (Phase 3)
- Rich HUD with move arrows and tech path overlays (Phase 4)
- Game history database and cross-game learning (Phase 5)
- Model fine-tuning or reinforcement learning (Phase 6)
- Mobile/Android screen capture via ADB (deferred -- Windows/Steam first)
