"""Simulation canvas widget and overlay."""

from __future__ import annotations

import math
import random
from typing import Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..physics.ball import Ball
from ..physics.engine import PhysicsEngine
from ..physics.polygon import PolygonBody


def density_to_rgb(density: float) -> Tuple[int, int, int]:
    import colorsys
    min_d, max_d = 0.1, 10.0
    val = max(0.0, min(1.0, (density - min_d) / (max_d - min_d)))
    
    # قوس المطر (Rainbow): الأزرق=240, الأحمر=0
    hue = (240.0 - val * 240.0) / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.6, 0.9)
    return (int(r * 255), int(g * 255), int(b * 255))


def random_fill_rgb() -> Tuple[int, int, int]:
    return (random.randint(40, 220), random.randint(40, 220), random.randint(40, 220))


def fmt_float_hud(value: float) -> str:
    """Three fractional digits, comma as decimal separator (European style)."""
    return f"{value:.3f}".replace(".", ",")


class SimulationWidget(QWidget):
    """60 FPS physics canvas with walls, telemetry overlay, and body rendering."""

    telemetry_updated = pyqtSignal(float, float, float, float)  # px, py, |p|, ke

    def __init__(self, engine: PhysicsEngine, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._dt = 1.0 / 60.0
        self._running = True
        self._poly_random_edges: bool = True
        self._poly_num_edges: int = 6
        self.setMinimumSize(640, 480)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_polygon_edge_mode(self, random_edges: bool, num_edges: int) -> None:
        self._poly_random_edges = random_edges
        self._poly_num_edges = max(3, min(25, int(num_edges)))

    def is_running(self) -> bool:
        return self._running

    def toggle_running(self) -> None:
        self._running = not self._running

    def start(self) -> None:
        self._timer.start(int(self._dt * 1000))

    def stop_timer(self) -> None:
        self._timer.stop()

    def set_running(self, running: bool) -> None:
        self._running = running

    @property
    def simulation_dt(self) -> float:
        return self._dt

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._engine.set_world_size(float(self.width()), float(self.height()))

    def _tick(self) -> None:
        if self._running:
            self._engine.step(self._dt)
        px, py = self._engine.total_linear_momentum()
        p_mag = self._engine.scalar_momentum()
        ke = self._engine.total_kinetic_energy()
        self.telemetry_updated.emit(px, py, p_mag, ke)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(28, 30, 36))

        outline_pen = QPen(QColor(255, 255, 255))
        outline_pen.setWidthF(1.5)
        painter.setPen(outline_pen)

        for body in self._engine.bodies:
            r, g, b = body.fill_rgb
            painter.setBrush(QColor(r, g, b))
            if isinstance(body, Ball):
                d = 2.0 * body.radius
                painter.drawEllipse(QRectF(body.x - body.radius, body.y - body.radius, d, d))
            elif isinstance(body, PolygonBody):
                verts = body.get_world_vertices()
                if len(verts) >= 3:
                    qpts = [QPointF(v[0], v[1]) for v in verts]
                    painter.drawPolygon(qpts)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(90, 95, 110), 2.0))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        px, py = self._engine.total_linear_momentum()
        p_mag = self._engine.scalar_momentum()
        ke = self._engine.total_kinetic_energy()

        painter.setPen(QPen(QColor(220, 225, 235)))
        font = QFont("monospace", 10)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        painter.setFont(font)
        margin = 10
        lines = [
            f"Vector momentum: ({fmt_float_hud(px)}, {fmt_float_hud(py)}) kg·m/s | magnitude: {fmt_float_hud(p_mag)} kg·m/s",
            f"Total kinetic energy: {fmt_float_hud(ke)} J",
        ]
        y = margin + 14
        for line in lines:
            painter.drawText(margin, y, line)
            y += 16

        painter.end()

    def add_ball_at_random(self, radius: Optional[float] = None, density: Optional[float] = None, speed: Optional[float] = None) -> None:
        w, h = float(self.width()), float(self.height())
        r = radius if radius is not None else random.uniform(14.0, 28.0)
        d = density if density is not None else random.uniform(0.5, 3.0)
        x = random.uniform(r + 4, max(r + 8, w - r - 4))
        y = random.uniform(r + 4, max(r + 8, h - r - 4))
        ball = Ball(
            x,
            y,
            r,
            density=d,
            restitution=0.72,
            fill_rgb=density_to_rgb(d),
        )
        actual_speed = speed if speed is not None else random.uniform(50.0, 150.0)
        ang = random.uniform(0, 2 * math.pi)
        ball.vx = actual_speed * math.cos(ang)
        ball.vy = actual_speed * math.sin(ang)
        ball.angular_velocity = random.uniform(-4.0, 4.0)
        self._engine.add_body(ball)

    def add_polygon_at_random(self, radius: Optional[float] = None, density: Optional[float] = None, speed: Optional[float] = None) -> None:
        w, h = float(self.width()), float(self.height())
        rad = radius if radius is not None else random.uniform(22.0, 45.0)
        d = density if density is not None else random.uniform(0.5, 3.0)
        x = random.uniform(rad + 4, max(rad + 8, w - rad - 4))
        y = random.uniform(rad + 4, max(rad + 8, h - rad - 4))
        n_edges: Optional[int] = None if self._poly_random_edges else self._poly_num_edges
        poly = PolygonBody(
            x,
            y,
            rad,
            density=d,
            restitution=0.65,
            fill_rgb=density_to_rgb(d),
            num_edges=n_edges,
        )
        actual_speed = speed if speed is not None else random.uniform(50.0, 150.0)
        ang = random.uniform(0, 2 * math.pi)
        poly.vx = actual_speed * math.cos(ang)
        poly.vy = actual_speed * math.sin(ang)
        poly.angular_velocity = random.uniform(-3.5, 3.5)
        poly.angle = random.uniform(0.0, 2.0 * math.pi)
        self._engine.add_body(poly)
