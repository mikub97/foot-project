"""Figure builders for the foot-pressure dashboard.

Four views, each with one job:

``rhythm_figure``    total force under each foot over time — the gait cycle
``heatmap_figure``   all 16 sensors over time, as magnitude
``foot_map_figure``  where the pressure sits right now, anatomically
``box_figure``       how each sensor is loaded across the window

The palette is deliberately small. Sixteen sensors are never sixteen hues: the
two feet are the only categorical split (blue / orange), and everything that
encodes *magnitude* uses a single blue ramp, light for high. Both were validated
against this dashboard's `#1E1E1E` surface.
"""

import numpy as np
import plotly.graph_objs as go

from gaitdata import LEFT_SENSORS, RIGHT_SENSORS, SENSOR_COORDS, SENSORS

# -- Theme ------------------------------------------------------------------
# Dark surface, matching assets/style.css.
SURFACE = "#1E1E1E"
PANEL = "#31302F"
INK = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRID = "#2c2c2a"
AXIS = "#383835"

LEFT_COLOR = "#3987e5"   # categorical slot 1, dark step
RIGHT_COLOR = "#d95926"  # categorical slot 2, dark step
CRITICAL = "#d03b3b"     # status: reserved for the irregular-stride marker

#: Sequential blue, dark-surface orientation: low values recede towards the
#: surface, high values come forward.
PRESSURE_SCALE = [
    [0.00, "#0d366b"], [0.15, "#184f95"], [0.30, "#256abf"],
    [0.45, "#3987e5"], [0.60, "#5598e7"], [0.75, "#86b6ef"],
    [0.90, "#b7d3f6"], [1.00, "#cde2fb"],
]

FONT = dict(
    family='system-ui, -apple-system, "Segoe UI", sans-serif',
    color=INK_SECONDARY,
    size=12,
)

#: Cap on points pushed per series per frame. The stream runs several times a
#: second, so an undownsampled 100 Hz window would dominate the payload.
MAX_POINTS = 400


def _base_layout(**overrides):
    layout = dict(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=FONT,
        margin=dict(l=60, r=20, t=48, b=44),
        title=dict(font=dict(color=INK, size=14), x=0.01, xanchor="left"),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=AXIS, font=dict(color=INK)),
        showlegend=False,
        uirevision="keep",  # don't reset the reader's zoom on every push
    )
    layout.update(overrides)
    return layout


def _axis(title=None, **overrides):
    axis = dict(
        title=dict(text=title, font=dict(color=INK_MUTED, size=11)),
        gridcolor=GRID,
        zerolinecolor=AXIS,
        linecolor=AXIS,
        tickfont=dict(color=INK_MUTED, size=10),
    )
    axis.update(overrides)
    return axis


def _empty(message="Waiting for data…"):
    figure = go.Figure()
    figure.update_layout(**_base_layout())
    figure.add_annotation(
        text=message, showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5,
        font=dict(color=INK_MUTED, size=13),
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure


def _thin(frame, max_points=MAX_POINTS):
    """Every nth row, so a frame carries at most ``max_points`` samples."""
    if len(frame) <= max_points:
        return frame
    return frame.iloc[:: int(np.ceil(len(frame) / max_points))]


def _anomaly_spans(frame, column):
    """Contiguous ``(t_start, t_end)`` ranges where ``column`` is flagged.

    One shaded band per irregular stride, rather than one marker per sample —
    at 100 Hz the latter would be thousands of shapes per frame.
    """
    flags = frame[column].to_numpy(dtype=int)
    times = frame["t"].to_numpy(dtype=float)
    if flags.size == 0 or not flags.any():
        return []

    padded = np.concatenate(([0], flags, [0]))
    starts = np.flatnonzero((padded[1:] == 1) & (padded[:-1] == 0))
    ends = np.flatnonzero((padded[:-1] == 1) & (padded[1:] == 0)) - 1
    return [(times[s], times[min(e, times.size - 1)]) for s, e in zip(starts, ends)]


# -- Rhythm -----------------------------------------------------------------

def rhythm_figure(frame):
    """Total force under each foot: the walking rhythm, with irregular strides.

    Two series is the whole point — the alternation between them *is* the gait
    cycle, and stance/swing asymmetry is visible at a glance.
    """
    if frame.empty:
        return _empty()

    thinned = _thin(frame)
    figure = go.Figure()
    for column, name, color in (
        ("total_l", "Left foot", LEFT_COLOR),
        ("total_r", "Right foot", RIGHT_COLOR),
    ):
        figure.add_trace(go.Scatter(
            x=thinned["t"], y=thinned[column], name=name, mode="lines",
            line=dict(color=color, width=2),
            hovertemplate=f"{name}: %{{y:.0f}} N<extra></extra>",
        ))

    peak = float(frame[["total_l", "total_r"]].to_numpy().max())
    for column in ("anom_l", "anom_r"):
        for start, end in _anomaly_spans(frame, column):
            figure.add_vrect(
                x0=start, x1=end, line_width=0, fillcolor=CRITICAL, opacity=0.14,
                layer="below",
            )

    figure.update_layout(**_base_layout(
        title=dict(text="Ground reaction force", font=dict(color=INK, size=14),
                   x=0.01, xanchor="left"),
        showlegend=True,
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=1, xanchor="right",
                    font=dict(color=INK_SECONDARY, size=11)),
        hovermode="x unified",
        xaxis=_axis("time in recording (s)",
                    range=[float(frame["t"].iloc[0]), float(frame["t"].iloc[-1])]),
        yaxis=_axis("force (N)", range=[0, peak * 1.12 if peak else 1]),
    ))

    shaded = _anomaly_spans(frame, "anom_l") + _anomaly_spans(frame, "anom_r")
    if shaded:
        figure.add_annotation(
            text="⚠ shaded = irregular stride", showarrow=False,
            xref="paper", yref="paper", x=0.01, y=1.06, xanchor="left",
            font=dict(color=CRITICAL, size=11),
        )
    return figure


# -- Heatmap ----------------------------------------------------------------

def heatmap_figure(frame):
    """All 16 sensors over time. Magnitude, so: one hue, light for high."""
    if frame.empty:
        return _empty()

    thinned = _thin(frame, 240)
    # Plotly draws y[0] at the bottom, so this puts each foot's toe at the top
    # of its block, heel at the bottom, with the left foot above the right.
    order = RIGHT_SENSORS + LEFT_SENSORS
    figure = go.Figure(go.Heatmap(
        z=[thinned[s].to_numpy() for s in order],
        x=thinned["t"],
        y=order,
        colorscale=PRESSURE_SCALE,
        zmin=0,
        colorbar=dict(
            title=dict(text="N", font=dict(color=INK_MUTED, size=10)),
            tickfont=dict(color=INK_MUTED, size=10),
            outlinecolor=AXIS, thickness=10, len=0.9,
        ),
        hovertemplate="%{y} at %{x:.2f}s: %{z:.0f} N<extra></extra>",
    ))
    figure.update_layout(**_base_layout(
        title=dict(text="All 16 sensors", font=dict(color=INK, size=14),
                   x=0.01, xanchor="left"),
        margin=dict(l=60, r=20, t=48, b=44),
        xaxis=_axis("time in recording (s)"),
        yaxis=_axis(None, tickfont=dict(color=INK_MUTED, size=9), showgrid=False),
    ))
    # A hairline between the two feet, so the blocks read as two insoles.
    figure.add_hline(y=7.5, line=dict(color=INK_MUTED, width=1))
    return figure


# -- Foot map ---------------------------------------------------------------

def _foot_outline(centre_x, mirror=False):
    """An SVG path roughly the shape of a foot, around one insole's sensors.

    The sensor coordinates alone read as a scatter of dots; an outline makes
    the panel legible as a pair of feet at a glance. The shape is decorative —
    only the sensor positions inside it are from the dataset.
    """
    side = -1 if mirror else 1

    def point(dx, dy):
        return f"{centre_x + side * dx},{dy}"

    return (
        f"M {point(-30, -1010)} "                                  # heel centre
        f"C {point(-330, -990)} {point(-370, -700)} {point(-350, -430)} "
        f"C {point(-330, -150)} {point(-370, 300)} {point(-330, 620)} "
        f"C {point(-300, 900)} {point(-60, 1000)} {point(90, 960)} "   # toes
        f"C {point(260, 900)} {point(330, 700)} {point(320, 430)} "
        f"C {point(310, 100)} {point(300, -300)} {point(300, -560)} "
        f"C {point(300, -880)} {point(200, -1020)} {point(-30, -1010)} Z"
    )


def foot_map_figure(row, peak=None):
    """Where the load sits right now, drawn at the real sensor coordinates.

    Replaces the original's static ``feet.png`` legend: position carries sensor
    identity, colour and size carry pressure, and the ring marks each foot's
    centre of pressure — the force-weighted centroid of its eight sensors.

    ``peak`` fixes the colour scale for the whole recording. Without it the
    scale would re-fit on every frame and the same colour would mean a
    different force from one push to the next.
    """
    if row is None:
        return _empty("No sample yet")

    values = np.array([float(row[s]) for s in SENSORS])
    xs = np.array([SENSOR_COORDS[s][0] for s in SENSORS], dtype=float)
    ys = np.array([SENSOR_COORDS[s][1] for s in SENSORS], dtype=float)
    ceiling = float(peak) if peak else max(float(values.max()), 1.0)

    figure = go.Figure()
    figure.update_layout(**_base_layout(
        title=dict(text="Pressure map", font=dict(color=INK, size=14),
                   x=0.01, xanchor="left"),
        margin=dict(l=10, r=10, t=48, b=20),
        xaxis=_axis(None, range=[-1150, 1150], visible=False),
        yaxis=_axis(None, range=[-1250, 1200], visible=False,
                    scaleanchor="x", scaleratio=1),
    ))

    for centre, mirror in ((-500, False), (500, True)):
        figure.add_shape(
            type="path", path=_foot_outline(centre, mirror),
            line=dict(color=AXIS, width=1.5), fillcolor="#262625", layer="below",
        )

    figure.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers", name="sensors",
        marker=dict(
            size=13 + 25 * np.clip(values / ceiling, 0, 1),
            color=values, colorscale=PRESSURE_SCALE, cmin=0, cmax=ceiling,
            line=dict(color=SURFACE, width=2),  # 2px surface ring on overlap
            colorbar=dict(
                title=dict(text="N", font=dict(color=INK_MUTED, size=10)),
                tickfont=dict(color=INK_MUTED, size=10),
                outlinecolor=AXIS, thickness=10, len=0.85,
            ),
        ),
        text=SENSORS,
        hovertemplate="%{text}: %{marker.color:.0f} N<extra></extra>",
    ))

    for sensors, color, label, x_label in (
        (LEFT_SENSORS, LEFT_COLOR, "Left", -500),
        (RIGHT_SENSORS, RIGHT_COLOR, "Right", 500),
    ):
        weights = np.array([float(row[s]) for s in sensors])
        if weights.sum() > 0:
            cop_x = float(np.average([SENSOR_COORDS[s][0] for s in sensors], weights=weights))
            cop_y = float(np.average([SENSOR_COORDS[s][1] for s in sensors], weights=weights))
            figure.add_trace(go.Scatter(
                x=[cop_x], y=[cop_y], mode="markers",
                name=f"{label} centre of pressure",
                marker=dict(size=18, color="rgba(0,0,0,0)", symbol="circle",
                            line=dict(color=color, width=3)),
                hovertemplate=f"{label} centre of pressure<extra></extra>",
            ))
        figure.add_annotation(
            text=label, x=x_label, y=-1160, showarrow=False,
            font=dict(color=color, size=12),
        )

    figure.add_annotation(
        text="○ centre of pressure", showarrow=False,
        xref="paper", yref="paper", x=0.5, y=1.02, xanchor="center",
        font=dict(color=INK_MUTED, size=10),
    )
    return figure


# -- Distribution -----------------------------------------------------------

def box_figure(frame):
    """Per-sensor load distribution over the window.

    Position on the x axis carries sensor identity; colour only repeats the
    left/right split, so no sensor depends on a hue of its own.
    """
    if frame.empty:
        return _empty()

    figure = go.Figure()
    for sensor in SENSORS:
        figure.add_trace(go.Box(
            y=frame[sensor], name=sensor,
            marker=dict(color=LEFT_COLOR if sensor.startswith("L") else RIGHT_COLOR,
                        size=3, outliercolor=INK_MUTED),
            line=dict(width=1),
            fillcolor="rgba(0,0,0,0)",
            # 100 Hz means thousands of samples per box; only outliers are drawn.
            boxpoints="outliers",
            hoverinfo="y",
        ))
    figure.update_layout(**_base_layout(
        title=dict(text="Sensor load distribution", font=dict(color=INK, size=14),
                   x=0.01, xanchor="left"),
        margin=dict(l=60, r=20, t=48, b=40),
        xaxis=_axis(None, tickfont=dict(color=INK_MUTED, size=10)),
        yaxis=_axis("force (N)", zeroline=True),
    ))
    return figure
