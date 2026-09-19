from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from presentation import rect_from_center


def test_center_cm_to_inches_conversion():
    actual = rect_from_center(12.7, 10, 5.08, 2.54, 20)
    expected = (4.0, 3.437007874015748, 6.0, 4.437007874015748)
    assert all(abs(a - b) < 1e-12 for a, b in zip(actual, expected))
