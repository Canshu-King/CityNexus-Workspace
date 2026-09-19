import math


def inverse_transform(pin_x, pin_y, loc_x, loc_y, angle, page_x, page_y):
    dx, dy = page_x-pin_x, page_y-pin_y
    c, s = math.cos(angle), math.sin(angle)
    return loc_x+c*dx+s*dy, loc_y-s*dx+c*dy


def forward_transform(pin_x, pin_y, loc_x, loc_y, angle, x, y):
    dx, dy = x-loc_x, y-loc_y
    c, s = math.cos(angle), math.sin(angle)
    return pin_x+c*dx-s*dy, pin_y+s*dx+c*dy


def test_page_local_roundtrip_positive_width():
    params=(5.0,4.0,2.0,1.0,0.0)
    p=(7.5,5.25)
    local=inverse_transform(*params,*p)
    out=forward_transform(*params,*local)
    assert abs(out[0]-p[0])<1e-12 and abs(out[1]-p[1])<1e-12


def test_page_local_roundtrip_negative_width_height():
    params=(5.0,4.0,-2.0,-1.0,0.0)
    p=(2.5,1.25)
    local=inverse_transform(*params,*p)
    out=forward_transform(*params,*local)
    assert abs(out[0]-p[0])<1e-12 and abs(out[1]-p[1])<1e-12


def test_page_local_roundtrip_rotated():
    params=(5.0,4.0,2.0,1.0,math.radians(30))
    p=(7.5,5.25)
    local=inverse_transform(*params,*p)
    out=forward_transform(*params,*local)
    assert abs(out[0]-p[0])<1e-12 and abs(out[1]-p[1])<1e-12
