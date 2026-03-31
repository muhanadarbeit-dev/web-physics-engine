"""Main window: composes simulation canvas, controls, and graphs."""

from __future__ import annotations

from typing import Tuple

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..physics.engine import PhysicsEngine
from .simulation_view import SimulationWidget
from .telemetry_graph import TelemetryGraphWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("2D Rigid Body Physics — PyQt6")
        self.resize(1180, 760)

        self._engine = PhysicsEngine()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        left_col = QVBoxLayout()
        self._sim = SimulationWidget(self._engine)
        left_col.addWidget(self._sim, stretch=1)
        left_col.addWidget(self._build_controls())
        root.addLayout(left_col, stretch=3)

        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        lbl_tel = QLabel("Telemetry")
        lbl_tel.setStyleSheet("font-weight: 600; font-size: 14px; color: #a8c7ff;")
        right_col.addWidget(lbl_tel)

        dt = self._sim.simulation_dt
        self._graph_ke = TelemetryGraphWidget(
            "Kinetic energy (J)",
            [("KE", "KE", QColor(255, 200, 80))],
            maxlen=300,
            sample_dt=dt,
        )
        self._graph_momentum = TelemetryGraphWidget(
            "Momentum (kg·m/s)",
            [
                ("Px", "Px", QColor(0, 230, 200)),
                ("Py", "Py", QColor(255, 90, 170)),
                ("|p|", "|p|", QColor(140, 180, 255)),
            ],
            maxlen=300,
            sample_dt=dt,
        )
        right_col.addWidget(self._graph_ke, stretch=1)
        right_col.addWidget(self._graph_momentum, stretch=1)
        root.addLayout(right_col, stretch=2)

        self._sim.telemetry_updated.connect(self._on_telemetry)
        self._sim.start()
        self._seed_initial_bodies()

    def _on_telemetry(self, px: float, py: float, p_mag: float, ke: float) -> None:
        self._graph_ke.push_row({"KE": ke})
        self._graph_momentum.push_row({"Px": px, "Py": py, "|p|": p_mag})

    def _create_prop_row(self, label: str, default_val: float, min_val: float, max_val: float, step: float = 1.0) -> Tuple[QWidget, QCheckBox, QDoubleSpinBox]:
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label)
        chk = QCheckBox("Random")
        chk.setChecked(True)
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setValue(default_val)
        spin.setEnabled(False)
        
        chk.toggled.connect(lambda c: spin.setEnabled(not c))
        
        lay.addWidget(lbl)
        lay.addWidget(spin)
        lay.addWidget(chk)
        lay.addStretch(1)
        return row, chk, spin

    def _build_controls(self) -> QGroupBox:
        box = QGroupBox("Control panel")
        main_lay = QVBoxLayout(box)

        # Buttons
        btn_row = QWidget()
        btn_lay = QHBoxLayout(btn_row)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        
        btn_ball = QPushButton("Add Ball")
        btn_poly = QPushButton("Add Polygon")
        btn_play = QPushButton("Play/Pause")
        btn_reset = QPushButton("Reset")

        btn_ball.clicked.connect(self._add_ball)
        btn_poly.clicked.connect(self._add_poly)
        btn_play.clicked.connect(self._toggle_play)
        btn_reset.clicked.connect(self._reset)

        btn_lay.addWidget(btn_ball)
        btn_lay.addWidget(btn_poly)
        btn_lay.addWidget(btn_play)
        btn_lay.addWidget(btn_reset)
        main_lay.addWidget(btn_row)

        # Property Rows
        prop_grid = QGridLayout()
        
        poly_label = QLabel("Polygon sides (3–25):")
        self._poly_random = QCheckBox("Random")
        self._poly_random.setChecked(True)
        self._poly_spin = QSpinBox()
        self._poly_spin.setRange(3, 25)
        self._poly_spin.setValue(6)
        self._poly_spin.setEnabled(False)

        def sync_polygon_mode() -> None:
            rnd = self._poly_random.isChecked()
            self._poly_spin.setEnabled(not rnd)
            self._sim.set_polygon_edge_mode(rnd, self._poly_spin.value())

        self._poly_random.toggled.connect(lambda _=False: sync_polygon_mode())
        self._poly_spin.valueChanged.connect(lambda _=0: sync_polygon_mode())
        sync_polygon_mode()

        poly_row = QWidget()
        pl = QHBoxLayout(poly_row)
        pl.setContentsMargins(0,0,0,0)
        pl.addWidget(poly_label)
        pl.addWidget(self._poly_spin)
        pl.addWidget(self._poly_random)
        pl.addStretch()
        
        prop_grid.addWidget(poly_row, 0, 0, 1, 2)

        r1, self._chk_rad_rnd, self._spin_rad = self._create_prop_row("Radius:", 20.0, 10.0, 100.0)
        r2, self._chk_spd_rnd, self._spin_spd = self._create_prop_row("Init Speed:", 100.0, 0.0, 500.0, 10.0)
        r3, self._chk_den_rnd, self._spin_den = self._create_prop_row("Density:", 1.0, 0.1, 10.0, 0.1)

        prop_grid.addWidget(r1, 1, 0)
        prop_grid.addWidget(r2, 1, 1)
        prop_grid.addWidget(r3, 2, 0, 1, 2)
        
        main_lay.addLayout(prop_grid)

        # Environment Controls
        env_grid = QGridLayout()
        g_down = QCheckBox("Gravity Down")
        g_up = QCheckBox("Gravity Up")
        g_left = QCheckBox("Gravity Left")
        g_right = QCheckBox("Gravity Right")

        g_down.setChecked(True)
        g_up.setChecked(False)
        g_left.setChecked(False)
        g_right.setChecked(False)

        g_down.toggled.connect(lambda c: setattr(self._engine, "gravity_down", c))
        g_up.toggled.connect(lambda c: setattr(self._engine, "gravity_up", c))
        g_left.toggled.connect(lambda c: setattr(self._engine, "gravity_left", c))
        g_right.toggled.connect(lambda c: setattr(self._engine, "gravity_right", c))

        env_grid.addWidget(g_down, 0, 0)
        env_grid.addWidget(g_up, 0, 1)
        env_grid.addWidget(g_left, 1, 0)
        env_grid.addWidget(g_right, 1, 1)

        elastic = QCheckBox("Elastic collisions (e = 1, conserve KE)")
        elastic.setChecked(True)
        elastic.toggled.connect(lambda c: setattr(self._engine, "elastic_collisions", c))
        env_grid.addWidget(elastic, 2, 0, 1, 2)
        
        main_lay.addLayout(env_grid)

        return box

    def _add_ball(self) -> None:
        r = None if self._chk_rad_rnd.isChecked() else self._spin_rad.value()
        s = None if self._chk_spd_rnd.isChecked() else self._spin_spd.value()
        d = None if self._chk_den_rnd.isChecked() else self._spin_den.value()
        self._sim.add_ball_at_random(radius=r, density=d, speed=s)

    def _add_poly(self) -> None:
        r = None if self._chk_rad_rnd.isChecked() else self._spin_rad.value()
        s = None if self._chk_spd_rnd.isChecked() else self._spin_spd.value()
        d = None if self._chk_den_rnd.isChecked() else self._spin_den.value()
        self._sim.add_polygon_at_random(radius=r, density=d, speed=s)

    def _toggle_play(self) -> None:
        self._sim.toggle_running()

    def _reset(self) -> None:
        self._engine.clear()
        self._graph_ke.clear_data()
        self._graph_momentum.clear_data()
        self._seed_initial_bodies()

    def _seed_initial_bodies(self) -> None:
        for _ in range(3):
            self._sim.add_ball_at_random()
        self._sim.add_polygon_at_random()
