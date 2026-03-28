import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from ..state.models import GameState
from ..state.serializer import GameStateSerializer
import logging

logger = logging.getLogger(__name__)

class OverlayWindow(QMainWindow):
    state_updated = pyqtSignal(object)
    status_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.current_state = None
        self.state_updated.connect(self.update_state)
        self.status_updated.connect(self.update_status)

    def _setup_ui(self):
        # Frameless, transparent, always on top, click-through
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)

        self.info_label = QLabel("Polysistia HUD")
        self.info_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        self.info_label.setFont(QFont("Consolas", 12))

        self.layout.addWidget(self.info_label)
        self.setCentralWidget(self.central_widget)

        # Position top-right by default
        self.setGeometry(1500, 50, 400, 300)

    def update_state(self, state: GameState):
        self.current_state = state
        summary = GameStateSerializer.to_compact_text(state)
        self.info_label.setText(summary)

    def update_status(self, status: str):
        self.info_label.setText(f"[Polysistia]\n{status}")

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
