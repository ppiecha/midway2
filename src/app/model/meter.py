from pydantic import BaseModel, PositiveInt, NonNegativeFloat, PositiveFloat

from src.app.mingus.core.value import add, subtract
from src.app.model.types import Unit
from src.app.utils.properties import GuiAttr


def invert(value: float):
    return 0 if value == 0 else 1.0 / value


class Meter(BaseModel):
    numerator: PositiveInt = 4
    denominator: PositiveInt = 4
    min_unit: PositiveInt = GuiAttr.GRID_MIN_UNIT

    def length(self) -> NonNegativeFloat:
        return self.numerator * invert(value=self.denominator)

    def below_limit(self, unit: Unit) -> NonNegativeFloat:
        return invert(unit) < invert(self.min_unit)

    def exceeds_length(self, unit: Unit):
        return invert(unit) > self.length()

    def add(self, value: float, value_diff: float) -> NonNegativeFloat:
        if value_diff == -value:
            return 0
        if value_diff > 0:
            return add(value1=value, value2=value_diff)
        elif value_diff < 0:
            return subtract(value1=value, value2=-value_diff)
        else:
            return value

    def bar_remainder(self, unit: Unit) -> NonNegativeFloat:
        if unit < 0:
            return invert(self.length() + invert(unit))
        elif self.exceeds_length(unit=unit):
            return invert(invert(unit) - self.length())

    def unit_from_ratio(self, ratio: float) -> Unit:
        value = ratio * self.length()
        return 0 if value == 0 else invert(value)

    def unit_ratio(self, unit: Unit) -> PositiveFloat:
        return invert(unit) / self.length() if unit != 0 else 0
