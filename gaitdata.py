"""Data layer for the foot-pressure dashboard.

Replaces the original VPN-only feed (``tesla.iem.pw.edu.pl:9080``) with the
PhysioNet *Gait in Parkinson's Disease* database (``gaitpdb`` v1.0.0):

    https://physionet.org/content/gaitpdb/1.0.0/

Each recording holds 19 tab-separated columns sampled at 100 Hz: the time in
seconds, the vertical ground reaction force on 8 sensors under the left foot,
the same 8 under the right foot, and the total force under each foot.

This module downloads the recordings, ingests them into SQLite together with
derived anomaly flags, and serves query windows to the dashboard.
"""

import os
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd
import requests

#: Where to fetch recordings from. The PhysioNet site is canonical; the AWS
#: Open Data mirror is the same content and is tried when the site is
#: unreachable (their TLS certificate has been known to lapse).
MIRRORS = [
    "https://physionet.org/files/gaitpdb/1.0.0",
    "https://physionet-open.s3.amazonaws.com/gaitpdb/1.0.0",
]
BASE_URL = MIRRORS[0]
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gait.db")

DEMOGRAPHICS_FILE = "demographics.txt"

#: Three PD patients and three controls, mirroring the six "patients" the
#: original dashboard pulled from the university mock service.
DEFAULT_SUBJECTS = ["GaPt03", "GaPt04", "JuPt03", "GaCo01", "JuCo01", "SiCo01"]

#: Subjects recorded walking *and* walking while counting backwards in sevens.
#: Only 27 subjects in the dataset have both walks (21 patients, 6 controls),
#: all in the ``Ga`` study; these are three of each. The pair is what makes a
#: within-subject cognitive-load contrast possible at all.
DUAL_TASK_SUBJECTS = ["GaPt13", "GaPt14", "GaPt15", "GaCo13", "GaCo14", "GaCo15"]

LEFT_SENSORS = [f"L{i}" for i in range(1, 9)]
RIGHT_SENSORS = [f"R{i}" for i in range(1, 9)]
SENSORS = LEFT_SENSORS + RIGHT_SENSORS

#: Sensor positions inside each insole, quoted verbatim from the dataset's
#: ``format.txt``. The origin sits between the legs and +Y points towards the
#: toes; the scale is arbitrary but the relative geometry is real, which is what
#: the foot map and the centre-of-pressure proxy need.
SENSOR_COORDS = {
    "L1": (-500, -800), "L2": (-700, -400), "L3": (-300, -400), "L4": (-700, 0),
    "L5": (-300, 0), "L6": (-700, 400), "L7": (-300, 400), "L8": (-500, 800),
    "R1": (500, -800), "R2": (700, -400), "R3": (300, -400), "R4": (700, 0),
    "R5": (300, 0), "R6": (700, 400), "R7": (300, 400), "R8": (500, 800),
}

#: Columns as they appear in a recording file.
RECORD_COLUMNS = ["t"] + SENSORS + ["total_l", "total_r"]

#: Columns held per trace row in SQLite (adds the derived anomaly flags).
TRACE_COLUMNS = RECORD_COLUMNS + ["anom_l", "anom_r"]

GROUP_LABELS = {1: "Parkinson's", 2: "Control"}
GENDER_LABELS = {1: "Male", 2: "Female"}
STUDY_LABELS = {
    "Ga": "Yogev et al. — dual tasking",
    "Ju": "Hausdorff et al. — rhythmic auditory stimulation",
    "Si": "Frenkel-Toledo et al. — treadmill walking",
}


class DataMissing(RuntimeError):
    """Raised when the dataset has not been fetched or ingested yet."""


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------

#: Walk ``01`` is a usual walk. Walk ``10``, in the ``Ga`` study only, is the
#: same subject walking while counting backwards in sevens — a dual task. Both
#: are quoted from the dataset's ``format.txt``. 27 subjects have the pair
#: (21 patients, 6 controls); most have only the usual walk.
USUAL_WALK = "01"
DUAL_TASK_WALK = "10"

WALK_LABELS = {USUAL_WALK: "usual walking", DUAL_TASK_WALK: "dual task (serial 7s)"}


def record_filename(subject_id, walk=USUAL_WALK):
    """Name of one walk recorded for ``subject_id``."""
    return f"{subject_id}_{walk}.txt"


def recording_id(subject_id, walk=USUAL_WALK):
    """Key for one recording.

    A usual walk keys on the bare subject id, so every recording ingested
    before walks existed keeps the name it already had.
    """
    return subject_id if walk == USUAL_WALK else f"{subject_id}_{walk}"


def split_recording_id(rec_id):
    """``recording_id`` inverted: ``("GaPt13", "10")``."""
    base, _, walk = rec_id.partition("_")
    return base, walk or USUAL_WALK


def _get(name, log=print):
    """Fetch one dataset file, falling back to the next mirror on failure."""
    errors = []
    for base in MIRRORS:
        try:
            response = requests.get(f"{base}/{name}", timeout=120)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            errors.append(f"{base}: {exc}")
            log(f"       {base} unavailable, trying the next mirror")
    raise DataMissing(
        "Could not download " + name + " from any mirror:\n  " + "\n  ".join(errors)
    )


def as_recordings(subject_ids, walks=(USUAL_WALK,)):
    """``["GaPt13"], ("01", "10")`` -> ``[("GaPt13", "01"), ("GaPt13", "10")]``."""
    return [(s, w) for s in subject_ids for w in walks]


def download(subject_ids=None, dest=DATA_DIR, force=False, log=print,
             walks=(USUAL_WALK,), recordings=None):
    """Fetch the demographics table and the requested recordings.

    Files already on disk are left alone unless ``force`` is set. A walk the
    dataset does not have is skipped with a note rather than raising: most
    subjects have only the usual walk, and asking for the dual task everywhere
    is the normal way to find out who has it.
    """
    if recordings is None:
        recordings = as_recordings(list(subject_ids or DEFAULT_SUBJECTS), walks)
    os.makedirs(dest, exist_ok=True)

    paths = []
    for name in [DEMOGRAPHICS_FILE] + [record_filename(s, w) for s, w in recordings]:
        target = os.path.join(dest, name)
        if os.path.exists(target) and not force:
            log(f"  have {name} ({os.path.getsize(target):,} bytes)")
        else:
            log(f"  get  {name} ...")
            try:
                content = _get(name, log=log)
            except DataMissing:
                if name == DEMOGRAPHICS_FILE:
                    raise
                log(f"       {name} is not in the dataset — skipped")
                continue
            with open(target, "wb") as handle:
                handle.write(content)
            log(f"       {len(content):,} bytes")
        if name != DEMOGRAPHICS_FILE:
            paths.append(target)
    return paths


def available_recordings(dest=DATA_DIR):
    """``(subject, walk)`` for every recording file present locally."""
    if not os.path.isdir(dest):
        return []
    found = []
    for name in os.listdir(dest):
        if not name.endswith(".txt") or name == DEMOGRAPHICS_FILE:
            continue
        stem, _, walk = name[:-4].rpartition("_")
        if stem and walk.isdigit():
            found.append((stem, walk))
    return sorted(found)


def available_subjects(dest=DATA_DIR):
    """Subject ids whose usual walk is present locally."""
    return sorted({s for s, w in available_recordings(dest) if w == USUAL_WALK})


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def read_record(path):
    """Read one recording file into a frame with :data:`RECORD_COLUMNS`."""
    df = pd.read_csv(path, sep=r"\s+", header=None, names=RECORD_COLUMNS)
    return df.astype(float)


#: The meaningful columns of ``demographics.txt``. The published file is ragged
#: — rows carry between 20 and 30 tab-separated fields — but only the first 20
#: hold data; the rest is trailing padding, so the columns are named explicitly
#: rather than inferred from the header.
DEMOGRAPHIC_COLUMNS = [
    "ID", "Study", "Group", "Subjnum", "Gender", "Age", "Height", "Weight",
    "HoehnYahr", "UPDRS", "UPDRSM", "TUAG",
    "Speed_01", "Speed_02", "Speed_03", "Speed_04",
    "Speed_05", "Speed_06", "Speed_07", "Speed_10",
]


def read_demographics(dest=DATA_DIR):
    """Read ``demographics.txt`` into a frame indexed by subject id."""
    path = os.path.join(dest, DEMOGRAPHICS_FILE)
    if not os.path.exists(path):
        raise DataMissing(
            f"{path} is missing — run `python fetch_data.py` to download the dataset."
        )
    df = pd.read_csv(
        path,
        sep="\t",
        skiprows=1,
        header=None,
        names=DEMOGRAPHIC_COLUMNS,
        usecols=range(len(DEMOGRAPHIC_COLUMNS)),
        dtype={"ID": str},
    )
    df = df.dropna(subset=["ID"])
    df["ID"] = df["ID"].str.strip()
    return df.set_index("ID", drop=False)


# --------------------------------------------------------------------------
# Derived anomalies
# --------------------------------------------------------------------------

#: A stride is irregular when it deviates this much from the subject's median.
STRIDE_TOLERANCE = 0.10
#: Intervals outside this range mean a missed or double-counted heel strike.
MIN_STRIDE_SECONDS = 0.4
MAX_STRIDE_SECONDS = 3.0


def _mad(values):
    """Median absolute deviation, scaled to be comparable to a std deviation."""
    values = np.asarray(values, dtype=float)
    median = np.median(values)
    return 1.4826 * np.median(np.abs(values - median)), median


def heel_strikes(total_force, times, threshold_fraction=0.25):
    """Indices where the foot loads up, i.e. force rises through a threshold.

    The threshold is a fraction of the recording's peak force for that foot,
    which keeps it robust to differences in body weight between subjects.
    """
    total_force = np.asarray(total_force, dtype=float)
    peak = np.nanmax(total_force) if total_force.size else 0.0
    if peak <= 0:
        return np.array([], dtype=int)
    loaded = total_force > peak * threshold_fraction
    # A rising edge: not loaded at i-1, loaded at i.
    rising = np.flatnonzero(~loaded[:-1] & loaded[1:]) + 1
    return rising


def stride_intervals(total_force, times):
    """Stride durations of one foot, with the sample range each one spans.

    A stride is the interval between successive heel strikes of the same foot.
    Implausible intervals (a missed or double-counted strike) are dropped.
    Returns ``(durations, starts, ends)`` as parallel arrays.
    """
    times = np.asarray(times, dtype=float)
    strikes = heel_strikes(total_force, times)
    if strikes.size < 4:
        empty = np.array([], dtype=int)
        return np.array([]), empty, empty

    durations = np.diff(times[strikes])
    keep = (durations > MIN_STRIDE_SECONDS) & (durations < MAX_STRIDE_SECONDS)
    return durations[keep], strikes[:-1][keep], strikes[1:][keep]


def stride_variability(total_force, times):
    """Coefficient of variation of stride time, as a percentage.

    Stride-time variability is the measure this dataset was collected to study:
    it is markedly higher in Parkinson's gait than in healthy gait, so the
    dashboard reports it as a per-subject gait statistic.
    """
    durations, _, _ = stride_intervals(total_force, times)
    if durations.size < 3 or durations.mean() == 0:
        return float("nan")
    return float(100.0 * durations.std() / durations.mean())


def stride_anomalies(total_force, times, tolerance=STRIDE_TOLERANCE):
    """Flag every sample belonging to a stride of irregular duration.

    A stride counts as irregular when it runs more than ``tolerance`` (10% by
    default) longer or shorter than that subject's median stride. The threshold
    is deliberately a fraction of the median rather than a multiple of the
    subject's own spread: a spread-relative threshold widens for exactly the
    erratic walkers whose strides most deserve flagging, and would flag them no
    more often than steady ones.
    """
    times = np.asarray(times, dtype=float)
    flags = np.zeros(times.size, dtype=np.int8)

    durations, starts, ends = stride_intervals(total_force, times)
    if durations.size < 3:
        return flags

    median = np.median(durations)
    if median <= 0:
        return flags

    irregular = np.abs(durations - median) > tolerance * median
    for start, end, bad in zip(starts, ends, irregular):
        if bad:
            flags[start:end] = 1
    return flags


def detect_anomalies(frame):
    """Add ``anom_l`` / ``anom_r`` columns derived from the signal itself.

    The original API delivered anomaly booleans alongside every reading; this
    dataset has none, so they are computed here from stride timing and are
    clearly derived rather than measured.
    """
    frame = frame.copy()
    for side, total in (("anom_l", "total_l"), ("anom_r", "total_r")):
        frame[side] = stride_anomalies(frame[total], frame["t"]).astype(int)
    return frame


# --------------------------------------------------------------------------
# Ingest
# --------------------------------------------------------------------------

SQL_CREATE_SUBJECTS = """
CREATE TABLE IF NOT EXISTS subjects (
    subject   TEXT PRIMARY KEY,
    study     TEXT,
    grp       INTEGER,
    gender    INTEGER,
    age       REAL,
    height    REAL,
    weight    REAL,
    hoehnyahr REAL,
    updrs     REAL,
    updrsm    REAL,
    tuag      REAL,
    duration  REAL,
    samples   INTEGER,
    stride_cv REAL,
    stride_median REAL,
    sensor_peak REAL,
    -- Appended rather than inserted: the insert is positional, so a new column
    -- in the middle would silently shift every value after it.
    base      TEXT,
    walk      TEXT
);
"""

SQL_CREATE_TRACES = """
CREATE TABLE IF NOT EXISTS traces (
    subject TEXT NOT NULL,
    t REAL NOT NULL,
    {sensor_columns},
    total_l REAL, total_r REAL,
    anom_l INTEGER, anom_r INTEGER
);
""".format(sensor_columns=", ".join(f"{s} REAL" for s in SENSORS))

SQL_CREATE_INDEX = "CREATE INDEX IF NOT EXISTS traces_subject_t ON traces (subject, t);"

SQL_INSERT_TRACES = "INSERT INTO traces (subject, {columns}) VALUES (?, {marks});".format(
    columns=", ".join(TRACE_COLUMNS),
    marks=", ".join("?" * len(TRACE_COLUMNS)),
)


def connect(db_path=DB_PATH, read_only=False):
    """Open the trace database.

    ``check_same_thread=False`` because the ASGI worker serves callbacks from
    both the event loop and a thread pool. Reads are serialised by SQLite and
    nothing writes at runtime, so this is safe here.
    """
    if read_only and not os.path.exists(db_path):
        raise DataMissing(
            f"{db_path} is missing — run `python fetch_data.py` to build it."
        )
    return sqlite3.connect(db_path, check_same_thread=False)


def ingest(subject_ids=None, data_dir=DATA_DIR, db_path=DB_PATH, log=print,
           walks=None, recordings=None):
    """Load recordings and demographics into SQLite. Idempotent per recording."""
    if recordings is None:
        if subject_ids:
            recordings = [(s, w) for s, w in available_recordings(data_dir)
                          if s in set(subject_ids)
                          and (walks is None or w in walks)]
        else:
            recordings = available_recordings(data_dir)
    if not recordings:
        raise DataMissing(
            f"No recordings in {data_dir} — run `python fetch_data.py` first."
        )

    demographics = read_demographics(data_dir)
    conn = connect(db_path)
    try:
        conn.execute(SQL_CREATE_SUBJECTS)
        conn.execute(SQL_CREATE_TRACES)
        conn.execute(SQL_CREATE_INDEX)

        for subject, walk in recordings:
            rec_id = recording_id(subject, walk)
            path = os.path.join(data_dir, record_filename(subject, walk))
            if not os.path.exists(path):
                raise DataMissing(f"{path} is missing — run `python fetch_data.py`.")

            frame = detect_anomalies(read_record(path))
            rows = [
                (rec_id, *row)
                for row in frame[TRACE_COLUMNS].itertuples(index=False, name=None)
            ]

            conn.execute("DELETE FROM traces WHERE subject = ?;", (rec_id,))
            conn.executemany(SQL_INSERT_TRACES, rows)

            if subject in demographics.index:
                info = demographics.loc[subject]
            else:
                info = pd.Series(dtype=object)

            def field(name):
                value = info.get(name)
                return None if value is None or pd.isna(value) else float(value)

            durations, _, _ = stride_intervals(frame["total_l"], frame["t"])
            stride_cv = stride_variability(frame["total_l"], frame["t"])
            stride_median = float(np.median(durations)) if durations.size else None

            conn.execute(
                "INSERT OR REPLACE INTO subjects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                (
                    rec_id,
                    str(info.get("Study", subject[:2])),
                    int(field("Group") or 0),
                    int(field("Gender") or 0),
                    field("Age"), field("Height"), field("Weight"),
                    field("HoehnYahr"), field("UPDRS"), field("UPDRSM"), field("TUAG"),
                    float(frame["t"].iloc[-1]),
                    len(frame),
                    None if stride_cv != stride_cv else stride_cv,
                    stride_median,
                    float(frame[SENSORS].to_numpy().max()),
                    subject,
                    walk,
                ),
            )

            median = np.median(durations) if durations.size else 0
            irregular = (
                int(np.sum(np.abs(durations - median) > STRIDE_TOLERANCE * median))
                if durations.size else 0
            )
            log(
                f"  {rec_id} ({WALK_LABELS.get(walk, walk)}): "
                f"{len(frame):,} samples over {frame['t'].iloc[-1]:.1f}s, "
                f"{durations.size} strides, stride-time CV {stride_cv:.1f}%, "
                f"{irregular} irregular ({100 * irregular / max(durations.size, 1):.1f}%)"
            )
        conn.commit()
    finally:
        conn.close()
    return [recording_id(s, w) for s, w in recordings]


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------

@dataclass
class Subject:
    """One row of the ``subjects`` table, with display helpers."""

    subject: str
    study: str
    grp: int
    gender: int
    age: float
    height: float
    weight: float
    hoehnyahr: float
    updrs: float
    updrsm: float
    tuag: float
    duration: float
    samples: int
    stride_cv: float
    stride_median: float
    sensor_peak: float
    base: str = None
    walk: str = USUAL_WALK

    @property
    def group_label(self):
        return GROUP_LABELS.get(self.grp, "Unknown")

    @property
    def gender_label(self):
        return GENDER_LABELS.get(self.gender, "Not recorded")

    @property
    def study_label(self):
        return STUDY_LABELS.get(self.study, self.study)

    @property
    def condition_label(self):
        return WALK_LABELS.get(self.walk, self.walk)

    @property
    def label(self):
        age = f"{self.age:.0f}y" if self.age else "age n/a"
        condition = "" if self.walk == USUAL_WALK else f", {self.condition_label}"
        return f"{self.subject} — {self.group_label}, {age}{condition}"


def subjects(conn):
    """Every ingested subject, controls first then patients, by id."""
    rows = conn.execute(
        "SELECT * FROM subjects ORDER BY grp, subject;"
    ).fetchall()
    if not rows:
        raise DataMissing("The database holds no subjects — run `python fetch_data.py`.")
    return [Subject(*row) for row in rows]


def subject_info(conn, subject_id):
    """One subject, or ``None`` when the id is unknown."""
    row = conn.execute(
        "SELECT * FROM subjects WHERE subject = ?;", (subject_id,)
    ).fetchone()
    return Subject(*row) if row else None


def _frame(rows):
    frame = pd.DataFrame.from_records(list(rows), columns=TRACE_COLUMNS)
    return frame.sort_values("t", ignore_index=True)


def traces_window(conn, subject_id, t_end, window_seconds):
    """The last ``window_seconds`` of data at or before ``t_end``."""
    rows = conn.execute(
        f"SELECT {', '.join(TRACE_COLUMNS)} FROM traces "
        "WHERE subject = ? AND t <= ? AND t >= ? ORDER BY t;",
        (subject_id, float(t_end), float(t_end) - float(window_seconds)),
    )
    return _frame(rows)


def traces_between(conn, subject_id, t_from, t_to):
    """Everything recorded between two offsets, in seconds from the start."""
    lo, hi = sorted((float(t_from), float(t_to)))
    rows = conn.execute(
        f"SELECT {', '.join(TRACE_COLUMNS)} FROM traces "
        "WHERE subject = ? AND t BETWEEN ? AND ? ORDER BY t;",
        (subject_id, lo, hi),
    )
    return _frame(rows)


def recording_duration(conn, subject_id):
    """Length of a subject's recording in seconds, 0 when unknown."""
    row = conn.execute(
        "SELECT duration FROM subjects WHERE subject = ?;", (subject_id,)
    ).fetchone()
    return float(row[0]) if row and row[0] else 0.0
