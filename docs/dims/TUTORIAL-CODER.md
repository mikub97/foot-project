# DIMS tutorial — the terminal path

*Walkthrough report, GAIT-attempt, 2026-09-10. Followed from
`docs/getting-started.md` immediately after the no-code path failed.
Companion to [TUTORIAL-NONCODER.md](TUTORIAL-NONCODER.md).*

## Verdict

- **It works, first time, end to end.** Clean clone to a rendered dashboard of my
  own data in **under 3 minutes**, with no guessing and no reading of source.
- **`getting-started.md` is the best documentation in the project** — ordered,
  accurate, and honest about what it does not do. It states the Python 3.13
  mediapipe limitation up front instead of letting you find it.
- **The data contract fits gait data almost exactly**: `{videoID}_{dataType}.csv`,
  `Time` in seconds ascending. My adapter is ~100 lines and translates nothing.
- **The gap between the two paths is the whole finding.** Same software, same
  install, same 10 minutes of prose: the coder path succeeds unaided and the
  no-code path cannot be started. The project is not short of quality; it is
  short of one link.
- **Two defects surfaced only because I ran it on unfamiliar data** — a warning
  that fires on rounding, and a figure titled for a different study.

## What happened

| Time | Step | Outcome |
|---|---|---|
| 03:52 | `git clone`, `pip install -e ./dims` in a fresh venv | 10 s, clean |
| 03:52 | `dims-case new gaitpd --visibility public` | < 1 s. Scaffold complete, core pinned at 1.4.1 |
| 03:53 | Write the adapter, export 6 recordings | 1 s for 12 CSVs |
| 03:53 | `dims-analysis run` | 20 s: RQA + cross-RQA over 6 recordings |
| 03:53 | `serve.py --port 8137` | **crashes** — port is positional |
| 03:53 | `serve.py 8137` | serving |
| 03:54 | Dashboard in the browser | **renders, with no video in the study** |

Time to first render of my own data: **under 3 minutes**. The no-code path, on
the same machine, in the same session, never started.

## What is genuinely good

**The warnings.** This, unprompted, on my data:

> the threshold could not reach the 7.0% target; this analysis is at 8.1%. Many
> exactly-equal distances (a quantised or partly-still signal) put the percentile
> on a plateau. Metrics that depend on the recurrence rate, DET and LAM among
> them, are not comparable with a recording analysed at 7.0%.

That is a real threat to comparability, correctly diagnosed from the signal, in
plain language, attached to the analysis that suffers from it. I have not seen
another tool in this space do it, and it is the reason I take the project
seriously.

**The privacy model.** `--visibility private` installs a pre-commit hook, a
pre-push hook and a CI check to stop recordings of identifiable people reaching
git. This is a correct reading of how research data actually leaks.

**The extension contract.** `contracts/tab.md` — one self-registering file,
`onTimeUpdate(app, time, windowSize)`, a stated list of what you may touch on
`app` and an instruction to open an issue rather than reach past it. Built-in
tabs use the same API, so it cannot rot unnoticed. I replaced the video component
through the documented `DIMS.extendHost` seam without editing the core once.

## What broke

| | Finding | Filed |
|---|---|---|
| `BUG` | The window warning fires on sample-grid rounding and prints both numbers identically — "the 20 s window was shortened to 20 s" over a **1.5 ms** difference. **12 of 18** window reports in my study carried it. | [PR #19](https://github.com/dims-network/dims/pull/19) |
| `BUG` | Every time-series figure is titled "ROI Synchrony Over Time" — an fNIRS leftover, over my foot-force traces. Docs say "Ignore it". | [PR #20](https://github.com/dims-network/dims/pull/20) |
| `BUG` | `Segment (NaN s – NaN s)` before the first playhead click; 404 console noise for unclaimed optional assets. | [#22](https://github.com/dims-network/dims/issues/22) |
| `FRICTION` | `serve.py --port` crashes; `dims-builder --help` starts the server. | [#23](https://github.com/dims-network/dims/issues/23) |

Both bugs are of the same species and neither is visible from inside the project:
they are wrong only when the data is not the data the tab was written for. That
is the specific value an outsider brings, and it argues for running the pipeline
on a deliberately foreign dataset now and then.
