"""Typed state: fields are validated when set and read, followed like state
keys, and bound to inputs with ref(); a rejected input shows its error until
a value is stored"""

from typing import Annotated

import pytest
from annotated_types import Gt

from ngapp.app import App, AppConfig
from ngapp.components import Div, QInput
from ngapp.observable import computed
from ngapp.state_model import StateModel, ref
from ngapp.test_utils import mount, standalone_app_test


class Wall(StateModel):
    thickness: float = 0.01
    material: str = "steel"


class TankState(StateModel):
    radius: Annotated[float, Gt(0)] = 1.0
    layers: int = 3
    names: list[str] = []
    wall: Wall


class Tank(App[TankState]):
    def __init__(self):
        super().__init__()
        s = self.state
        self.radius = QInput(ui_model_value=ref(lambda: s.radius))
        self.area = computed(lambda: 3.14 * s.radius**2)
        self.component = Div(self.radius)


AppConfig(Tank, name="tank", version="1")


@standalone_app_test
def test_validated_fields():
    s = Tank().state
    assert isinstance(s, TankState) and s.radius == 1.0 and s.names == []
    s.radius = "2.5"
    s["layers"] = 4.0
    assert s.radius == 2.5 and s.layers == 4 and dict(s) == {"radius": 2.5, "layers": 4}
    with pytest.raises(ValueError):
        s.radius = 0
    with pytest.raises(AttributeError):
        s.radiu = 1
    assert TankState.defaults() == {
        "radius": 1.0, "layers": 3, "names": [],
        "wall": {"thickness": 0.01, "material": "steel"},
    }


@standalone_app_test
def test_input_bound_to_field():
    app = Tank()
    fe = mount(app)
    error = ref(lambda: app.state.radius).error
    fe.event(app.radius, "update:model-value", "2")
    assert app.state["radius"] == 2.0 and app.area.value == 3.14 * 4
    fe.event(app.radius, "update:model-value", "-1")
    assert app.state.radius == 2.0 and error.value == "Input should be greater than 0"
    # another writer stores a value: the error is gone
    app.state.radius = 3
    assert error.value == "" and app.area.value == 3.14 * 9


@standalone_app_test
def test_nested_state():
    app = Tank()
    s = app.state
    runs = []
    mass = computed(lambda: runs.append(1) or s.wall.thickness * s.radius)
    thickness = QInput(ui_model_value=ref(lambda: s.wall.thickness))
    app.component.ui_children = [app.radius, thickness]
    fe = mount(app)
    assert mass.value == 0.01 and len(runs) == 1
    fe.event(thickness, "update:model-value", "0.02")
    assert s.wall.thickness == 0.02 and app.state.ns("wall")["thickness"] == 0.02
    assert mass.value == 0.02 and len(runs) == 2
    s.wall.material = "copper"  # not read by mass
    assert mass.value == 0.02 and len(runs) == 2
    s.wall = {"thickness": "0.03"}
    assert s.wall.dump() == {"thickness": 0.03, "material": "steel"}
    assert mass.value == 0.03
    assert "wall" not in dict(s) and s.dump()["wall"]["thickness"] == 0.03
