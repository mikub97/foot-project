# DIMS field notes — GAIT-attempt

Append-only. Written as I go, not reconstructed afterwards: the confusion is the
evidence, and a tidy retrospective would launder it into hindsight. Committed
incrementally, so the git history of this file records the order in which things
went wrong.

**Who is writing.** A researcher in embodied cognition working on gait dynamics
(`gait-pressure-dashboard` — foot-pressure recordings, PhysioNet gaitpdb, 16
force sensors at 100 Hz). Other studies in the same line use body-worn IMUs.
Came to DIMS from the outside, via the project page, wondering whether the next
study could live in it.

**Entry kinds**

| Kind | What it captures |
|---|---|
| `BUG` | it does the wrong thing — with a reproduction |
| `DOC` | docs disagree with the code, omit a step, or assume an unnamed tool |
| `INCONSISTENCY` | two parts of DIMS disagree with each other |
| `GAP` | not broken, but there is nowhere to put something I have |
| `FRICTION` | it works, and it cost me more than it should have |
| `IDEA` | something DIMS could be |
| `ATTENTION` | needs a decision from the project owner |
| `TASTE` | I disagree but cannot call it wrong — flagged so the report can discount it |

Every entry: timestamp, kind, location, expected vs. actual.

---

## 2026-09-10 — Phase 0, before first contact

**03:44 `NOTE`** Branch `GAIT-attempt/dims-integration` created off
`modernize-dash4-gaitpdb`. Nothing about DIMS read yet. The only thing I know is
the URL: <https://dims-network.github.io/>.

I noticed `WimPouw/DIMS_dashboard` earlier while researching the project's
network and deliberately did not open it. That matters for what follows: the
non-coder walkthrough below is a genuine cold read.

**03:44 `NOTE`** Method for Phase 1a, stated before I start so I cannot quietly
relax it. While following the **non-coder** path I may not: open the source, use
a terminal to unblock myself, guess a command from experience, or fix anything.
Where I get stuck, that is the finding. Where I *could* have rescued myself as a
programmer but a non-coder could not, it is logged `FRICTION` and says so.

## 2026-09-10 — Phase 1a, non-coder path (cold read)

**03:44 `NOTE`** Start. Entry point <https://dims-network.github.io/>. Nav is
Home / Tutorial / Set up / Docs / GitHub. Version v1.0.1. Landing claim: "An open
family of tools for multimodal social-interaction data" — time series, video,
transcripts and ELAN annotations on one timeline; recurrence, cross-recurrence,
cross-wavelet coherence, cross-effector networks.

**03:45 `NOTE`** Two landing-page claims that matter to me before I touch
anything, because they pre-empt things I had planned to propose:

- DIMS already **compares coherence against simulated chance levels** ("unrelated
  signals score around 0.25, not zero"). I had planned to contribute
  surrogate-pair nulls as if they were missing. They are not. Adjusting: the
  contribution is to reuse that machinery, not to invent it.
- DIMS already has **cross-effector networks** — i.e. the idea that two coupled
  streams need not be two people is *already in the design*. My planned framing
  ("a pair of streams need not be a pair of people") is therefore not a novel
  claim to DIMS. Kept as a framing for gait; dropped as a critique.

Recording this now, before it is tempting to pretend I knew.

**03:45 `DOC` — the no-code path never says how to start** — severity: high.
`tutorial.html` sells a "no-code builder": prerequisites Python 3.10–3.12 and
"dims-network/dims — clone it, or download the ZIP and unzip it", "About 10
minutes", then Step 1 opens mid-wizard at "Your Study".
*Expected:* having installed Python and unzipped the folder, something tells me
how to open the wizard.
*Actual:* nothing on the tutorial page launches it. `setup.html` points the other
way — "if you would rather click through a wizard, the tutorial does that" — so
the two pages each defer to the other. The launcher exists (`dims-builder`
appears in the docs' CLI reference) but only in the terminal reference a
non-coder never reaches.
*Consequence:* the no-code path's first action is an undocumented terminal
command. A non-coder is stopped at step zero with no error message to search for
— the worst kind of stuck, because nothing has visibly failed.
*Fix:* one line at the top of `tutorial.html`, before Step 1: the exact command,
plus what a successful launch looks like.

**03:45 `FRICTION` — "clone it, or download the ZIP"** — severity: medium.
"Clone" is unglossed on a page addressed to non-coders. The ZIP alternative is
the right instinct, but `setup.html` then warns "Do not copy the scaffold
directory by hand. It has no `vendor/`, so the page loads eight script tags that
404." A ZIP user has no way to know whether that warning applies to them.
*Note per method:* I know what cloning is. A non-coder does not, and this is
exactly the kind of gap I must not silently step over.

**03:46 `NOTE`** Docs structure read (index only, no source). Tabs shipped:
Time series, RQA, Cross-RQA, Cross-wavelet, Cross-effector network, ELAN. **No
DTW anywhere** — so a DTW/alignment tab is a real addition, not a duplicate.
Extension seams are documented and sound promising: "Add a tab" = "one
self-registering file", "Add an analysis" = "one Python class". There is a
`window.DIMS` browser API and a host runtime owning "the shared time axis, the
tab lifecycle, the video" — which is the seam my foot-map renderer needs.

**03:47 `INCONSISTENCY` — the public site is three minor versions stale** —
severity: high, cost: one line.
*Location:* <https://dims-network.github.io/> vs `pyproject.toml`.
*Expected:* the front page names the current release.
*Actual:* the page says **v1.0.1** (twice); the repository is **v1.4.1**.
*Why it matters to an outsider:* the version on the front page is the number I
would cite in a methods section and pin in a study config. Getting it wrong is
not cosmetic.

**03:47 `BUG` (documentation) — the front page still quotes a figure the project
already retracted** — severity: high, cost: one sentence.
*Location:* <https://dims-network.github.io/> — "signals score about 0.25, not 0".
*Expected:* the site agrees with the code and the changelog.
*Actual:* `CHANGELOG.md` for v1.4.1 says exactly this number was removed from the
README because it "merged a mean with a 95th percentile and generalised one
study's measurement into a range", and that "The README no longer quotes a
number". The website was never updated, so the retracted figure is still the
first quantitative claim a new reader meets.
*Repro:* `curl -s https://dims-network.github.io/ | grep 0.25`
*Fix:* apply the same correction the README got; or, better, generate the site's
claims from the same source as the docs so the two cannot drift again.
*Note:* I believed this figure on first read and wrote it into my own notes at
03:45 as a reason to change my plans. That is the actual cost of a stale site.

**03:47 `ATTENTION` — I disturbed your environment and put it back.**
`pip install -e ./dims`, run verbatim from `setup.html`, went into your **conda
base env** and uninstalled the `dims-network` already there (recorded 1.1.0),
replacing it with an editable install pointing into my throwaway clone. I
restored it: `dims-network` is editable again from
`/Users/m11/Documents/codes/DIMS_ALL/dims`, your own checkout, now recording
1.4.1 (that directory is at 1.4.1; the 1.1.0 was stale install-time metadata).
Your checkout itself was never read or modified — outsider discipline, and it
may hold unpublished work. All my work is now in an isolated venv.
*The finding underneath:* `setup.html` gives `pip install -e ./dims` with **no
virtual environment step**. On a machine with conda or a system Python that is a
global mutation, and for the one reader most likely to already have a DIMS
install — a returning user — it silently replaces it. A `python -m venv` line
before the `pip` line would cost nothing.

**03:47 `NOTE`** Isolated venv install: 10 s, clean. Console scripts provided:
`dims-analysis`, `dims-case`, `dims-builder`.

## 2026-09-10 — Phase 1b/2/3, coder path with my own data

**03:49 `BUG` — the builder's own fix-hint is unreachable** — severity: high,
cost: 4 lines. `apps/builder/dims_builder/__main__.py` docstring says
`pip install "dims-network[builder]"`, but line 16
(`from dims_builder.server import create_app`) raises `ModuleNotFoundError:
No module named 'flask'` before anything prints. `dims_builder/project.py`
already does this correctly twice ("Reinstall with: pip install
'dims-network[builder]'"), so only the entry point is missing it.
*Fix:* guard that import, print the line the docstring already has.

**03:49 `FRICTION` — `dims-builder --help` starts the server.** No argument
parsing; it launches the wizard and opens a browser. Cost me a 120 s timeout.

**03:52 `NOTE`** Coder path is *good*. `docs/getting-started.md` is accurate,
ordered and honest. `dims-case new gaitpd --visibility public` scaffolds in
under a second. The Private/Public split — pre-commit hook, pre-push hook and a
CI check to keep recordings of identifiable people out of git — is better than
anything in my own project.

**03:53 `NOTE`** The data contract is a near-exact match for gaitpdb:
`{videoID}_{dataType}.csv`, `Time` in seconds ascending. My adapter is 100 lines
and adds nothing. `getting-started.md` even anticipates the neighbouring
ecosystem: "Tools that emit milliseconds — several EnvisionBox modules do —
need a unit change and a rename."

**03:53 `E2` — RESULT: a study with no video works.** This was my headline
question and the answer is yes. Six recordings, no `.mp4` anywhere, `dims-case`
→ adapter → `dims-analysis run` → `serve.py`, and the dashboard renders with
Time series, RQA, Cross-RQA and ELAN tabs live. **This is the finding that
decides adoption for me**, and it is positive.
Caveats, all cosmetic: the video panel still renders, labelled
`Segment (NaNs – NaNs)`; and the browser console logs 4 × 404 for absent
transcripts/videos. Optional assets should be absent quietly when the config
does not claim them.

**03:53 `E3`/`E6` — RESULT: 6 recordings, RQA + cross-RQA, 20 s wall clock.**
12 119 samples at 100 Hz decimated to 25 Hz (3 030 points) before export. The
analyses downsample again for the browser ("Reduced 3030 -> 432 points, block
average / density-preserving"). No throughput problem at this scale.

**03:53 `ATTENTION` — my 25 Hz decimation is a decision, not a default.**
Recurrence is O(n²); 12 119 samples is a 147-million-cell matrix per pair. I
decimate to 25 Hz, which preserves every stride event (the fastest feature is a
~0.1 s heel-strike rise) but is my choice, in `dims_adapter/export.py`.
Decimation, not interpolation — an interpolated force is a number nobody
measured. *What would change if you disagree:* raise `TARGET_HZ`; the analyses
will still re-reduce for the browser, so the cost is CPU, not fidelity.

**03:54 `BUG` — the window warning contradicts itself and cries wolf** —
severity: high, cost: two lines.
*Location:* `packages/dims-analysis/dims_analysis/common/window.py`, `_warning()`.
*Actual output:* "the 20 s window was shortened to **20 s**, because a 121.2 s
recording cannot hold 20 of the requested windows. DET and LAM ... are not
comparable with an analysis at **20 s**."
*Payload:* `length_requested_sec: 20.0`, `length_used_sec: 19.9985`.
Two separate defects:
1. **Formatting.** `{requested:g}` and `{used:.4g}` both render as `20`, so the
   sentence says a value was changed to itself. On my data this happened in
   **12 of 12** warnings — every one that fired.
2. **Threshold.** `length_moved` fires when the difference exceeds `1e-9` s —
   one nanosecond. Here the difference is **1.5 ms, 0.0075 %**, and the warning
   declares DET and LAM "not comparable" over it. It also says the recording
   "cannot hold 20 of the requested windows" while reporting `n_windows: 102`.
*Why this matters more than it looks:* DIMS's warnings are, elsewhere, the best
thing in it — the recurrence-rate plateau warning is genuinely excellent science
communication. A warning that fires on a 1.5 ms rounding difference teaches
users to ignore the channel that carries the real ones.
*Fix:* compare against one sample or a percentage of the window, not 1e-9; and
format both numbers at a precision that can distinguish them.

**03:54 `BUG` — the time-series chart is titled for a study it is no longer
about** — severity: medium, cost: ~5 lines.
`packages/dims-tabs/timeseries.js:82` hardcodes
`ROI Synchrony Over Time for Video ${videoID}`. My foot-pressure traces are
labelled as ROI synchrony. `docs/tabs/timeseries.md:31` is admirably honest
about it — "a leftover from the fNIRS study the tab was first written for and is
wrong for a tab that plots any measure at all ... **Ignore it**" — but
documenting a wart is not fixing it, and "ignore it" is advice a reader cannot
follow when the title is the first thing on the figure. `config.schema.json`
already carries `title` and `subtitle`, so the plumbing exists.
*Fix:* default the figure title to the study title, allow an override.
*Note:* for a project whose stated scope is "multimodal social-interaction
data", a hardcoded fNIRS label on the most-used tab is the clearest signal of
where the generality is aspirational.

**03:53 `FRICTION` — `serve.py --port 8137` crashes.** `ValueError: invalid
literal for int() with base 10: '--port'`; the port is positional
(`serve.py 8137`). Cost: one restart.

## 2026-09-10 — Phase 4, the feet in the video slot

**04:00 `RESULT` — done, and the seam was clean.** The video component is
`window.TimeRangeVideo`, a React component taking `{src, startTime, endTime,
title}`, mounted by `DIMSApp.updateVideos(clickTime, windowSize)` into
`#fullVideoContainer` and `#segmentVideoContainer`. I replaced the *rendering*
rather than the component, by overriding `updateVideos` through the documented
`DIMS.extendHost` seam — no reaching into internals, no core edit. 173 lines of
JS in the study's own `tabs/`.

- `#fullVideoContainer` → the two feet at the playhead: 16 sensors sized and
  coloured by force, both centres of pressure, the colour scale pinned to the
  recording's peak.
- `#segmentVideoContainer` → the participant: group, study, age, sex, body,
  Hoehn & Yahr, UPDRS, stride time, stride-time variability.

The geometry, the outline path and the colour ramp are all generated by the
**same Python that draws my Dash dashboard** (`figures._foot_outline`,
`figures.PRESSURE_SCALE`) and shipped in the asset, so the two renderings cannot
drift. This is the thesis of the whole exercise made concrete: *a video
component is a function from a timestamp to a picture, and so is a pressure
map.* DIMS did not have to be told my data has no camera.

**04:00 `BUG` — `Segment (NaNs – NaNs)`** — severity: low, cost: one line.
`updateVideos` is called once before any playhead click, and
`` `Segment (${startTime.toFixed(1)}s – …)` `` renders `NaNs` because
`clickTime` is undefined. Visible on every fresh load, with or without video.
*Fix:* default the time to 0 (or the recording start) before formatting.

**04:00 `GAP` — the panel headings are hardcoded to video** — severity: low.
`index.html` hardcodes `<h4>Videos</h4>` and `<h4>Video Transcript</h4>`. With
the video slot repurposed they label the wrong thing; I retitled them in my own
study to "Recording" and "Notes", which is a study-local patch to a core
scaffold assumption. *Fix:* let the scaffold take these from `config.json`, as
it already does for `title` and `subtitle`.

**04:00 `NOTE`** Screenshot evidence: `images/feet-replacing-video.png` shows
the hardcoded **"ROI Synchrony Over Time for Video GaPt03"** sitting directly
above two foot-force traces. That is the clearest single illustration of the
`timeseries.js:82` finding.

