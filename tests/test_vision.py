import pytest
from polysistia.vision.ocr import OCR
from polysistia.config import Calibration, TileGrid
import numpy as np

def test_ocr_extraction_dummy():
    # Placeholder for OCR test with a mock frame
    calibration = Calibration(
        window_title="Test",
        regions={"turn": [0, 0, 10, 10], "stars": [0, 0, 10, 10], "score": [0, 0, 10, 10]},
        tile_grid=TileGrid(origin=(0, 0)),
        tesseract_cmd="tesseract"
    )

    ocr = OCR(calibration)

    # Create empty frame
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # stats should return 0 by default when no text is found
    # stats = ocr.extract_game_stats(frame)
    # assert stats["turn"] == "0"
    # assert stats["stars"] == "0"
    # assert stats["score"] == "0"
    pass

def test_tile_classifier_dummy():
    from polysistia.vision.tile_classifier import TileClassifier
    from polysistia.vision.grid_mapper import GridMapper

    calibration = Calibration(
        window_title="Test",
        regions={"map": [0, 0, 100, 100]},
        tile_grid=TileGrid(origin=(0, 0)),
        resolution=(100, 100)
    )
    mapper = GridMapper(calibration)
    classifier = TileClassifier(calibration, mapper, "dummy_templates")

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    tile = classifier.classify_tile(frame, 0, 0)

    assert tile.position.x == 0
    assert tile.position.y == 0
    assert tile.tile_type == "ground"
