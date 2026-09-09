"""End-to-end checks: drive the dashboard in a real browser.

The dashboard pushes every update over a WebSocket, so nothing here can be
verified by inspecting a rendered HTML response — a browser has to run the page.

    python app.py                      # in one terminal
    python -m pytest tests/            # in another

Requires `pip install -r requirements-dev.txt`.
"""

import pytest
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8050/"

# A window of GaPt03 that contains strides flagged as irregular.
ANOMALY_RANGE = (12.3, 17.5)


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        yield page
        browser.close()


def elapsed(page):
    """The replay position the status line reports, in seconds."""
    return float(page.inner_text("#stream-status").split("s /")[0])


def test_charts_render(page):
    for chart in ("rhythm-plot", "sensor-heatmap", "box-plot", "foot-map"):
        assert page.locator(f"#{chart} .js-plotly-plot").count() == 1, chart


def test_subject_panel_shows_real_demographics(page):
    assert page.inner_text("#info-subject") == "GaPt03"
    assert page.inner_text("#info-group") == "Parkinson's"
    assert page.inner_text("#info-age") == "82 years"
    # Stride-time variability is derived, not read from the dataset.
    assert page.inner_text("#info-cv").endswith("%")


def test_replay_advances(page):
    first = elapsed(page)
    page.wait_for_timeout(2500)
    assert elapsed(page) > first, "the virtual clock did not advance"


def test_pause_freezes_and_resumes(page):
    page.click("#stream-switch input[type=checkbox]")
    page.wait_for_timeout(1200)
    frozen = elapsed(page)
    page.wait_for_timeout(2000)
    assert elapsed(page) == frozen, "paused replay kept advancing"

    page.click("#stream-switch input[type=checkbox]")
    page.wait_for_timeout(2000)
    assert elapsed(page) > frozen, "replay did not resume"


def test_switching_subject_restarts_the_stream(page):
    page.click("#patient-picker")
    page.wait_for_timeout(400)
    page.get_by_text("GaCo01", exact=False).first.click()
    page.wait_for_timeout(2500)

    assert page.inner_text("#info-subject") == "GaCo01"
    assert page.inner_text("#info-group") == "Control"
    # The clock restarts at the top of the new recording rather than carrying over.
    assert elapsed(page) < 5.0


def test_fixed_range_pins_the_window_and_shows_anomalies(page):
    page.click("#patient-picker")
    page.wait_for_timeout(400)
    page.get_by_text("GaPt03", exact=False).first.click()
    page.wait_for_timeout(1500)

    page.fill("#time1-input", str(ANOMALY_RANGE[0]))
    page.fill("#time2-input", str(ANOMALY_RANGE[1]))
    page.wait_for_timeout(2500)

    status = page.inner_text("#stream-status")
    assert "fixed range" in status, status

    # The window holds irregular strides, so the annotation must be drawn.
    assert page.locator("#rhythm-plot").get_by_text("irregular stride").count() == 1

    page.fill("#time1-input", "")
    page.fill("#time2-input", "")
    page.wait_for_timeout(1500)
    assert "fixed range" not in page.inner_text("#stream-status")


def test_reload_restarts_cleanly(page):
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    first = elapsed(page)
    page.wait_for_timeout(2000)
    assert elapsed(page) > first, "stream did not resume after a reload"


def test_no_console_errors(page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    assert errors == []
