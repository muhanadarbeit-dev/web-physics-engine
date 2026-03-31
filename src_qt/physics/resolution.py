"""Collision resolution routines: impulses and positional correction."""

from typing import Sequence, Tuple

from .ball import Ball
from .body import RigidBody
from .collision import Contact
from .math_utils import Vec2, cross2d, vec_dot, vec_scale, vec_sub
from .polygon import PolygonBody

PENETRATION_PERCENT: float = 0.8
PENETRATION_SLOP: float = 0.01
VELOCITY_SLOP: float = 0.01
NUM_SOLVER_ITERATIONS: int = 6


def resolve_impulse(c: Contact, *, elastic: bool) -> None:
    a, b = c.body_a, c.body_b
    n = c.normal
    ra = vec_sub(c.contact_point, a.position)
    rb = vec_sub(c.contact_point, b.position)

    va = a.linear_velocity_at(c.contact_point)
    vb = b.linear_velocity_at(c.contact_point)
    rel = vec_sub(vb, va)
    vn = vec_dot(rel, n)
    if vn > -VELOCITY_SLOP:
        return

    # e = 1: elastic normal impulse
    e = 1.0 if elastic else min(a.restitution, b.restitution)
    ra_n = cross2d(ra, n)
    rb_n = cross2d(rb, n)
    denom = (
        a.inv_mass
        + b.inv_mass
        + ra_n * ra_n * a.inv_inertia
        + rb_n * rb_n * b.inv_inertia
    )
    if denom < 1e-12:
        return

    j = -(1.0 + e) * vn / denom
    impulse = vec_scale(n, j)

    a.vx -= impulse[0] * a.inv_mass
    a.vy -= impulse[1] * a.inv_mass
    a.angular_velocity -= cross2d(ra, impulse) * a.inv_inertia

    b.vx += impulse[0] * b.inv_mass
    b.vy += impulse[1] * b.inv_mass
    b.angular_velocity += cross2d(rb, impulse) * b.inv_inertia


def positional_correction(c: Contact) -> None:
    a, b = c.body_a, c.body_b
    pen = c.penetration
    if pen <= PENETRATION_SLOP:
        return
    correction_mag = max(pen - PENETRATION_SLOP, 0.0) * PENETRATION_PERCENT
    n = c.normal
    inv_sum = a.inv_mass + b.inv_mass
    if inv_sum < 1e-12:
        return
    corr = vec_scale(n, correction_mag / inv_sum)
    a.x -= corr[0] * a.inv_mass
    a.y -= corr[1] * a.inv_mass
    b.x += corr[0] * b.inv_mass
    b.y += corr[1] * b.inv_mass


def _wall_impulse_and_correct_ball(
    ball: Ball,
    nx: float,
    ny: float,
    penetration: float,
    contact: Vec2,
    *,
    elastic: bool,
) -> None:
    if penetration <= 0.0:
        return
    if penetration > PENETRATION_SLOP:
        corr = (penetration - PENETRATION_SLOP) * PENETRATION_PERCENT
        ball.x += nx * corr
        ball.y += ny * corr

    n = (nx, ny)
    ra = vec_sub(contact, ball.position)
    va = ball.linear_velocity_at(contact)
    vn = vec_dot(va, n)
    if vn >= -VELOCITY_SLOP:
        return
    e = 1.0 if elastic else ball.restitution
    ra_n = cross2d(ra, n)
    denom = ball.inv_mass + ra_n * ra_n * ball.inv_inertia
    if denom < 1e-12:
        return
    j = -(1.0 + e) * vn / denom
    imp = vec_scale(n, j)
    ball.vx += imp[0] * ball.inv_mass
    ball.vy += imp[1] * ball.inv_mass
    ball.angular_velocity += cross2d(ra, imp) * ball.inv_inertia


def resolve_walls_ball(ball: Ball, width: float, height: float, *, elastic: bool) -> None:
    r = ball.radius
    if ball.x - r < 0.0:
        pen = r - ball.x
        cp = (0.0, ball.y)
        _wall_impulse_and_correct_ball(ball, 1.0, 0.0, pen, cp, elastic=elastic)
    if ball.x + r > width:
        pen = ball.x + r - width
        cp = (width, ball.y)
        _wall_impulse_and_correct_ball(ball, -1.0, 0.0, pen, cp, elastic=elastic)
    if ball.y - r < 0.0:
        pen = r - ball.y
        cp = (ball.x, 0.0)
        _wall_impulse_and_correct_ball(ball, 0.0, 1.0, pen, cp, elastic=elastic)
    if ball.y + r > height:
        pen = ball.y + r - height
        cp = (ball.x, height)
        _wall_impulse_and_correct_ball(ball, 0.0, -1.0, pen, cp, elastic=elastic)


def _support_point_poly(verts: Sequence[Vec2], dir_vec: Vec2) -> Tuple[float, Vec2]:
    best_d = -float("inf")
    best_v = verts[0]
    for v in verts:
        d = vec_dot(v, dir_vec)
        if d > best_d:
            best_d = d
            best_v = v
    return best_d, best_v


def resolve_walls_polygon(poly: PolygonBody, width: float, height: float, *, elastic: bool) -> None:
    verts = poly.get_world_vertices()
    if not verts:
        return

    min_x = min(v[0] for v in verts)
    if min_x < 0.0:
        _, vp = _support_point_poly(verts, (-1.0, 0.0))
        pen = -min_x
        n = (1.0, 0.0)
        ra = vec_sub(vp, poly.position)
        if pen > PENETRATION_SLOP:
            corr = (pen - PENETRATION_SLOP) * PENETRATION_PERCENT
            poly.x += corr
            verts = poly.get_world_vertices()
            _, vp = _support_point_poly(verts, (-1.0, 0.0))
            ra = vec_sub(vp, poly.position)
        va = poly.linear_velocity_at(vp)
        vn = vec_dot(va, n)
        if vn < -VELOCITY_SLOP:
            e = 1.0 if elastic else poly.restitution
            ra_n = cross2d(ra, n)
            denom = poly.inv_mass + ra_n * ra_n * poly.inv_inertia
            if denom > 1e-12:
                j = -(1.0 + e) * vn / denom
                imp = vec_scale(n, j)
                poly.vx += imp[0] * poly.inv_mass
                poly.vy += imp[1] * poly.inv_mass
                poly.angular_velocity += cross2d(ra, imp) * poly.inv_inertia

    verts = poly.get_world_vertices()
    max_x = max(v[0] for v in verts)
    if max_x > width:
        _, vp = _support_point_poly(verts, (1.0, 0.0))
        pen = max_x - width
        n = (-1.0, 0.0)
        ra = vec_sub(vp, poly.position)
        if pen > PENETRATION_SLOP:
            corr = (pen - PENETRATION_SLOP) * PENETRATION_PERCENT
            poly.x -= corr
            verts = poly.get_world_vertices()
            _, vp = _support_point_poly(verts, (1.0, 0.0))
            ra = vec_sub(vp, poly.position)
        va = poly.linear_velocity_at(vp)
        vn = vec_dot(va, n)
        if vn < -VELOCITY_SLOP:
            e = 1.0 if elastic else poly.restitution
            ra_n = cross2d(ra, n)
            denom = poly.inv_mass + ra_n * ra_n * poly.inv_inertia
            if denom > 1e-12:
                j = -(1.0 + e) * vn / denom
                imp = vec_scale(n, j)
                poly.vx += imp[0] * poly.inv_mass
                poly.vy += imp[1] * poly.inv_mass
                poly.angular_velocity += cross2d(ra, imp) * poly.inv_inertia

    verts = poly.get_world_vertices()
    min_y = min(v[1] for v in verts)
    if min_y < 0.0:
        _, vp = _support_point_poly(verts, (0.0, -1.0))
        pen = -min_y
        n = (0.0, 1.0)
        ra = vec_sub(vp, poly.position)
        if pen > PENETRATION_SLOP:
            corr = (pen - PENETRATION_SLOP) * PENETRATION_PERCENT
            poly.y += corr
            verts = poly.get_world_vertices()
            _, vp = _support_point_poly(verts, (0.0, -1.0))
            ra = vec_sub(vp, poly.position)
        va = poly.linear_velocity_at(vp)
        vn = vec_dot(va, n)
        if vn < -VELOCITY_SLOP:
            e = 1.0 if elastic else poly.restitution
            ra_n = cross2d(ra, n)
            denom = poly.inv_mass + ra_n * ra_n * poly.inv_inertia
            if denom > 1e-12:
                j = -(1.0 + e) * vn / denom
                imp = vec_scale(n, j)
                poly.vx += imp[0] * poly.inv_mass
                poly.vy += imp[1] * poly.inv_mass
                poly.angular_velocity += cross2d(ra, imp) * poly.inv_inertia

    verts = poly.get_world_vertices()
    max_y = max(v[1] for v in verts)
    if max_y > height:
        _, vp = _support_point_poly(verts, (0.0, 1.0))
        pen = max_y - height
        n = (0.0, -1.0)
        ra = vec_sub(vp, poly.position)
        if pen > PENETRATION_SLOP:
            corr = (pen - PENETRATION_SLOP) * PENETRATION_PERCENT
            poly.y -= corr
            verts = poly.get_world_vertices()
            _, vp = _support_point_poly(verts, (0.0, 1.0))
            ra = vec_sub(vp, poly.position)
        va = poly.linear_velocity_at(vp)
        vn = vec_dot(va, n)
        if vn < -VELOCITY_SLOP:
            e = 1.0 if elastic else poly.restitution
            ra_n = cross2d(ra, n)
            denom = poly.inv_mass + ra_n * ra_n * poly.inv_inertia
            if denom > 1e-12:
                j = -(1.0 + e) * vn / denom
                imp = vec_scale(n, j)
                poly.vx += imp[0] * poly.inv_mass
                poly.vy += imp[1] * poly.inv_mass
                poly.angular_velocity += cross2d(ra, imp) * poly.inv_inertia


def resolve_walls(body: RigidBody, width: float, height: float, *, elastic: bool) -> None:
    if isinstance(body, Ball):
        resolve_walls_ball(body, width, height, elastic=elastic)
    elif isinstance(body, PolygonBody):
        resolve_walls_polygon(body, width, height, elastic=elastic)
