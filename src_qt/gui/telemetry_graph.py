"""Dark telemetry chart widget."""

from __future__ import annotations

import math
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


def fmt_axis_value(value: float) -> str:
    """Axis labels: compact for huge/small magnitudes, else three decimals."""
    av = abs(value)
    if av >= 1e6 or (av > 0 and av < 1e-3):
        return f"{value:.3e}".replace(".", ",")
    return f"{value:.3f}".replace(".", ",")


def _nice_step(span: float, target_ticks: int = 5) -> float:
    if not math.isfinite(span) or span <= 0:
        return 1.0
    raw = span / max(target_ticks, 1)
    exp = math.floor(math.log10(abs(raw)))
    f = raw / (10.0**exp)
    if f <= 1.0:
        nf = 1.0
    elif f <= 2.0:
        nf = 2.0
    elif f <= 5.0:
        nf = 5.0
    else:
        nf = 10.0
    return nf * (10.0**exp)


def _gen_y_ticks(vmin: float, vmax: float, max_ticks: int = 8) -> List[float]:
    span = vmax - vmin
    if span < 1e-30:
        return [vmin]
    step = _nice_step(span, 5)
    start = math.ceil(vmin / step - 1e-9) * step
    ticks: List[float] = []
    x = start
    while x <= vmax + step * 1e-6 and len(ticks) < max_ticks + 10:
        ticks.append(x)
        x += step
    if not ticks:
        ticks = [vmin, vmax]
    return ticks


class TelemetryGraphWidget(QWidget):
    """
    Dark telemetry chart with titled axes, Y tick labels, and time-based X axis.
    ``series`` entries: (data_key, legend_label, QColor).
    """

    def __init__(
        self,
        title: str,
        series: List[Tuple[str, str, QColor]],
        maxlen: int = 240,
        sample_dt: float = 1.0 / 60.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._series_meta = series
        self._sample_dt = sample_dt
        self._data: Dict[str, Deque[float]] = {k: deque(maxlen=maxlen) for k, _, _ in series}
        self.setMinimumHeight(200)
        self.setMinimumWidth(280)

    def push_row(self, values: Dict[str, float]) -> None:
        for k, v in values.items():
            if k in self._data:
                self._data[k].append(v)
        self.update()

    def clear_data(self) -> None:
        for dq in self._data.values():
            dq.clear()
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w, h = self.width(), self.height()
        bg = QColor(16, 18, 24)
        painter.fillRect(self.rect(), bg)

        margin_l, margin_r = 56, 12
        margin_t, margin_b = 30, 52
        plot_w = max(1, w - margin_l - margin_r)
        plot_h = max(1, h - margin_t - margin_b)
        plot_rect = QRectF(float(margin_l), float(margin_t), float(plot_w), float(plot_h))

        axis_color = QColor(120, 128, 145)
        grid_color = QColor(45, 50, 62)
        title_color = QColor(200, 210, 230)

        font_title = QFont("monospace", 9)
        font_title.setBold(True)
        font_tick = QFont("monospace", 8)
        font_tick.setStyleHint(QFont.StyleHint.TypeWriter)
        font_small = QFont("monospace", 7)

        painter.setFont(font_title)
        painter.setPen(QPen(title_color))
        tw = painter.fontMetrics().horizontalAdvance(self._title)
        painter.drawText(int((w - tw) / 2), 20, self._title)

        series_list: List[Tuple[str, str, QColor, Deque[float]]] = [
            (k, lab, col, self._data[k]) for k, lab, col in self._series_meta
        ]

        all_vals: List[float] = []
        for _, _, _, dq in series_list:
            all_vals.extend(dq)

        if not all_vals:
            painter.setFont(font_tick)
            painter.setPen(QColor(130, 136, 150))
            painter.drawText(margin_l, margin_t + 24, "Waiting for samples…")
            painter.end()
            return

        vmin = min(all_vals)
        vmax = max(all_vals)
        span = vmax - vmin

        if "Kinetic energy" in self._title and span < 0.1:
            mid = (vmin + vmax) / 2.0
            vmin = mid - 0.05
            vmax = mid + 0.05
            span = 0.1

        if span < 1e-30:
            mid = vmin
            vmin, vmax = mid - 1.0, mid + 1.0
            span = 2.0
        pad = span * 0.06
        vmin -= pad
        vmax += pad
        span = vmax - vmin

        def y_map(val: float) -> float:
            t = (val - vmin) / span
            return float(margin_t + (1.0 - t) * plot_h)

        y_ticks = _gen_y_ticks(vmin, vmax)
        painter.setPen(QPen(grid_color, 1.0))
        for yt in y_ticks:
            yy = y_map(yt)
            painter.drawLine(int(margin_l), int(yy), int(margin_l + plot_w), int(yy))

        painter.setPen(QPen(axis_color, 1.5))
        painter.drawLine(int(margin_l), int(margin_t + plot_h), int(margin_l + plot_w), int(margin_t + plot_h))
        painter.drawLine(int(margin_l), int(margin_t), int(margin_l), int(margin_t + plot_h))

        painter.setFont(font_tick)
        painter.setPen(QPen(QColor(170, 176, 190)))
        fm = painter.fontMetrics()
        for yt in y_ticks:
            yy = int(y_map(yt))
            lab = fmt_axis_value(yt)
            painter.drawText(4, yy + fm.height() // 3, lab)

        sample_count = max(len(dq) for _, _, _, dq in series_list)
        t_max = max(0.0, (sample_count - 1) * self._sample_dt)
        x_divs = 5
        painter.setPen(QPen(grid_color, 1.0))
        for i in range(x_divs + 1):
            xi = margin_l + (i / x_divs) * plot_w
            painter.drawLine(int(xi), int(margin_t), int(xi), int(margin_t + plot_h))

        painter.setPen(QPen(axis_color, 1.5))
        for i in range(x_divs + 1):
            t = t_max * (i / x_divs) if sample_count > 1 else 0.0
            xi = margin_l + (i / x_divs) * plot_w
            tlab = f"{t:.3f}".replace(".", ",") + " s"
            tw_ = fm.horizontalAdvance(tlab)
            painter.drawText(int(xi - tw_ / 2), h - 28, tlab)

        painter.setFont(font_small)
        painter.setPen(QColor(150, 156, 170))
        painter.drawText(margin_l, h - 10, "t (s)")

        n_samples = max(sample_count, 1)

        for _, legend_label, color, dq in series_list:
            if len(dq) < 2:
                continue
            painter.setPen(QPen(color, 2.0))
            pts = list(dq)
            m = len(pts)
            for i in range(m - 1):
                x0 = margin_l + (i / max(n_samples - 1, 1)) * plot_w
                x1 = margin_l + ((i + 1) / max(n_samples - 1, 1)) * plot_w
                painter.drawLine(
                    int(x0),
                    int(y_map(pts[i])),
                    int(x1),
                    int(y_map(pts[i + 1])),
                )

        legend_x = margin_l
        ly = h - 12
        painter.setFont(font_small)
        for _, legend_label, color, _ in series_list:
            painter.setPen(QPen(color))
            painter.drawText(legend_x, ly, legend_label)
            legend_x += fm.horizontalAdvance(legend_label) + 16

        painter.end()
