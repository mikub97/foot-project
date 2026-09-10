#!/usr/bin/env python3
"""DTW gait space: how far a cognitive load moves a person's walking.

A study-owned step, per `contracts/step.md` — its input is this study's own
pipeline, so it belongs here rather than in the shared package.

DIMS's shipped analyses ask *how much* two signals are coupled. This one asks
how one must be stretched in time to match the other, and places every
recording in the space those distances define. Each participant here was
recorded twice, walking and walking while counting backwards in sevens, so the
distance between their two points is the effect of the load on their gait.

Reads   assets/timeseries/{videoID}_{measure}.csv
Writes  assets/dtw/gaitspace.json
Gated   "include_dtw": true
Tunes   config.json -> analysis.dtw.{measure,sample_rate_hz,band_fraction}
"""

import argparse
import json
import os

import numpy as np

from dims_analysis.common import assets, results, series

DEFAULTS = {"measure": "leftForce", "sample_rate_hz": 20.0, "band_fraction": 0.10}


def znorm(values):
    """Zero mean, unit variance.

    Without this, DTW compares body weights: a heavier walker's force trace
    sits higher everywhere and the distance is dominated by that offset rather
    than by the shape of the gait cycle.
    """
    values = np.asarray(values, dtype=float)
    spread = values.std()
    return (values - values.mean()) / (spread if spread > 0 else 1.0)


def dtw_distance(a, b, band_fraction):
    """Band-constrained DTW cost, normalised by path length.

    The Sakoe-Chiba band stops the alignment matching the start of one
    recording to the end of another, which for two minutes of walking is never
    the right answer. Normalising by ``n + m`` is what makes recordings of
    different length comparable.
    """
    a, b = znorm(a), znorm(b)
    n, m = a.size, b.size
    band = max(int(band_fraction * max(n, m)), abs(n - m) + 1)

    previous = np.full(m + 1, np.inf)
    previous[0] = 0.0
    for i in range(1, n + 1):
        current = np.full(m + 1, np.inf)
        lo = max(1, int(i * m / n) - band)
        hi = min(m, int(i * m / n) + band)
        cost = np.abs(a[i - 1] - b[lo - 1:hi])
        for offset, j in enumerate(range(lo, hi + 1)):
            current[j] = cost[offset] + min(previous[j], previous[j - 1], current[j - 1])
        previous = current
    return float(previous[m] / (n + m))


def embed(matrix):
    """Classical MDS to two dimensions.

    Torgerson's method — double-centre the squared distances, take the two
    leading eigenvectors. No optimisation, so the same input always draws the
    same picture.
    """
    squared = np.asarray(matrix, dtype=float) ** 2
    size = squared.shape[0]
    centering = np.eye(size) - np.ones((size, size)) / size
    gram = -0.5 * centering @ squared @ centering
    values, vectors = np.linalg.eigh(gram)
    order = np.argsort(values)[::-1][:2]
    coords = vectors[:, order] * np.sqrt(np.maximum(values[order], 0))
    total = np.maximum(values, 0).sum()
    return coords, float(values[order].sum() / total) if total else 0.0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    config = json.load(open(args.config))

    params = dict(DEFAULTS)
    params.update((config.get("analysis") or {}).get("dtw") or {})
    meta = config.get("recordings") or {}

    loaded = {}
    for video_id in config["videoIDs"]:
        path = assets.resolve(
            f"assets/timeseries/{video_id}_{params['measure']}.csv")
        found = series.load_or_none(path, min_points=100)
        if found is None:                  # already explained why, on stdout
            continue
        time, values = found
        # Decimate to the analysis rate: DTW is O(n*m), and at 100 Hz two
        # minutes of walking is 12 000 samples a side.
        period = float(np.median(np.diff(time))) if time.size > 1 else 0.0
        step = max(1, int(round((1.0 / params["sample_rate_hz"]) / period))) if period else 1
        loaded[video_id] = np.asarray(values, dtype=float)[::step]

    ids = list(loaded)
    if len(ids) < 2:
        print("  DTW: fewer than two usable recordings — nothing to compare")
        return

    print(f"  DTW: {len(ids)} recordings, {len(ids) * (len(ids) - 1) // 2} pairs "
          f"at {params['sample_rate_hz']:g} Hz")
    matrix = np.zeros((len(ids), len(ids)))
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            d = dtw_distance(loaded[ids[i]], loaded[ids[j]], params["band_fraction"])
            matrix[i, j] = matrix[j, i] = d

    coords, explained = embed(matrix)

    # The only comparison this study can honestly make. These participants
    # never walked together, so a distance between two of them measures nothing
    # about coordination -- it is the chance level. Same-person distances are
    # the signal.
    base_of = {r: (meta.get(r) or {}).get("base", r) for r in ids}
    within, between = [], []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            bucket = within if base_of[ids[i]] == base_of[ids[j]] else between
            bucket.append(matrix[i, j])
    within, between = np.array(within), np.array(between)

    permuted = None
    if within.size and between.size:
        pool = np.concatenate([within, between])
        rng = np.random.default_rng(0)
        null = np.array([rng.choice(pool, within.size, replace=False).mean()
                         for _ in range(20000)])
        permuted = float((null <= within.mean()).mean())
        print(f"  DTW: within-subject mean {within.mean():.4f} (n={within.size}), "
              f"between {between.mean():.4f} (n={between.size}), p={permuted:.4f}")

    payload = {
        "payload_version": 2,
        "measure": params["measure"],
        "sample_rate_hz": params["sample_rate_hz"],
        "band_fraction": params["band_fraction"],
        "ids": ids,
        "matrix": [[round(float(v), 6) for v in row] for row in matrix],
        "coords": [[round(float(x), 6), round(float(y), 6)] for x, y in coords],
        "explained": round(explained, 4),
        "meta": {r: meta.get(r, {}) for r in ids},
        "within_subject": {
            "n": int(within.size),
            "mean": round(float(within.mean()), 6) if within.size else None,
            "values": [round(float(v), 6) for v in within],
        },
        "between_subject": {
            "n": int(between.size),
            "mean": round(float(between.mean()), 6) if between.size else None,
        },
        "permutation_p": None if permuted is None else round(permuted, 4),
        "permutations": 20000,
    }

    out = assets.resolve("assets/dtw/gaitspace.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    results.write_payload(out, payload)
    print(f"  DTW: wrote {out} — 2-D embedding explains {100 * explained:.1f}%")


if __name__ == "__main__":
    main()
