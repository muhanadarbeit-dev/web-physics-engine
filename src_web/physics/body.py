"""Abstract rigid body base type for the 2D physics engine."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List, Tuple

from .math_utils import Vec2, vec_sub


class RigidBody(ABC):
    """Base rigid body: linear/angular kinematics and material properties."""

    __slots__ = (
        "x",
        "y",
        "vx",
        "vy",
        "angle",
        "angular_velocity",
        "mass",
        "inertia",
        "inv_mass",
        "inv_inertia",
        "restitution",
        "density",
        "fill_rgb",
    )

    def __init__(
        self,
        x: float,
        y: float,
        density: float,
        restitution: float,
        fill_rgb: Tuple[int, int, int],
    ) -> None:
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.density = density
        self.restitution = restitution
        self.fill_rgb = fill_rgb
        self.mass = 0.0
        self.inertia = 0.0
        self.inv_mass = 0.0
        self.inv_inertia = 0.0

    def _sync_inv(self) -> None:
        self.inv_mass = 1.0 / self.mass if self.mass > 1e-12 else 0.0
        self.inv_inertia = 1.0 / self.inertia if self.inertia > 1e-12 else 0.0

    @property
    def position(self) -> Vec2:
        return (self.x, self.y)

    def linear_velocity_at(self, world_point: Vec2) -> Vec2:
        r = vec_sub(world_point, self.position)
        rx, ry = r
        # v + ω×r where ω is scalar about +z.
        return (self.vx - self.angular_velocity * ry, self.vy + self.angular_velocity * rx)

    @abstractmethod
    def area(self) -> float:
        """Geometric area (uniform density)."""

    @abstractmethod
    def compute_mass_properties(self) -> None:
        """Set mass and inertia from area, density, and shape."""

    @abstractmethod
    def bounding_radius(self) -> float:
        """Maximum distance from position to any point on the shape (broad-phase)."""

    @abstractmethod
    def get_world_vertices(self) -> List[Vec2]:
        """Convex polygon vertices in world space (CCW). Empty or N/A for circles."""

    @abstractmethod
    def shape_type(self) -> str:
        """Discriminator for narrow-phase dispatch ('circle' | 'polygon')."""

