from ngapp.components import Div, QInput
from ngapp.test_utils import standalone_app_test


@standalone_app_test
def test_slot_keeps_namespaces_of_nested_components():
    """Components set into a slot keep the namespaces of their own parents"""
    from ngapp.app import App, AppConfig

    def field(id):
        inner = QInput(id="tol_type")
        return Div(Div(inner), id=id, namespace=True), inner

    a, ia = field("a")
    b, ib = field("b")

    class SlotApp(App):
        def __init__(self):
            self.holder = Div(id="step", namespace=True)
            super().__init__(self.holder)
            self.holder.ui_children = [a, b]

    AppConfig(name="slot", version="0", python_class=SlotApp)
    from ngapp.app import AppConfigWithAccess

    SlotApp._config = AppConfigWithAccess(**SlotApp._config.model_dump(), access_level=9000)
    SlotApp()
    assert (ia._fullid, ib._fullid) == ("step.a.tol_type", "step.b.tol_type")
