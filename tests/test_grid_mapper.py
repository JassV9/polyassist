from polysistia.vision.grid_mapper import GridMapper
from polysistia.config import Calibration, TileGrid

def test_grid_mapping_conversions():
    # Use standard 1920x1080 calibration
    calibration = Calibration(
        window_title="Test",
        regions={"map": [0, 80, 1920, 920]},
        tile_grid=TileGrid(origin=(960, 540), dx=64, dy=56),
        resolution=(1920, 1080)
    )

    mapper = GridMapper(calibration)

    # Origin should be 0,0
    gx, gy = mapper.pixel_to_tile(960, 540)
    assert gx == 0
    assert gy == 0

    # Forward mapping test
    px, py = mapper.tile_to_pixel(1, 0)
    # x = (1-0)*64 + 960 = 1024
    # y = (1+0)*56 + 540 = 596
    assert px == 1024
    assert py == 596

    # Reverse mapping test
    gx2, gy2 = mapper.pixel_to_tile(1024, 596)
    assert gx2 == 1
    assert gy2 == 0

    # Diagonal test
    gx3, gy3 = mapper.pixel_to_tile(960, 540 + 56*2)
    # py = (gx+gy)*56 + 540 = 652 => gx+gy = 2
    # px = (gx-gy)*64 + 960 = 960 => gx-gy = 0
    # gx=1, gy=1
    assert gx3 == 1
    assert gy3 == 1
