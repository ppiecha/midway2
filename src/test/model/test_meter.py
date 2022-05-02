from src.app.mingus.core import value
from src.app.model.meter import Meter, invert


def test_meter_exceeds_beat_limit():
    meter = Meter()
    assert meter.significant_value(unit=value.sixty_fourth) is False
    assert meter.significant_value(unit=value.eighth) is True


def test_meter_unit_from_ratio(capsys):
    meter = Meter(numerator=3)
    unit = meter.unit_from_ratio(ratio=1 / 3)
    print(unit)
    assert unit == 4.0


def test_meter_add(capsys):
    meter = Meter()
    val = meter.add(value=value.eighth, value_diff=-value.quarter)
    assert val == -value.eighth
    val = meter.add(value=value.eighth, value_diff=-value.eighth)
    assert val == 0
    val = meter.add(value=value.eighth, value_diff=value.eighth)
    assert val == value.quarter


def test_meter_bar_remainder(capsys):
    meter = Meter()
    val = meter.add(value=value.half, value_diff=value.quarter)
    print(val)
    val = meter.add(value=val, value_diff=value.half)
    print(val)
    val = meter.bar_remainder(val)
    print(val)
    assert val == 4.0
    val = meter.add(value=value.quarter, value_diff=-value.half)
    print(val)
    assert val == -4.0
    val = meter.bar_remainder(val)
    print(invert(val))
    assert invert(val) == 0.75
