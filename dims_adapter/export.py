"""gaitpdb -> DIMS study assets.

    python -m dims_adapter.export /path/to/case-gaitpd

Writes one CSV per measure per subject into ``assets/timeseries/`` and rewrites
``config.json`` to match. Does not touch anything else in the study.
"""

import argparse
import json
import os
import sys

import numpy as np

import gaitdata

#: DIMS reads whole series into the browser and the recurrence analyses are
#: O(n^2) in samples. 100 Hz over two minutes is 12 119 samples, which is a
#: 147-million-cell recurrence matrix per pair. 25 Hz keeps every stride event
#: (the fastest thing here is a ~0.1 s heel-strike rise) while cutting the
#: matrix 16-fold. Recorded as a decision, not a default: see FIELD-NOTES.
TARGET_HZ = 25.0

#: What each foot's total ground reaction force is called in the study. These
#: become the `dataTypes` DIMS offers in its dropdowns, so they are named for a
#: reader, not for the database.
MEASURES = {"leftForce": "total_l", "rightForce": "total_r"}


def resample(frame, target_hz=TARGET_HZ):
    """Every nth row, so the series lands near ``target_hz``.

    Decimation rather than interpolation: these are force readings, and an
    interpolated force is a number nobody measured.
    """
    if len(frame) < 2:
        return frame
    period = float(frame["t"].iloc[1] - frame["t"].iloc[0])
    if period <= 0:
        return frame
    step = max(1, int(round((1.0 / target_hz) / period)))
    return frame.iloc[::step]


def export_subject(conn, subject, timeseries_dir, target_hz=TARGET_HZ):
    """Write one CSV per measure for ``subject``. Returns the measure names."""
    info = gaitdata.subject_info(conn, subject)
    frame = resample(
        gaitdata.traces_between(conn, subject, 0.0, info.duration), target_hz
    )
    for data_type, column in MEASURES.items():
        path = os.path.join(timeseries_dir, f"{subject}_{data_type}.csv")
        with open(path, "w") as handle:
            handle.write(f"Time,{data_type}\n")
            for t, value in zip(frame["t"], frame[column]):
                handle.write(f"{t:.3f},{value:.4f}\n")
    return list(MEASURES)


def recording_meta(conn, subjects):
    """Per-recording facts the study's own analyses and tabs need.

    Kept in ``config.json`` rather than re-derived: the DTW step reads the
    exported CSVs and has no other way to know which two recordings are the
    same person, which is the entire basis of its within-subject comparison.
    """
    import gaitdata as _gd
    meta = {}
    for subject in subjects:
        info = _gd.subject_info(conn, subject)
        if info is None:
            continue
        meta[subject] = {
            "base": info.base or _gd.split_recording_id(subject)[0],
            "walk": info.walk,
            "condition": info.condition_label,
            "group": info.group_label,
            "age": info.age,
            "stride_cv": info.stride_cv,
        }
    return meta


def build_config(subjects, measures, title="Gait in Parkinson's Disease",
                 recordings=None):
    """A DIMS ``config.json`` for a study whose recordings have no video.

    The pairwise analyses take (left foot, right foot): in a gait recording the
    two feet are the coupled pair, which is what cross-RQA is for.
    """
    left, right = "leftForce", "rightForce"
    return {
        "title": title,
        "subtitle": "Foot-pressure replay — PhysioNet gaitpdb v1.0.0 (ODC-BY 1.0)",
        "videoIDs": list(subjects),
        "dataTypes": {s: list(measures) for s in subjects},
        "include_RQA": [left, right],
        "include_cRQA": [[left, right]],
        "include_elan": True,
        # Read by the study-local DTW tab's gate(); the core ignores it.
        "include_dtw": True,
        "timeseriesTitle": "Ground reaction force — {videoID}",
        "recordings": recordings or {},
        "analysis": {"dtw": {"measure": left, "sample_rate_hz": 20.0,
                             "band_fraction": 0.10}},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("case_dir", help="path to a study made by `dims-case new`")
    parser.add_argument("--subjects", help="comma-separated ids (default: all ingested)")
    parser.add_argument("--hz", type=float, default=TARGET_HZ)
    args = parser.parse_args(argv)

    conn = gaitdata.connect(read_only=True)
    subjects = (
        args.subjects.split(",") if args.subjects
        else [s.subject for s in gaitdata.subjects(conn)]
    )

    timeseries_dir = os.path.join(args.case_dir, "assets", "timeseries")
    if not os.path.isdir(timeseries_dir):
        sys.exit(f"{timeseries_dir} does not exist — is {args.case_dir} a DIMS study?")

    for subject in subjects:
        measures = export_subject(conn, subject, timeseries_dir, args.hz)
        print(f"  {subject}: {', '.join(measures)}")

    config_path = os.path.join(args.case_dir, "config.json")
    with open(config_path, "w") as handle:
        json.dump(build_config(subjects, MEASURES,
                               recordings=recording_meta(conn, subjects)),
                  handle, indent=2)
        handle.write("\n")
    print(f"\nwrote {config_path} — {len(subjects)} recordings at {args.hz:g} Hz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
