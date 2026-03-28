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

        self._loop_count = 0
        self._debug_screenshot_saved = False

        try:
            while self.is_running:
                self._loop_count += 1

                # Wait for the game window before doing anything
                window_rect = self.capture.find_game_window()
                if not window_rect:
                    if self._loop_count % 5 == 1:
                        logger.info("Waiting for Polytopia window...")
                    await asyncio.sleep(2.0)
                    continue

                logger.info(f"[Loop {self._loop_count}] Window found: {window_rect}")

                frame = self.capture.grab()
                if frame is None or frame.shape[0] <= 1:
                    logger.warning(f"[Loop {self._loop_count}] Capture returned empty frame")
                    await asyncio.sleep(settings.poll_rate)
                    continue

                logger.info(f"[Loop {self._loop_count}] Frame captured: {frame.shape} (h x w x channels)")

                # Save one debug screenshot so we can inspect what was captured
                if not self._debug_screenshot_saved:
                    try:
                        import cv2
                        cv2.imwrite("debug_capture.png", frame)
                        logger.info("Saved debug screenshot to debug_capture.png")
                        self._debug_screenshot_saved = True
                    except Exception as e:
                        logger.warning(f"Could not save debug screenshot: {e}")

                changed = self.change_detector.has_changed(frame)
                if not changed:
                    logger.debug(f"[Loop {self._loop_count}] No screen change detected, skipping")
                    await asyncio.sleep(settings.poll_rate)
                    continue

                logger.info(f"[Loop {self._loop_count}] Screen change detected, running vision pipeline...")

                # Vision extraction pipeline
                stats = {}
                tiles = []
                units = []
                researched_techs = []

                try:
                    stats = self.ocr.extract_game_stats(frame)
                    logger.info(f"[Loop {self._loop_count}] OCR stats: {stats}")
                except Exception as e:
                    logger.warning(f"[Loop {self._loop_count}] OCR failed: {e}")

                try:
                    tiles = self.tile_classifier.extract_all_tiles(frame)
                    tile_types = {}
                    for t in tiles:
                        tile_types[t.tile_type] = tile_types.get(t.tile_type, 0) + 1
                    logger.info(f"[Loop {self._loop_count}] Tiles: {len(tiles)} total, types: {tile_types}")
                except Exception as e:
                    logger.warning(f"[Loop {self._loop_count}] Tile classification failed: {e}")

                try:
                    units = self.unit_detector.detect_units(frame)
                    logger.info(f"[Loop {self._loop_count}] Units detected: {len(units)}")
                    for u in units:
                        logger.info(f"  -> {u.unit_type} at ({u.position.x},{u.position.y}) tribe={u.owner_tribe} hp={u.health:.1f}")
                except Exception as e:
                    logger.warning(f"[Loop {self._loop_count}] Unit detection failed: {e}")

                try:
                    researched_techs = self.tech_reader.get_researched_techs(frame)
                    logger.info(f"[Loop {self._loop_count}] Techs detected: {researched_techs}")
                except Exception as e:
                    logger.warning(f"[Loop {self._loop_count}] Tech reading failed: {e}")

                # Construct raw state
                turn_val = int(stats.get("turn", "0") or "0")
                stars_val = int(stats.get("stars", "0") or "0")
                score_val = int(stats.get("score", "0") or "0")

                raw_state = GameState(
                    turn=turn_val,
                    stars=stars_val,
                    star_income=0,
                    score=score_val,
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

                logger.info(f"[Loop {self._loop_count}] State: turn={turn_val} stars={stars_val} score={score_val} tiles={len(tiles)} units={len(units)} techs={len(researched_techs)}")

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
