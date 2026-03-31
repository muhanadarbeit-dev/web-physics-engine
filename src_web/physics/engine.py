"""
2D rigid-body physics engine: broad-phase, SAT narrow-phase, impulse resolution,
positional correction, directional gravity, and wall constraints.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Union

from .ball import Ball
from .body import RigidBody
from .collision import Contact, broad_phase, build_contact
from .math_utils import Vec2, vec_len
from .polygon import PolygonBody
from .resolution import NUM_SOLVER_ITERATIONS, positional_correction, resolve_impulse, resolve_walls

BodyType = Union[Ball, PolygonBody]


class PhysicsEngine:
    """
    Extensible physics world: register bodies, configure gravity axes, step simulation.
    New shapes: subclass RigidBody and register a collision resolver for new pairs.

    When ``elastic_collisions`` is True, normal restitution is forced to 1 during solving
    (elastic, frictionless model). Pairwise impulses conserve linear momentum; with e=1,
    kinetic energy is conserved for ideal contacts (small drift remains from positional
    correction and discrete time). Walls and gravity exchange momentum with the outside
    world, so total body momentum in the box is not conserved in those cases.
    """

    def __init__(self) -> None:
        self.bodies: List[BodyType] = []
        self.gravity_down: bool = True
        self.gravity_up: bool = False
        self.gravity_left: bool = False
        self.gravity_right: bool = False
        self.gravity_strength: float = 600.0
        self.world_width: float = 800.0
        self.world_height: float = 600.0
        self.elastic_collisions: bool = True
        self._custom_pair_resolvers: List[Callable[[RigidBody, RigidBody], Optional[Contact]]] = []

    def set_world_size(self, width: float, height: float) -> None:
        self.world_width = max(1.0, width)
        self.world_height = max(1.0, height)

    def add_body(self, body: BodyType) -> None:
        self.bodies.append(body)

    def clear(self) -> None:
        self.bodies.clear()

    def _gravity_accel(self) -> Vec2:
        ax = 0.0
        ay = 0.0
        g = self.gravity_strength
        if self.gravity_down:
            ay += g
        if self.gravity_up:
            ay -= g
        if self.gravity_left:
            ax -= g
        if self.gravity_right:
            ax += g
        return (ax, ay)

    def step(self, dt: float) -> None:
        ax, ay = self._gravity_accel()
        for b in self.bodies:
            b.vx += ax * dt
            b.vy += ay * dt
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.angle += b.angular_velocity * dt

        contacts: List[Contact] = []
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                bi, bj = self.bodies[i], self.bodies[j]
                if not broad_phase(bi, bj):
                    continue
                c: Optional[Contact] = None
                for resolver in self._custom_pair_resolvers:
                    c = resolver(bi, bj)
                    if c is not None:
                        break
                if c is None:
                    c = build_contact(bi, bj)
                if c is not None:
                    contacts.append(c)

        # Apply positional separation once per frame. ``Contact.penetration`` is a
        # snapshot from narrow-phase; repeating the same correction each solver
        # iteration over-separates bodies and drains kinetic energy artificially.
        for c in contacts:
            positional_correction(c)
        el = self.elastic_collisions
        for b in self.bodies:
            resolve_walls(b, self.world_width, self.world_height, elastic=el)

        for _ in range(NUM_SOLVER_ITERATIONS):
            for c in contacts:
                resolve_impulse(c, elastic=el)
            for b in self.bodies:
                resolve_walls(b, self.world_width, self.world_height, elastic=el)

    def total_linear_momentum(self) -> Vec2:
        px = sum(b.mass * b.vx for b in self.bodies)
        py = sum(b.mass * b.vy for b in self.bodies)
        return (px, py)

    def scalar_momentum(self) -> float:
        return vec_len(self.total_linear_momentum())

    def total_kinetic_energy(self) -> float:
        ke = 0.0
        for b in self.bodies:
            v2 = b.vx * b.vx + b.vy * b.vy
            ke += 0.5 * b.mass * v2 + 0.5 * b.inertia * b.angular_velocity * b.angular_velocity
        return ke

    def register_collision_pair(
        self,
        resolver: Callable[[RigidBody, RigidBody], Optional[Contact]],
    ) -> None:
        """Register a resolver tried before the built-in ``build_contact`` (first match wins)."""

        self._custom_pair_resolvers.append(resolver)
