"""Circular rigid body."""

from __future__ import annotations

import math
from typing import List, Tuple

from .body import RigidBody
from .math_utils import Vec2


class Ball(RigidBody):
    """Uniform disk: mass and inertia from area πr²."""

    __slots__ = ("radius",)

    def __init__(
        self,
        x: float,
        y: float,
        radius: float,
        density: float,
        restitution: float,
        fill_rgb: Tuple[int, int, int],
    ) -> None:
        super().__init__(x, y, density, restitution, fill_rgb)
        self.radius = radius
        self.compute_mass_properties()

    def area(self) -> float:
        return math.pi * self.radius * self.radius

    def compute_mass_properties(self) -> None:
        self.mass = self.area() * self.density
        self.inertia = 0.5 * self.mass * self.radius * self.radius
        self._sync_inv()

    def bounding_radius(self) -> float:
        return self.radius

    def get_world_vertices(self) -> List[Vec2]:
        return []

    def shape_type(self) -> str:
        return "circle"

