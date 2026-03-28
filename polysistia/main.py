import asyncio
import signal
import logging
import os
import sys
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from .config import settings
from .capture.dxcam_backend import DXCamBackend
from .capture.mss_backend import MSSBackend
from .vision.ocr import OCR
from .vision.change_detector import ChangeDetector
from .vision.grid_mapper import GridMapper
from .vision.tile_classifier import TileClassifier
from .vision.unit_detector import UnitDetector
from .vision.tech_tree_reader import TechTreeReader
from .state.tracker import GameStateTracker
from .state.models import GameState, Position
from .overlay.overlay_window import OverlayWindow
from .utils.logging import setup_logging

logger = setup_logging(settings.log_level)

class Polysistia:
    def __init__(self, overlay_window: OverlayWindow):
        self.calibration = settings.load_calibration()

        # Capture Backend with fallback
        try:
            self.capture = DXCamBackend(self.calibration.window_title)
            logger.info("Using DXCam backend.")
        except Exception as e:
            logger.warning(f"DXCam failed: {e}. Falling back to MSS.")
            self.capture = MSSBackend(self.calibration.window_title)

        self.grid_mapper = GridMapper(self.calibration)
        self.ocr = OCR(self.calibration)
        self.change_detector = ChangeDetector(settings.change_threshold)
        self.tracker = GameStateTracker()

        # Absolute path for templates
        templates_dir = os.path.join(os.path.dirname(__file__), "vision", "templates")
        self.tile_classifier = TileClassifier(self.calibration, self.grid_mapper, templates_dir)
        self.unit_detector = UnitDetector(self.calibration, self.grid_mapper, templates_dir)
        self.tech_reader = TechTreeReader(self.calibration, templates_dir)

        self.overlay = overlay_window
        self.is_running = False

    async def start(self):
        logger.info("Starting Polysistia...")
        self.is_running = True

        try:
            while self.is_running:
                # Wait for the game window before doing anything
                window_rect = self.capture.find_game_window()
                if not window_rect:
                    logger.debug("Waiting for Polytopia window...")
                    await asyncio.sleep(2.0)
                    continue

                frame = self.capture.grab()
                if frame is None or frame.shape[0] <= 1:
                    await asyncio.sleep(settings.poll_rate)
                    continue

                if not self.change_detector.has_changed(frame):
                    await asyncio.sleep(settings.poll_rate)
                    continue

                # Vision extraction pipeline
                try:
                    stats = self.ocr.extract_game_stats(frame)
                    tiles = self.tile_classifier.extract_all_tiles(frame)
                    units = self.unit_detector.detect_units(frame)
                    researched_techs = self.tech_reader.get_researched_techs(frame)
                except Exception as e:
                    logger.warning(f"Vision extraction error: {e}")
                    await asyncio.sleep(settings.poll_rate)
                    continue

                # Construct raw state
                raw_state = GameState(
                    turn=int(stats.get("turn", "0") or "0"),
                    stars=int(stats.get("stars", "0") or "0"),
                    star_income=0,
                    score=int(stats.get("score", "0") or "0"),
                    player_tribe="bardur",
                    cities=[],
                    units=units,
                    enemy_units=[],
                    enemy_cities=[],
                    visible_tiles=tiles,
                    fog_tiles=[],
                    researched_techs=researched_techs,
                    game_mode="domination",
                    confidence=1.0
                )

                # Update persistent state
                current_state = self.tracker.update(raw_state)

                # Update overlay safely via signal
                self.overlay.state_updated.emit(current_state)

                await asyncio.sleep(settings.poll_rate)
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        logger.info("Stopping Polysistia...")
        self.is_running = False

def main():
    qt_app = QApplication(sys.argv)
    loop = QEventLoop(qt_app)
    asyncio.set_event_loop(loop)

    overlay = OverlayWindow()
    overlay.show()

    polysistia = Polysistia(overlay)

    # Handle shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *args: polysistia.stop())

    try:
        loop.run_until_complete(polysistia.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == "__main__":
    main()
