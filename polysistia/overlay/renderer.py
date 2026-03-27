from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRect
from ..state.models import GameState


class HUD_Renderer:
    def __init__(self, painter: QPainter):
        self.painter = painter

    def draw_game_state(self, state: GameState):
        self.painter.setPen(QPen(QColor(255, 255, 255), 2))
        self.painter.setFont(QFont("Arial", 14))

        # Turn
        self.painter.drawText(20, 40, f"Turn: {state.turn}")

        # Stars
        self.painter.drawText(20, 70, f"Stars: {state.stars} (+{state.star_income})")

        # Confidence
        self.painter.drawText(20, 100, f"Confidence: {state.confidence:.2f}")

    def draw_unit_marker(self, x: int, y: int, color: QColor):
        self.painter.setPen(QPen(color, 3))
        self.painter.drawEllipse(x - 10, y - 10, 20, 20)
