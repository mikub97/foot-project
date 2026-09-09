"""Walking process analysis — a live foot-pressure dashboard.

The original version of this dashboard polled a mock service on the Warsaw
University of Technology network, which is no longer reachable. It now replays
real recordings from the PhysioNet *Gait in Parkinson's Disease* database
(see README.md) and pushes frames to the browser over a WebSocket.

Run `python fetch_data.py` once to download and ingest the data, then
`python app.py`.
"""

import asyncio
import time

from dash import Dash, Input, Output, State, ctx, dcc, html, set_props
from dash.exceptions import PreventUpdate

import figures
import gaitdata

#: How often the server pushes a new frame, in seconds.
FRAME_INTERVAL = 0.25

#: Replay speeds offered in the UI.
SPEEDS = [0.25, 1.0, 4.0]

DEFAULT_WINDOW_SECONDS = 8

conn = gaitdata.connect(read_only=True)
SUBJECTS = gaitdata.subjects(conn)
SUBJECT_OPTIONS = [{"label": s.label, "value": s.subject} for s in SUBJECTS]
FIRST_SUBJECT = SUBJECTS[0].subject

app = Dash(__name__, backend="fastapi", websocket_callbacks=True)
app.title = "Walking process analysis"


# ---------------------------------------------------------------- layout ---

def _info_row(label, cell_id):
    return html.Tr([html.Td(label, className="info-label"),
                    html.Td("—", id=cell_id, className="info-value")])


INFO_ROWS = [
    ("Subject", "info-subject"),
    ("Group", "info-group"),
    ("Study", "info-study"),
    ("Age", "info-age"),
    ("Sex", "info-gender"),
    ("Height / weight", "info-body"),
    ("Hoehn & Yahr", "info-hy"),
    ("UPDRS", "info-updrs"),
    ("Stride time", "info-stride"),
    ("Stride-time variability", "info-cv"),
]

header = html.Div([
    html.Div([html.H3("WALKING PROCESS ANALYSIS", className="logo")],
             className="six columns"),
    html.Div([html.Span(
        "Replay of recorded gait — PhysioNet Gait in Parkinson's Disease",
        className="subtitle")], className="six columns"),
], className="twelve columns")

sidebar = html.Div([
    html.H3("SUBJECT"),
    dcc.Dropdown(id="patient-picker", options=SUBJECT_OPTIONS, value=FIRST_SUBJECT,
                 clearable=False, placeholder="Select a subject"),
    html.Table([_info_row(label, cell_id) for label, cell_id in INFO_ROWS],
               className="info-table"),

    html.H3("REPLAY"),
    dcc.Checklist(id="stream-switch", className="toggle",
                  options=[{"label": " Pause", "value": "paused"}], value=[]),
    html.Div("—", id="stream-status", className="stream-status"),
    html.Label("Speed"),
    dcc.RadioItems(id="speed", className="toggle",
                   options=[{"label": f" {s:g}×", "value": s} for s in SPEEDS],
                   value=1.0, inline=True),
], className="three columns panel")

controls = html.Div([
    html.H3("WINDOW"),
    html.Label("How many seconds to show?"),
    dcc.Slider(id="window-seconds", value=DEFAULT_WINDOW_SECONDS, min=2, max=30, step=1,
               marks={s: str(s) for s in (2, 10, 20, 30)}),

    html.H3("FIXED RANGE"),
    html.Div(
        "Leave empty to follow the replay. Times are seconds from the start of "
        "the recording.", className="hint"),
    html.Div([
        # step defaults to "any": pinning it to a fraction would make the
        # browser reject anything off that grid, and Dash would send None.
        html.Div([html.Label("From"),
                  dcc.Input(id="time1-input", type="number", min=0,
                            placeholder="e.g. 12.0")], className="six columns"),
        html.Div([html.Label("Until"),
                  dcc.Input(id="time2-input", type="number", min=0,
                            placeholder="e.g. 30.0")], className="six columns"),
    ], className="twelve columns"),
], className="six columns panel")

app.layout = html.Div([
    dcc.Store(id="controls"),
    dcc.Store(id="stream-boot", data=0),
    header,
    html.Div([
        sidebar,
        html.Div(dcc.Graph(id="rhythm-plot", config={"displaylogo": False}),
                 className="six columns"),
        html.Div(dcc.Graph(id="foot-map", config={"displaylogo": False}),
                 className="three columns"),
    ], className="twelve columns row"),
    html.Div(dcc.Graph(id="sensor-heatmap", config={"displaylogo": False}),
             className="twelve columns row"),
    html.Div([
        html.Div(dcc.Graph(id="box-plot", config={"displaylogo": False}),
                 className="six columns"),
        controls,
    ], className="twelve columns row"),
    html.Div([
        "Data: Goldberger et al., PhysioNet · Gait in Parkinson's Disease "
        "(gaitpdb v1.0.0), ODC-BY 1.0. Anomaly markers are derived from stride "
        "timing, not supplied by the dataset."
    ], className="twelve columns footer"),
], className="container-fluid")


# ------------------------------------------------------------- callbacks ---

@app.callback(
    Output("controls", "data"),
    Input("patient-picker", "value"),
    Input("window-seconds", "value"),
    Input("speed", "value"),
    Input("stream-switch", "value"),
    Input("time1-input", "value"),
    Input("time2-input", "value"),
)
def collect_controls(subject, window, speed, switch, t_from, t_to):
    """Fold every control into one prop.

    The streaming loop reads its settings with a single round trip per frame
    rather than one per control.
    """
    return {
        "subject": subject,
        "window": window or DEFAULT_WINDOW_SECONDS,
        "speed": speed or 1.0,
        "paused": "paused" in (switch or []),
        "from": t_from,
        "to": t_to,
    }


@app.callback(
    [Output(cell_id, "children") for _, cell_id in INFO_ROWS],
    Input("patient-picker", "value"),
)
def update_info(subject_id):
    """Fill the subject panel from the dataset's demographics table."""
    info = gaitdata.subject_info(conn, subject_id)
    if info is None:
        raise PreventUpdate

    def number(value, unit="", digits=0):
        return "—" if value is None else f"{value:.{digits}f}{unit}"

    return (
        info.subject,
        info.group_label,
        info.study_label,
        number(info.age, " years"),
        info.gender_label,
        f"{number(info.height, ' m', 2)} / {number(info.weight, ' kg')}",
        number(info.hoehnyahr, "", 1) if info.grp == 1 else "n/a",
        number(info.updrs) if info.grp == 1 else "n/a",
        number(info.stride_median, " s", 2),
        number(info.stride_cv, "%", 1),
    )


def _frame_for(controls, elapsed, duration):
    """The rows to draw: a fixed range when one is set, else the live window."""
    subject = controls["subject"]
    t_from, t_to = controls.get("from"), controls.get("to")
    if t_from is not None and t_to is not None:
        return gaitdata.traces_between(conn, subject, t_from, t_to)
    return gaitdata.traces_window(conn, subject, elapsed, controls["window"])


@app.callback(Input("stream-boot", "data"), persistent=True, websocket=True)
async def stream(_):
    """Push frames for as long as the browser stays connected.

    This coroutine runs once per connection, so its locals *are* the per-viewer
    replay state — no shared session store is needed. The clock is virtual:
    nothing is written to the database at runtime, the window simply advances
    over the recording in wall-clock time.
    """
    ws = ctx.websocket
    elapsed = 0.0
    subject = None
    last_tick = time.monotonic()

    while True:
        if ws is None or ws.is_shutdown:
            raise PreventUpdate

        settings = await ws.get_prop("controls", "data")
        now = time.monotonic()
        delta, last_tick = now - last_tick, now

        if not settings or not settings.get("subject"):
            await asyncio.sleep(FRAME_INTERVAL)
            continue

        if settings["subject"] != subject:
            subject, elapsed = settings["subject"], 0.0
            info = gaitdata.subject_info(conn, subject)
            duration = info.duration if info else 0.0
            peak = info.sensor_peak if info else None

        fixed_range = settings.get("from") is not None and settings.get("to") is not None
        if not settings["paused"] and not fixed_range:
            elapsed += delta * settings["speed"]
            if duration and elapsed > duration:
                elapsed = 0.0  # loop the recording

        frame = await asyncio.to_thread(_frame_for, settings, elapsed, duration)

        set_props("rhythm-plot", {"figure": figures.rhythm_figure(frame)})
        set_props("sensor-heatmap", {"figure": figures.heatmap_figure(frame)})
        set_props("box-plot", {"figure": figures.box_figure(frame)})
        set_props("foot-map", {"figure": figures.foot_map_figure(
            frame.iloc[-1] if len(frame) else None, peak=peak
        )})

        if fixed_range:
            status = f"Showing {settings['from']:.1f}–{settings['to']:.1f}s (fixed range)"
        else:
            state = "paused" if settings["paused"] else f"{settings['speed']:g}×"
            status = f"{elapsed:.1f}s / {duration:.0f}s · {state}"
        set_props("stream-status", {"children": status})

        await asyncio.sleep(FRAME_INTERVAL)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050)
