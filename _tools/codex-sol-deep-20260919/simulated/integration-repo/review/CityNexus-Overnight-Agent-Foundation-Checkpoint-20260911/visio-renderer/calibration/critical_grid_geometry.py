"""Exact critical-coordinate helpers for CityNexus route planning.

The existing 0.10 cm raster is useful for coarse search, but several legal P1
ports are not 0.10-aligned (examples: 3.16, 4.23, 8.875, 11.225, 12.575 cm).
A proof-quality router must not silently drop those terminal segments.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

DEFAULT_SCALE = 200  # integer quantum = 0.005 cm


def q(value, scale: int = DEFAULT_SCALE) -> int:
    d=Decimal(str(value))*Decimal(scale)
    return int(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def unq(value: int, scale: int = DEFAULT_SCALE) -> float:
    return value/scale


def orientation(a,b):
    if a[1]==b[1]: return 'H'
    if a[0]==b[0]: return 'V'
    return 'D'


def closed_contact(a,b,c,d):
    """Exact closed-segment contact for quantized orthogonal integer points."""
    o1=orientation(a,b); o2=orientation(c,d)
    if 'D' in (o1,o2): raise ValueError('non-orthogonal segment')
    if o1==o2=='H':
        if a[1]!=c[1]: return False
        return max(min(a[0],b[0]),min(c[0],d[0])) <= min(max(a[0],b[0]),max(c[0],d[0]))
    if o1==o2=='V':
        if a[0]!=c[0]: return False
        return max(min(a[1],b[1]),min(c[1],d[1])) <= min(max(a[1],b[1]),max(c[1],d[1]))
    if o1=='V': return closed_contact(c,d,a,b)
    x=c[0]; y=a[1]
    return min(a[0],b[0])<=x<=max(a[0],b[0]) and min(c[1],d[1])<=y<=max(c[1],d[1])


def collect_critical_coordinates(*, page_width, page_height, nodes, route_points_list, port_points, base_step_cm=0.10, offset_cm=0.10, scale=DEFAULT_SCALE):
    """Return exact X/Y coordinate sets for a critical-coordinate rectilinear graph.

    Includes the coarse base lattice PLUS exact node boundaries, frozen-route
    coordinates, exact terminal ports, and +/- offset lanes. This avoids the
    occupancy blind spot caused by dropping non-0.10-aligned segments.
    """
    maxx=q(page_width,scale); maxy=q(page_height,scale)
    step=q(base_step_cm,scale); off=q(offset_cm,scale)
    xs=set(range(0,maxx+1,step)); ys=set(range(0,maxy+1,step)); xs.add(maxx);ys.add(maxy)
    critical_x=set();critical_y=set()
    for n in nodes:
        x=q(n['x'],scale); y=q(n['y'],scale); hw=q(float(n['width'])/2,scale); hh=q(float(n['height'])/2,scale)
        critical_x.update((x-hw,x+hw)); critical_y.update((y-hh,y+hh))
    for pts in route_points_list:
        for x,y in pts: critical_x.add(q(x,scale));critical_y.add(q(y,scale))
    for x,y in port_points: critical_x.add(q(x,scale));critical_y.add(q(y,scale))
    for v in critical_x:
        for d in (-off,0,off):
            if 0<=v+d<=maxx: xs.add(v+d)
    for v in critical_y:
        for d in (-off,0,off):
            if 0<=v+d<=maxy: ys.add(v+d)
    return sorted(xs),sorted(ys)
