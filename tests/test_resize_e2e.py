"""Plot and canvas follow their element: resized container, content drawn or
resized while hidden."""

from playwright.sync_api import Page

from ngapp.e2e import app_test

_FITS = """(w) => {
  const box = document.querySelector('.t-plot'), svg = box.querySelector('.main-svg');
  const c = document.querySelector('canvas.t-canvas'), dpr = window.devicePixelRatio;
  return !!svg && box.clientWidth === w && +svg.getAttribute('width') === w
    && +svg.getAttribute('height') === box.clientHeight
    && c.clientWidth === w && c.width === Math.round(w * dpr);
}"""


@app_test("tests.local_app_resize")
def test_plot_and_canvas_follow_their_size(page: Page, app) -> None:
    def fits(width):
        page.wait_for_function(_FITS, arg=width, timeout=15000)

    fits(600)
    app.width.value = 300  # container only, no window resize
    fits(300)
    app.hidden.value = True
    app.n.value = 2  # drawn while hidden
    page.wait_for_timeout(500)
    app.hidden.value = False
    fits(300)
    app.hidden.value = True
    app.width.value = 500  # resized while hidden
    page.wait_for_timeout(500)
    app.hidden.value = False
    fits(500)
