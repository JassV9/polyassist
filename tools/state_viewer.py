from polysistia.capture.mss_backend import MSSBackend
from polysistia.vision.ocr import OCR
from polysistia.config import settings
from polysistia.state.serializer import GameStateSerializer
from polysistia.state.models import GameState
import json

def main():
    print("Polysistia State Viewer Diagnostic")
    print("-----------------------------------")

    calibration = settings.load_calibration()
    capture = MSSBackend(calibration.window_title)
    ocr = OCR(calibration)

    frame = capture.grab()
    stats = ocr.extract_game_stats(frame)

    print(f"Captured stats: {stats}")

    raw_state = GameState(
        turn=int(stats.get("turn", 0)),
        stars=int(stats.get("stars", 0)),
        star_income=0,
        score=int(stats.get("score", 0)),
        player_tribe="bardur",
        cities=[],
        units=[],
        enemy_units=[],
        enemy_cities=[],
        visible_tiles=[],
        fog_tiles=[],
        researched_techs=[],
        game_mode="domination",
        confidence=1.0
    )

    print("\nCompact Game State Summary:")
    print(GameStateSerializer.to_compact_text(raw_state))

if __name__ == "__main__":
    main()
