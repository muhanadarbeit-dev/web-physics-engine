"""Regular convex polygon rigid body."""

from __future__ import annotations

import math
import random
from typing import List, Tuple

from .body import RigidBody
from .math_utils import Vec2, rotate_vec


class PolygonBody(RigidBody):
    """
    Filled regular n-gon with given circumradius (center to vertex).
    Area: (n/2) R² sin(2π/n).
    Moment of inertia about center ⊥ plane: (m R² / 6) * (2 + cos(2π/n)).
    """

    __slots__ = ("num_edges", "circumradius", "_local_vertices")

    def __init__(
        self,
        x: float,
        y: float,
        circumradius: float,
        density: float,
        restitution: float,
        fill_rgb: Tuple[int, int, int],
        num_edges: int | None = None,
    ) -> None:
        super().__init__(x, y, density, restitution, fill_rgb)
        self.circumradius = circumradius
        self.num_edges = num_edges if num_edges is not None else random.randint(3, 25)
        self.num_edges = max(3, min(25, self.num_edges))
        self._local_vertices = self._build_local_vertices()
        self.compute_mass_properties()

    def _build_local_vertices(self) -> List[Vec2]:
        n = self.num_edges
        r = self.circumradius
        verts: List[Vec2] = []
        for k in range(n):
            t = 2.0 * math.pi * k / n - math.pi / 2.0
            verts.append((r * math.cos(t), r * math.sin(t)))
        return verts

    def area(self) -> float:
        n = self.num_edges
        r = self.circumradius
        return 0.5 * n * r * r * math.sin(2.0 * math.pi / n)

    def compute_mass_properties(self) -> None:
        self.mass = self.area() * self.density
        n = self.num_edges
        r = self.circumradius
        cos_term = math.cos(2.0 * math.pi / n)
        self.inertia = (self.mass * r * r / 6.0) * (2.0 + cos_term)
        self._sync_inv()

    def bounding_radius(self) -> float:
        return self.circumradius

    def get_world_vertices(self) -> List[Vec2]:
        out: List[Vec2] = []
        for lx, ly in self._local_vertices:
            wx, wy = rotate_vec((lx, ly), self.angle)
            out.append((self.x + wx, self.y + wy))
        return out

    def shape_type(self) -> str:
        return "polygon"

