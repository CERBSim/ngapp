"""Material model and parameter"""

import dataclasses
from typing import Optional

import pint

from .helper_components import NumberInput
from .qcomponents import QSelect

ureg = pint.UnitRegistry()
ureg.formatter.default_format = "{:~P}"
pint.set_application_registry(ureg)
Unit = ureg.Unit
Quantity = ureg.Quantity


def parse_quantity(quantity: str) -> Quantity:
    tokens = quantity.strip().split(" ")
    if len(tokens) == 1:
        return Quantity(tokens[0])

    return Quantity(tokens[0], " ".join(tokens[1:]))


class QuantityInput(NumberInput):
    """A float parameter with a unit"""

    ui_units: list[str]
    _unit_input: QSelect | None

    def __init__(
        self,
        ui_units: list[str] | str,
        ui_value: str | None = None,
        ui_label: str = "",
        **kwargs,
    ):
        self._my_callbacks = []
        if isinstance(ui_units, str):
            ui_units = [ui_units]
        self.ui_units = ui_units
        if len(self.ui_units) == 1:
            # only one unit, just show it in hint
            ui_label += f" ({ui_units[0]})"
            self._unit_input = None
        else:
            self._unit_input = QSelect(
                ui_model_value=self.ui_units[0],
                ui_options=self.ui_units,
                ui_label="Unit",
                ui_class="q-ml-xs",
                ui_style="width: 4em;",
            )
        super().__init__(ui_label=ui_label, **kwargs)
        if self._unit_input is not None:
            self.ui_slots["after"] = [self._unit_input]

        if ui_value is not None:
            if isinstance(ui_value, str):
                self.quantity = parse_quantity(ui_value)
            else:
                self.ui_model_value = float(ui_value)

        if self._unit_input is not None:
            # Trigger update:model-value of value when unit changes
            self._unit_input.on_update_model_value(
                lambda args: self._handle(
                    "update:model-value", self.ui_model_value
                )
            )

    @property
    def unit(self):
        """The unit of the parameter"""
        if self._unit_input is None:
            return Unit(self.ui_units[0])
        return Unit(self._unit_input.ui_model_value)

    @unit.setter
    def unit(self, unit: str):
        if self._unit_input is not None:
            self._unit_input.ui_model_value = unit

    @property
    def quantity(self) -> Quantity | None:
        """The value of the parameter as quantity"""
        if self.ui_model_value is None:
            return None
        return Quantity(self.ui_model_value, self.unit)

    @quantity.setter
    def quantity(self, quantity: Optional[Quantity | str]):
        if quantity is None:
            self.ui_model_value = None
            return
        if isinstance(quantity, str):
            quantity = parse_quantity(quantity)
        self.ui_model_value = quantity.m
        self.unit = str(quantity.u)

    def to(self, unit: str) -> Quantity | None:
        """Converts the value to the given unit"""
        q = self.quantity
        if q is None:
            return None
        return q.to(unit)

    def m_as(self, unit: str) -> float | None:
        """Converts the magnitute (float) in the given unit"""
        q = self.quantity
        if q is None:
            return None
        return q.m_as(unit)

    def dump(self):
        data = super().dump()
        if self.quantity is not None:
            if data is None:
                data = {}
            data["unit"] = f"{self.unit:~P}"
        data["units"] = self.ui_units
        return data

    def load(self, data):
        self.unit = data.pop("unit", None)
        self.ui_units = data.pop("units", self.ui_units)
        super().load(data)

    @NumberInput.ui_label.getter
    def ui_label(self):
        l = self._props.get("label", "")
        if len(self.ui_units) > 1:
            return l
        return l[: -len(f" ({self.ui_units[0]})")]

    @NumberInput.ui_label.setter
    def ui_label(self, value):
        if len(self.ui_units) == 1:
            value = f"{value} ({self.ui_units[0]})"
        self._set_prop("label", value)


@dataclasses.dataclass
class Constants:
    """Physical constants"""

    eps0 = 8.8541878128e-12 * Unit("A s / (V m)")
    mu0 = 1.25663706212e-6 * Unit("N / (A A)")
    c = 299792458 * Unit("m/s")
