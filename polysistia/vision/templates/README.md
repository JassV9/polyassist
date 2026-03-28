# Vision Templates

These directories hold reference PNG images for OpenCV template matching.
Templates are NOT included in git -- you capture them from your own game.

## How to capture templates

1. Run Polytopia and start a game (Creative mode with all techs is ideal)
2. Run: `python tools/template_capture.py`
3. The tool will take a screenshot and let you crop regions
4. Save crops into the correct subdirectory below

## Directory structure

- `tiles/` - Tile types: `ground.png`, `forest.png`, `mountain.png`, `water.png`, `ocean.png`, `ice.png`
- `units/` - Unit sprites: `warrior.png`, `rider.png`, `archer.png`, `knight.png`, etc.
- `buildings/` - Building sprites: `farm.png`, `mine.png`, `lumber_hut.png`, `port.png`, etc.
- `resources/` - Resource sprites: `fruit.png`, `crop.png`, `animal.png`, `fish.png`, `metal.png`
- `icons/` - UI icons: tech tree icons, star icon, etc.

## Naming convention

File names must match the enum values in `polysistia/state/models.py`.
For example, `forest.png` matches `TileType.FOREST = "forest"`.

## Recommended crop size

~60x60 to 80x80 pixels per template, centered on the feature.
