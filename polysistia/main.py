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
from .capture.window_finder import is_polytopia_foreground
from .vision.ocr import OCR
from .vision.change_detector import ChangeDetector
from .vision.grid_mapper import GridMapper
from .vision.tile_classifier import TileClassifier
from .vision.unit_detector import UnitDetector
from .vision.city_detector import CityDetector
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

        templates_dir = os.path.join(os.path.dirname(__file__), "vision", "templates")
        self.tile_classifier = TileClassifier(self.calibration, self.grid_mapper, templates_dir)
        self.unit_detector = UnitDetector(self.calibration, self.grid_mapper, templates_dir)
        self.tech_reader = TechTreeReader(self.calibration, templates_dir)
        self.city_detector = CityDetector(self.calibration)

        self.overlay = overlay_window
        self.is_running = False

    def _set_overlay_status(self, status: str):
        """Update the overlay HUD with a status message."""
        self.overlay.status_updated.emit(status)

    async def start(self):
        logger.info("Starting Polysistia...")
        self.is_running = True
        self._set_overlay_status("Starting up...")

        loop_count = 0
        debug_screenshot_saved = False
        last_status = ""

        try:
            while self.is_running:
                loop_count += 1

                # Step 1: Find the game window
                window_rect = self.capture.find_game_window()
                if not window_rect:
                    status = "Waiting for Polytopia window...\nMake sure the game is open (not minimized)."
                    if status != last_status:
                        self._set_overlay_status(status)
                        last_status = status
                        logger.info("Waiting for Polytopia window...")
                    await asyncio.sleep(2.0)
                    continue

                # Step 2: Check if game is in foreground
                fg = is_polytopia_foreground(self.calibration.window_title)
                if not fg:
                    status = (
                        f"Window found: {window_rect[2]}x{window_rect[3]}\n"
                        "Polytopia is NOT in foreground!\n"
                        "Click on the game window so I can see it."
                    )
                    if status != last_status:
                        self._set_overlay_status(status)
                        last_status = status
                        logger.info("Polytopia not in foreground, DXCam will capture wrong window")
                    await asyncio.sleep(1.0)
                    continue

                # Step 3: Grab frame
                frame = self.capture.grab()
                if frame is None or frame.shape[0] <= 1:
                    self._set_overlay_status("Capture returned empty frame...")
                    await asyncio.sleep(settings.poll_rate)
                    continue

                # Save first debug screenshot
                if not debug_screenshot_saved:
                    try:
                        import cv2
                        cv2.imwrite("debug_capture.png", frame)
                        logger.info(f"Saved debug screenshot: {frame.shape[1]}x{frame.shape[0]}")
                        debug_screenshot_saved = True
                    except Exception as e:
                        logger.warning(f"Could not save debug screenshot: {e}")

                # Step 4: Check for screen changes
                if not self.change_detector.has_changed(frame):
                    status = (
                        f"Connected: {frame.shape[1]}x{frame.shape[0]}\n"
                        f"Loop #{loop_count} - No change detected\n"
                        "Watching for game updates..."
                    )
                    if loop_count % 10 == 0 and status != last_status:
                        self._set_overlay_status(status)
                        last_status = status
                    await asyncio.sleep(settings.poll_rate)
                    continue

                # Step 5: Run vision pipeline
                self._set_overlay_status(
                    f"Connected: {frame.shape[1]}x{frame.shape[0]}\n"
                    f"Loop #{loop_count} - Analyzing..."
                )

                stats = {}
                tiles = []
                units = []
                all_cities = []
                researched_techs = []

                try:
                    stats = self.ocr.extract_game_stats(frame)
                    logger.info(f"[{loop_count}] OCR: {stats}")
                except Exception as e:
                    logger.warning(f"[{loop_count}] OCR failed: {e}")

                try:
                    tiles = self.tile_classifier.extract_all_tiles(frame)
                    tile_types = {}
                    for t in tiles:
                        tile_types[str(t.tile_type)] = tile_types.get(str(t.tile_type), 0) + 1
                    logger.info(f"[{loop_count}] Tiles: {len(tiles)} - {tile_types}")
                except Exception as e:
                    logger.warning(f"[{loop_count}] Tile classification failed: {e}")

                try:
                    units = self.unit_detector.detect_units(frame)
                    logger.info(f"[{loop_count}] Units: {len(units)}")
                except Exception as e:
                    logger.warning(f"[{loop_count}] Unit detection failed: {e}")

                try:
                    all_cities = self.city_detector.detect_cities(frame)
                    logger.info(f"[{loop_count}] Cities: {len(all_cities)}")
                except Exception as e:
                    logger.warning(f"[{loop_count}] City detection failed: {e}")

                try:
                    researched_techs = self.tech_reader.get_researched_techs(frame)
                    logger.info(f"[{loop_count}] Techs: {researched_techs}")
                except Exception as e:
                    logger.warning(f"[{loop_count}] Tech reading failed: {e}")

                turn_val = int(stats.get("turn", "0") or "0")
                stars_val = int(stats.get("stars", "0") or "0")
                score_val = int(stats.get("score", "0") or "0")
                star_income_val = int(stats.get("star_income", "0") or "0")

                # Split cities into player-owned and enemy-owned
                player_tribe = self.calibration.player_tribe
                player_cities = [c for c in all_cities if c.owner_tribe == player_tribe]
                enemy_cities = [c for c in all_cities if c.owner_tribe != player_tribe]

                # Split units into player and enemy by tribe
                player_units = [u for u in units if u.owner_tribe == player_tribe or u.owner_tribe == "unknown"]
                enemy_units = [u for u in units if u.owner_tribe != player_tribe and u.owner_tribe != "unknown"]

                raw_state = GameState(
                    turn=turn_val,
                    stars=stars_val,
                    star_income=star_income_val,
                    score=score_val,
                    player_tribe=player_tribe,
                    cities=player_cities,
                    units=player_units,
                    enemy_units=enemy_units,
                    enemy_cities=enemy_cities,
                    visible_tiles=tiles,
                    fog_tiles=[],
                    researched_techs=researched_techs,
                    game_mode="domination",
                    confidence=1.0
                )

                logger.info(
                    f"[{loop_count}] State: turn={turn_val} stars={stars_val} "
                    f"income={star_income_val} score={score_val} "
                    f"tiles={len(tiles)} units={len(player_units)}+{len(enemy_units)}e "
                    f"cities={len(player_cities)}+{len(enemy_cities)}e"
                )

                current_state = self.tracker.update(raw_state)
                self.overlay.state_updated.emit(current_state)

                await asyncio.sleep(settings.poll_rate)
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            self._set_overlay_status(f"ERROR: {e}")
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
