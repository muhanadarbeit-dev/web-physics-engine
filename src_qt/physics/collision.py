"""Collision detection routines: broad-phase and narrow-phase (SAT)."""

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .ball import Ball
from .body import RigidBody
from .math_utils import Vec2, vec_dot, vec_len_sq, vec_normalize, vec_perp, vec_sub
from .polygon import PolygonBody


@dataclass
class Contact:
    """Collision manifold data for resolution."""

    body_a: RigidBody
    body_b: RigidBody
    normal: Vec2  # From A toward B (world space)
    penetration: float
    contact_point: Vec2


def closest_point_on_segment(p: Vec2, a: Vec2, b: Vec2) -> Vec2:
    ab = vec_sub(b, a)
    t = vec_dot(vec_sub(p, a), ab) / max(vec_len_sq(ab), 1e-12)
    t = max(0.0, min(1.0, t))
    return (a[0] + ab[0] * t, a[1] + ab[1] * t)


def closest_point_on_polygon(p: Vec2, verts: Sequence[Vec2]) -> Vec2:
    if not verts:
        return p
    n = len(verts)
    best = verts[0]
    best_d2 = vec_len_sq(vec_sub(p, best))
    for i in range(n):
        a, b = verts[i], verts[(i + 1) % n]
        q = closest_point_on_segment(p, a, b)
        d2 = vec_len_sq(vec_sub(p, q))
        if d2 < best_d2:
            best_d2 = d2
            best = q
    return best


def project_polygon(verts: Sequence[Vec2], axis: Vec2) -> Tuple[float, float]:
    first = vec_dot(verts[0], axis)
    mn = mx = first
    for i in range(1, len(verts)):
        p = vec_dot(verts[i], axis)
        mn = min(mn, p)
        mx = max(mx, p)
    return mn, mx


def sat_poly_poly(
    verts_a: Sequence[Vec2], verts_b: Sequence[Vec2], center_a: Vec2, center_b: Vec2
) -> Optional[Tuple[Vec2, float]]:
    """Returns (normal from A to B, penetration) or None if separated."""

    axes: List[Vec2] = []
    na, nb = len(verts_a), len(verts_b)
    for i in range(na):
        edge = vec_sub(verts_a[(i + 1) % na], verts_a[i])
        n = vec_normalize(vec_perp(edge))
        if vec_len_sq(n) > 1e-12:
            axes.append(n)
    for i in range(nb):
        edge = vec_sub(verts_b[(i + 1) % nb], verts_b[i])
        n = vec_normalize(vec_perp(edge))
        if vec_len_sq(n) > 1e-12:
            axes.append(n)

    min_overlap = float("inf")
    best_axis: Optional[Vec2] = None

    for ax in axes:
        min_a, max_a = project_polygon(verts_a, ax)
        min_b, max_b = project_polygon(verts_b, ax)
        overlap = min(max_a, max_b) - max(min_a, min_b)
        if overlap <= 0.0:
            return None
        if overlap < min_overlap:
            min_overlap = overlap
            best_axis = ax

    if best_axis is None:
        return None

    d = vec_sub(center_b, center_a)
    if vec_dot(d, best_axis) < 0.0:
        best_axis = (-best_axis[0], -best_axis[1])
    return best_axis, min_overlap


def sat_circle_poly(
    circle: Ball, verts: Sequence[Vec2], center_poly: Vec2
) -> Optional[Tuple[Vec2, float, Vec2]]:
    """
    Circle vs convex polygon SAT.
    Returns (normal from polygon toward circle, penetration, closest point on poly).
    """

    if not verts:
        return None

    c = circle.position
    r = circle.radius
    n_verts = len(verts)
    min_overlap = float("inf")
    best_axis: Optional[Vec2] = None

    def orient_from_poly(axis: Vec2) -> Vec2:
        d = vec_sub(c, center_poly)
        return axis if vec_dot(axis, d) >= 0.0 else (-axis[0], -axis[1])

    for i in range(n_verts):
        edge = vec_sub(verts[(i + 1) % n_verts], verts[i])
        ax = vec_normalize(vec_perp(edge))
        if vec_len_sq(ax) < 1e-12:
            continue
        min_p, max_p = project_polygon(verts, ax)
        center_proj = vec_dot(c, ax)
        min_c, max_c = center_proj - r, center_proj + r
        overlap = min(max_p, max_c) - max(min_p, min_c)
        if overlap <= 0.0:
            return None
        if overlap < min_overlap:
            min_overlap = overlap
            best_axis = orient_from_poly(ax)

    closest = closest_point_on_polygon(c, verts)
    to_circle = vec_sub(c, closest)
    dist_sq = vec_len_sq(to_circle)
    if dist_sq > 1e-12:
        sep = vec_normalize(to_circle)
        min_p, max_p = project_polygon(verts, sep)
        center_proj = vec_dot(c, sep)
        min_c, max_c = center_proj - r, center_proj + r
        overlap = min(max_p, max_c) - max(min_p, min_c)
        if overlap <= 0.0:
            return None
        if overlap < min_overlap:
            min_overlap = overlap
            best_axis = orient_from_poly(sep)

    if best_axis is None:
        return None

    return best_axis, min_overlap, closest


def circle_circle(a: Ball, b: Ball) -> Optional[Tuple[Vec2, float, Vec2]]:
    d = vec_sub(b.position, a.position)
    dist_sq = vec_len_sq(d)
    rad = a.radius + b.radius
    if dist_sq >= rad * rad:
        return None
    dist = math.sqrt(dist_sq)
    if dist < 1e-8:
        n: Vec2 = (1.0, 0.0)
    else:
        n = (d[0] / dist, d[1] / dist)
    pen = rad - dist
    cp = (a.x + n[0] * a.radius, a.y + n[1] * a.radius)
    return n, pen, cp


def broad_phase(a: RigidBody, b: RigidBody) -> bool:
    dx = b.x - a.x
    dy = b.y - a.y
    dist_sq = dx * dx + dy * dy
    reach = a.bounding_radius() + b.bounding_radius()
    return dist_sq <= reach * reach + 1e-6


def build_contact(a: RigidBody, b: RigidBody) -> Optional[Contact]:
    """Narrow-phase dispatch. Convention: normal from A to B."""

    if isinstance(a, Ball) and isinstance(b, Ball):
        r = circle_circle(a, b)
        if r is None:
            return None
        n, pen, cp = r
        return Contact(a, b, n, pen, cp)

    if isinstance(a, PolygonBody) and isinstance(b, PolygonBody):
        va = a.get_world_vertices()
        vb = b.get_world_vertices()
        r = sat_poly_poly(va, vb, a.position, b.position)
        if r is None:
            return None
        n, pen = r
        cp = ((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)
        return Contact(a, b, n, pen, cp)

    if isinstance(a, Ball) and isinstance(b, PolygonBody):
        verts = b.get_world_vertices()
        r = sat_circle_poly(a, verts, b.position)
        if r is None:
            return None
        n_poly_to_ball, pen, _ = r
        n = (-n_poly_to_ball[0], -n_poly_to_ball[1])
        cp = closest_point_on_polygon(a.position, verts)
        return Contact(a, b, n, pen, cp)

    if isinstance(a, PolygonBody) and isinstance(b, Ball):
        verts = a.get_world_vertices()
        r = sat_circle_poly(b, verts, a.position)
        if r is None:
            return None
        n_poly_to_ball, pen, _ = r
        cp = closest_point_on_polygon(b.position, verts)
        return Contact(a, b, n_poly_to_ball, pen, cp)

    return None
