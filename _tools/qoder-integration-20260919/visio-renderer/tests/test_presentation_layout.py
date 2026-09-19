from pathlib import Path
import yaml


def test_c3_presentation_spec_is_inside_page_and_nonoverlapping():
    renderer = Path(__file__).resolve().parents[1]
    spec = yaml.safe_load((renderer / 'calibration' / 'c3-presentation-spec.yaml').read_text(encoding='utf-8'))
    page_w = float(spec['page']['widthCm'])
    page_h = float(spec['page']['heightCm'])
    shapes = spec['presentation']
    assert len({x['id'] for x in shapes}) == len(shapes)
    rects = {}
    for item in shapes:
        x, y, w, h = map(float, (item['x'], item['y'], item['width'], item['height']))
        left, right = x - w / 2, x + w / 2
        top, bottom = y - h / 2, y + h / 2
        assert left >= -1e-9 and top >= -1e-9
        assert right <= page_w + 1e-9 and bottom <= page_h + 1e-9
        rects[item['id']] = (left, top, right, bottom)

    non_bg = [x['id'] for x in shapes if x['id'] != 'BG-CANVAS']
    for i, a in enumerate(non_bg):
        la, ta, ra, ba = rects[a]
        for b in non_bg[i + 1:]:
            lb, tb, rb, bb = rects[b]
            overlap = min(ra, rb) > max(la, lb) and min(ba, bb) > max(ta, tb)
            assert not overlap, f'{a} overlaps {b}'
