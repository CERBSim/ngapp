"""Geometry helpers for the workshop — you don't need to read this file.

``create_geometry`` builds the 2-D flow domain around a NACA 4-digit airfoil:
a rectangle (the wind tunnel) with the wing cut out of it.  The boundaries are
named so we can attach physics later:

    "inlet"   the left edge        (flow comes in here)
    "outlet"  the other 3 edges    (flow leaves here)
    "wall"    the airfoil surface

It returns a ``netgen.occ.OCCGeometry`` (dim=2) ready to render or mesh.
"""

from math import atan, cos, sin, sqrt

import numpy as np
from netgen.occ import (
    Axis,
    Face,
    OCCGeometry,
    Rectangle,
    SplineApproximation,
    Wire,
    X,
    Z,
)


def _naca4(number, n=100):
    """Return the (x, y) outline of a NACA 4-digit airfoil, chord = 1."""
    m = float(number[0]) / 100.0          # max camber
    p = float(number[1]) / 10.0           # camber position
    t = float(number[2:]) / 100.0         # max thickness

    a0, a1, a2, a3, a4 = 0.2969, -0.1260, -0.3516, 0.2843, -0.1036
    x = np.linspace(0.0, 1.0, n + 1)
    yt = [5 * t * (a0 * sqrt(xx) + a1 * xx + a2 * xx**2 + a3 * xx**3 + a4 * xx**4)
          for xx in x]

    if p == 0:  # symmetric airfoil
        xu, yu = x, yt
        xl, yl = x, [-v for v in yt]
    else:
        xc1 = [xx for xx in x if xx <= p]
        xc2 = [xx for xx in x if xx > p]
        yc = ([m / p**2 * xx * (2 * p - xx) for xx in xc1]
              + [m / (1 - p)**2 * (1 - 2 * p + xx) * (1 - xx) for xx in xc2])
        dyc = ([m / p**2 * (2 * p - 2 * xx) for xx in xc1]
               + [m / (1 - p)**2 * (2 * p - 2 * xx) for xx in xc2])
        theta = [atan(v) for v in dyc]
        xu = [xx - yy * sin(th) for xx, yy, th in zip(x, yt, theta)]
        yu = [cc + yy * cos(th) for cc, yy, th in zip(yc, yt, theta)]
        xl = [xx + yy * sin(th) for xx, yy, th in zip(x, yt, theta)]
        yl = [cc - yy * cos(th) for cc, yy, th in zip(yc, yt, theta)]

    xs = list(xu[::-1]) + list(xl[1:])
    ys = list(yu[::-1]) + list(yl[1:])
    return xs, ys


def create_geometry(camber=2, camber_pos=40, thickness=12, angle=5,
                    width=4.0, height=3.0, wall_maxh=0.02):
    """Flow domain (rectangle minus the airfoil) as a 2-D OCCGeometry.

    Parameters are the four NACA inputs (camber %, camber position %, thickness
    %, angle of attack in degrees).  Boundaries are named ``inlet``/``outlet``/
    ``wall``.
    """
    code = f"{int(camber)}{int(camber_pos) // 10}{int(thickness):d}"
    xs, ys = _naca4(code)
    points = [(x, y, 0) for x, y in zip(xs, ys)]

    rect = Rectangle(width, height).Face().Move((-width / 2 + 1, -height / 2, 0))
    rect.edges.name = "outlet"
    rect.edges.Min(X).name = "inlet"

    # a modest tolerance keeps the spline from wiggling into a self-intersection
    # near the sharp trailing edge (which would make the face impossible to mesh)
    wing = Face(Wire(SplineApproximation(points, tol=1e-3)))
    wing.edges.name = "wall"
    wing.edges.maxh = wall_maxh
    wing = wing.Rotate(Axis((0, 0, 0), Z), -float(angle))

    air = rect - wing
    return OCCGeometry(air, dim=2)


class FlowResult:
    """The outcome of one flow solve, handed back to the app."""

    def __init__(self, mesh, speed, lift, drag):
        self.mesh = mesh
        self.speed = speed          # speed field, for the colour plot
        self.lift = lift            # lift coefficient C_L
        self.drag = drag            # drag coefficient C_D
        self.ld = lift / drag if drag else 0.0


def solve(camber=2, camber_pos=40, thickness=12, angle=5, maxh=0.1, order=3):
    """Solve potential flow around the airfoil; return a :class:`FlowResult`.

    Incompressible, irrotational flow via the stream function psi (Laplace's
    equation).  The airfoil is a streamline and the far field carries a uniform
    horizontal stream; the angle of attack lives in the rotated geometry.

    Lift comes from the circulation, fixed by a Kutta condition (the trailing
    edge must be a stagnation point).  We solve two cheap problems sharing one
    factorised matrix — psi0 with no circulation and psi1 a unit-circulation
    mode — and combine them as psi = psi0 + Gamma * psi1.  Potential flow is
    inviscid (zero true drag), so drag is a simple profile-drag polar estimate.
    """
    import ngsolve as ngs
    import numpy as np

    geo = create_geometry(camber, camber_pos, thickness, angle)
    mesh = ngs.Mesh(geo.GenerateMesh(maxh=maxh))
    mesh.Curve(order)

    fes = ngs.H1(mesh, order=order, dirichlet="inlet|outlet|wall")
    u, v = fes.TnT()
    a = ngs.BilinearForm(ngs.grad(u) * ngs.grad(v) * ngs.dx).Assemble()
    inv = a.mat.Inverse(fes.FreeDofs())

    def solve_bc(far_value, wall_value):
        g = ngs.GridFunction(fes)
        g.Set(ngs.CF(far_value), definedon=mesh.Boundaries("inlet|outlet"))
        if wall_value:
            g.Set(ngs.CF(wall_value), definedon=mesh.Boundaries("wall"))
        rhs = g.vec.CreateVector()
        rhs.data = -a.mat * g.vec
        g.vec.data += inv * rhs
        return g

    psi0 = solve_bc(ngs.y, 0)        # uniform stream, airfoil at psi = 0
    psi1 = solve_bc(0, 1)            # unit-circulation mode (wall = 1, far = 0)

    # Kutta: pick the circulation that makes the trailing edge a stagnation
    # point, i.e. minimises the speed of psi0 + Gamma*psi1 just behind the TE.
    a_rad = np.deg2rad(float(angle))
    te = np.array([np.cos(a_rad), -np.sin(a_rad)])   # rotated trailing edge
    gamma = 0.0
    for eps in (0.05, 0.08, 0.12, 0.03):
        try:
            mip = mesh(*(te + eps * te))
            g0, g1 = ngs.grad(psi0)(mip), ngs.grad(psi1)(mip)
            denom = g1[0] ** 2 + g1[1] ** 2
            if denom > 1e-9:
                gamma = -(g0[0] * g1[0] + g0[1] * g1[1]) / denom
                break
        except Exception:
            continue

    psi = ngs.GridFunction(fes)
    psi.vec.data = psi0.vec + gamma * psi1.vec
    grad = ngs.grad(psi)
    speed = ngs.sqrt(grad[0] ** 2 + grad[1] ** 2)

    # C_L = 2*Gamma / (U*chord) (both 1); sign so positive angle -> positive lift
    lift = -2.0 * gamma
    t = float(thickness) / 100.0
    drag = 0.008 + 0.01 * t + 0.04 * lift ** 2   # profile-drag polar estimate
    return FlowResult(mesh, speed, lift, drag)
