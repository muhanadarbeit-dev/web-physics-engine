"""Vector math utilities for 2D physics."""

import math
from typing import Tuple

Vec2 = Tuple[float, float]


def vec_add(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] + b[0], a[1] + b[1])


def vec_sub(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] - b[0], a[1] - b[1])


def vec_scale(v: Vec2, s: float) -> Vec2:
    return (v[0] * s, v[1] * s)


def vec_dot(a: Vec2, b: Vec2) -> float:
    return a[0] * b[0] + a[1] * b[1]


def vec_len_sq(v: Vec2) -> float:
    return v[0] * v[0] + v[1] * v[1]


def vec_len(v: Vec2) -> float:
    return math.sqrt(vec_len_sq(v))


def vec_normalize(v: Vec2) -> Vec2:
    l = vec_len(v)
    if l < 1e-12:
        return (0.0, 0.0)
    return (v[0] / l, v[1] / l)


def vec_perp(v: Vec2) -> Vec2:
    """Perpendicular (90° CCW in standard math; with y-down screen, use consistently)."""
    return (-v[1], v[0])


def cross2d(a: Vec2, b: Vec2) -> float:
    """Scalar z-component of a × b in 2D."""
    return a[0] * b[1] - a[1] * b[0]


def rotate_vec(v: Vec2, angle_rad: float) -> Vec2:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)
