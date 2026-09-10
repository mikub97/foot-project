# GAIT-attempt: an outsider's evaluation of DIMS, and a gait-dynamics integration

## Context

I maintain `gait-pressure-dashboard` — a Dash 4 app that replays foot-pressure
recordings from the PhysioNet *Gait in Parkinson's Disease* database (16 force
sensors under two insoles, 100 Hz, 166 subjects with demographics and clinical
scales). I found DIMS through its GitHub organisation and want to know whether
it is worth building my gait work on top of.

Four parts, deliberately in tension:

1. **Adopt** DIMS next to my own project, in a new branch.
2. **Criticise** it — a running log of every issue in the docs and the code.
3. **Extend** it — the two-foot pressure visualisation replaces the *video
   component*; demographics sits alongside as its own panel.
4. **Report** — fixes, issues and ideas that make DIMS more usable.

I have **not** opened the DIMS repository. (I saw `WimPouw/DIMS_dashboard` in a
repo listing while researching the collaborator and did not open it.) This plan
is written from my own codebase and from domain research, with an explicit
"first contact" phase that will revise it.

**Constraints from the user.** I push as the repo owner but must *behave as an
outsider*: fork, no merges to `main`, no maintainer shortcuts. Everything is
prefixed **`GAIT-attempt`**. Full upstream flow is authorised — real issues and
PRs against the DIMS repo.

### Who this is actually for

**Me first.** I am a researcher in embodied cognition working on gait dynamics,
and in my *other* studies — not this one — the data comes from **inertial
measurement units**. So the real question behind this exercise is not "is DIMS
a nice project" but **"could I put my next study into it?"** That sets hard
requirements the gaitpdb work only partly exercises, and I will test them
anyway because they are the ones that decide adoption:

- **Many numeric channels at high rate, no camera.** IMUs give accel/gyro/mag
  per sensor at 50–200 Hz. Nothing about that is a video.
- **Several sensors, several clocks.** Body-worn units drift and start at
  different moments; alignment is the whole problem. (Pouw's own
  `xdf_desync_problem_testing` repo says this network has been bitten by it.)
- **Session and participant metadata that survives export**, because the
  contrast between conditions *is* the analysis.
- **Motion-BIDS** — the standard that exists precisely for organising motion
  data, IMUs included. If DIMS ingests or emits it, my pipeline is much shorter.

**Second, Wim Pouw's network** (Tilburg / Donders / envisionBOX, with Warsaw and
Kraków collaborators) — the people I would be sharing this with. Researching it
changed my target:

- Their core object is a **kinematic time series extracted from video** —
  MediaPipe/YOLO pose, `envisionhgdetector`, Masked-Piper, InterPerDynPipeline.
- Their analytic tradition is **dynamical systems**: smoothness, dynamic time
  warping, and **CRQA** on *interpersonal* coordination.
- **ELAN is the lingua franca** — `envisionhgdetector` emits ELAN files. Interop
  is not a nice-to-have in this network.
- **Privacy is first-class** — Masked-Piper exists to strip identity from video
  while keeping kinematics.
- envisionBOX is explicitly a *teaching* resource: "a community of learners…
  to understand embodied minds in interaction and communication."

This is the hinge of my whole approach: **my data is the same shape as theirs —
a kinematic time series — but it never had a video.** It comes from insoles, not
from a camera. So replacing the video component is not a gimmick; it is the
proof that DIMS can host a modality with no camera behind it, which is what
audio-only corpora, mocap, force plates, EMG, eye-tracking — **and the IMUs in
my own other studies** — all need too, and what Masked-Piper's privacy motive
implies people already want. Insoles are the cheapest possible test of the
seam that IMUs will later demand.

### Two verified facts that shape the work

1. **`format.txt` confirms**: walk suffix `_01` is usual walking; **`_10` (Ga
   study) is dual-task walking — serial-7 subtraction while walking.** My
   dataset already contains a cognitive-load contrast.
2. **My own project throws that away.** `record_filename()`
   ([gaitdata.py:79](gaitdata.py#L79)) hardcodes `_01`. Fixing this on the
   branch is a prerequisite, and it is the single most valuable thing I can do
   for the embodied-cognition framing.

---

## The log is the primary artefact

Everything else in this plan produces material; **the log is what turns it into
a result.** `docs/dims/FIELD-NOTES.md` is append-only and written *as I go*, not
reconstructed afterwards — a reconstruction would quietly launder my confusion
into hindsight, and the confusion is the evidence. It commits incrementally, so
the git history of the notes file is itself a record of the order in which
things went wrong.

Every entry carries a **timestamp**, a **kind**, a **location** (file, line, doc
section, or command), and **expected vs. actual**.

| Kind | What it captures |
|---|---|
| `BUG` | it does the wrong thing — with a reproduction |
| `DOC` | docs disagree with the code, omit a step, or assume an unnamed tool |
| `INCONSISTENCY` | two parts of DIMS disagree with each other — naming, units, time bases, conventions |
| `GAP` | not broken, but there is nowhere to put something I have |
| `FRICTION` | it works, and it cost me more than it should have — with the cost |
| `IDEA` | something DIMS could be; my own extensions start life here |
| `ATTENTION` | **needs Michał** — a judgment call, a decision, or something I think you'd want to see |
| `TASTE` | I disagree with a design choice but cannot call it wrong — flagged so the report can discount it |

`ATTENTION` and `TASTE` exist to keep me honest. The first stops me making your
decisions silently; the second stops me dressing up preference as a defect,
which is the standard failure mode of an outsider's evaluation.

**`ATTENTION` items do not block.** I log the item, take the most defensible
option, state the assumption in the entry, and keep going. They surface together
in the report's *Decisions I took* section, so you review them in one pass
instead of a stream of interruptions — and each one records what would change if
you decide differently.

**The report is generated from this log** — every claim traces to a dated entry,
and anything not in the log does not go in the report. Alongside the branches and
the PRs, it is the deliverable.

---

## What I bring

**My visualisation is already shaped like a video player.**
[figures.py:231](figures.py#L231) `foot_map_figure(row, peak=...)` is stateless:
one sample in, one picture out. That is exactly a video component's contract —
*a function from a timestamp to a frame*. "Replace the video" therefore means
registering a **synthetic media provider** against whatever playhead DIMS owns.
If that seam generalises it is the most valuable thing I could upstream: pose
skeletons, spectrograms and gaze heatmaps all fit the same slot.

**A clock worth not duplicating.** [app.py:194](app.py#L194) runs one coroutine
per connection whose locals *are* the replay state. DIMS's playhead must become
master and my renderer slave; two clocks on one page is the obvious failure mode
and the first thing I check.

**A hard-won lesson about colour.** `sensor_peak`
([gaitdata.py:397](gaitdata.py#L397)) exists solely so the pressure map fixes its
scale across a whole recording — otherwise the scale re-fits per frame and the
same colour means a different force from one push to the next. I expect to find
this bug in DIMS.

**Derived-vs-measured discipline.** My anomaly bands are computed from stride
timing, not supplied by the dataset, and the README, architecture doc and page
footer all say so. `_anomaly_spans()` ([figures.py:100](figures.py#L100))
already returns contiguous `(t_start, t_end)` ranges — which *is* an ELAN tier.

**Demographics.** `Subject` + `INFO_ROWS` ([app.py:45](app.py#L45)) already
render group, study, age, sex, height/weight, Hoehn & Yahr, UPDRS, stride time
and stride-time variability.

---

## Plan

### Phase 0 — arm the notebook (before first contact)
Branch **`GAIT-attempt/dims-integration`** off `modernize-dash4-gaitpdb` in
`github.com/mikub97/gait-pressure-dashboard`. Start `docs/dims/FIELD-NOTES.md`,
append-only and timestamped, each entry carrying severity, location, and
expected-vs-actual. It starts **now** so it captures the cold read rather than a
reconstruction of it.

### Phase 1 — first contact: both tutorials, in this order

DIMS ships tutorials for coders and for non-coders. I follow **both**, literally
and with a stopwatch, and each produces **its own report**. The sequence is not
arbitrary:

**1a — the non-coder tutorial first, before I have read a single line of source.**
Once I have read the code I cannot un-know it, and every later attempt to judge
the non-coder path is contaminated by knowledge a non-coder does not have. This
window exists once.

The discipline that makes it worth anything — while on this path I may **not**:
open the source, use the terminal to unblock myself, guess at a command from
experience, or fix anything. When I get stuck, that is the finding. I record the
exact step, what the docs told me to expect, what I saw instead, and what a
non-coder's only remaining option would be (ask a colleague, email the author,
give up). Any place where I *could* have rescued myself as a programmer but a
reader could not is logged as `FRICTION` with that noted explicitly — it is the
single most valuable thing I can report to a network that runs summer schools.

**1b — the coder tutorial**, same stopwatch, same literalism. Every place the
docs lie, assume an unnamed tool, or skip a step goes in the log. Recorded to
first render, and separately to first render *of my own data*.

**1c — the source read**, only once both tutorials have succeeded or failed on
their own terms. Focused on: the media/time abstraction, the annotation model,
the ingest seam, transport and update rate, and test coverage.

Non-coders are not a secondary audience here. envisionBOX exists explicitly as a
teaching resource — "a community of learners" — and Pouw's repos are full of
summer-school and workshop material. If the non-coder path is broken, DIMS fails
the audience it was built for, whatever the code quality.

### Phase 2 — the dual-task data my project is missing
Extend fetch/ingest to pull **both** `_01` and `_10` for Ga subjects, keyed by
condition rather than by subject alone. This touches `record_filename`,
`DEFAULT_SUBJECTS`, the `subjects` schema and `Subject` — following the
documented positional-insert gotcha in
[docs/architecture.md](docs/architecture.md). Then a thin `dims_adapter/` that
exports gaitpdb into whatever DIMS eats, built on existing `gaitdata` queries
without changing their public surface. Every impedance mismatch gets logged:
what DIMS demands that I cannot supply, what I have that it cannot hold.

### Phase 3 — experiments, results written down
- **E1 Cold start** — time and failure count, clean checkout to rendered view.
- **E2 Nullable media** — can DIMS open a session with **no video at all**? My
  data has none, and Masked-Piper's existence says others' effectively won't
  either. If it cannot, that is the headline finding.
- **E3 Throughput** — my stream pushes 4 Hz with 400-point downsampling
  ([figures.py:51](figures.py#L51)). Can DIMS carry a 100 Hz channel, and where
  does it fall over?
- **E4 Clock fidelity** — drift between DIMS's playhead and my sample index over
  a two-minute recording.
- **E5 ELAN round-trip** — derive stride events, push them in as annotations,
  export, diff. This is the interop test that matters to this network.
- **E6 Scale** — 6 subjects is my default; the dataset has 166.
- **E7 Multi-stream alignment (the IMU rehearsal)** — feed the same recording as
  *two independently-clocked streams* with a deliberate offset and a slow drift,
  standing in for two body-worn units. Can DIMS represent per-stream time bases
  at all, or does it assume one? This is the question that decides whether my
  next IMU study can live here, and gaitpdb lets me ask it without new hardware.

### Phase 4 — the replacement branch
Branch **`GAIT-attempt/gait-media-panel`** on my fork of DIMS. The **feet
visualisation occupies the video slot**, driven by the DIMS playhead;
**demographics is a separate adjacent panel**. Whichever seam I have to cut
through tells me the upstream fix: a hardcoded video assumption becomes an
issue, a clean seam becomes a PR.

### Phase 5 — file it, as an outsider
Issues titled `GAIT-attempt: …`, each with repro, expected-vs-actual, and a
suggested fix.

**The extension PR — a Coordination tab: two gait streams, aligned by DTW.**

The unifying claim is that **a pair of streams need not be a pair of people**.
The same alignment machinery answers three questions at three scales:

| The two streams | What it measures |
|---|---|
| left foot vs right foot, one walk | interlimb coordination |
| `_01` vs `_10`, one participant | **cognitive load as displacement** |
| participant A vs participant B | interpersonal coordination |

Why DTW is the right instrument: the **warping path is the finding**, not a
by-product. It says how much one gait must be stretched or compressed in time to
match another, which is exactly what changes under load and exactly what a
dashboard can draw. Pouw's network already speaks it — `envisionhgdetector`
ships DTW distance matrices and gesture-similarity spaces, and envisionBOX has a
"gesture kinematics spaces / dynamic time warping" module. This is the same
figure for feet.

The tab, in build order:

1. **Pair picker** — any two streams from the table above.
2. **Alignment view** — the two traces with the warping path drawn between them.
3. **Distance matrix** across the cohort.
4. **Gait space** — embed the matrix in 2D. Each participant appears twice,
   usual and dual-task; **the arrow between the two is the cognitive-load
   effect.** This is the figure the whole exercise is for, and it is the direct
   analogue of their gesture-kinematics space.
5. **Surrogate null** — see below.

**The honest problem, and why it is an asset.** gaitpdb participants never
walked together — separate sessions, separate studies, separate labs. Any
"synchrony" I compute between two of them is *by construction* spurious. Two
consequences, and both are good:

- I must build the **surrogate-pair null distribution** — shuffled pairings of
  people who never met — because it is the only defensible thing to compute on
  this data. That machinery is precisely the control that real dyadic studies
  need, and it is the part such tools usually lack.
- So the tab ships with its null already built, and works unchanged the day real
  dyadic data arrives — which this network *has*: InterPerDynPipeline is
  literally two people being tracked at once.

`ATTENTION` items I will log rather than decide quietly: **the speed confound**
(comparing an 82-year-old patient walking at 0.778 m/s against a control
conflates gait *shape* with gait *rate*, and DTW is only partly blind to it —
the report must say which normalisation I chose and what it costs), and **what
signal to warp** (raw total force, stride-interval series, or time-normalised
stride cycles — they answer different questions).

Grounding: spontaneous interpersonal gait synchronisation is well established in
side-by-side walking, and there is existing work on **dual-tasking's effect on
that synchronisation** — so the cognitive-load axis and the pairing axis are
already joined in the literature, not only in this dashboard.

Supporting PRs, in order of confidence: ELAN export of derived events;
provenance-tagged derived tracks (rule + parameters recorded, visually distinct
from human coding); the synthetic-media provider interface.

### Phase 6 — the report
Three documents, all generated from the log, every claim tracing to a dated
entry.

**The two tutorial reports** are written in Phase 1, at the time, not
retrospectively — `TUTORIAL-NONCODER.md` before any source read, then
`TUTORIAL-CODER.md`. Each follows the same shape so they can be read side by
side: the step-by-step timeline with elapsed time, time-to-first-render, every
blocker with what a reader would do next, screenshots of what I actually saw
(including the failures), and a verdict on whether someone could complete it
unaided. The comparison between the two is itself a finding — a large gap
between them means the project has a documentation audience it is not serving.

**`docs/dims/REPORT.md`** is the final evaluation, drawing on both.

1. **Findings** — bugs, doc defects and inconsistencies, each with a
   reproduction and a proposed fix, cross-referenced to the `GAIT-attempt`
   issue it became.
2. **Gaps and frictions** — what DIMS has nowhere to put, and what it made me
   pay for. Ranked cost against benefit.
3. **Ideas and extensions** — including the DTW Coordination tab, with
   the reasoning that led there.
4. **Decisions I took** — every `ATTENTION` item, the call I made, and the
   assumption it rests on, so a disagreement is easy to spot and reverse.
5. **Adoption verdict** — the part I actually care about: **would I put my next
   IMU study in DIMS, and what would have to be true first?** A short list of
   blocking gaps, so it is answerable rather than rhetorical.

**Voice: outsider throughout, and publishable.** Written as an external
researcher evaluating DIMS for adoption — constructive enough to forward to Wim
or attach to an issue. Section 3 keeps me honest about which complaints are
really "DIMS is not the tool I would have written": `TASTE` entries are reported
*as* taste, not laundered into defects.

**Short, and self-contained anyway.** These two pull against each other, so the
rule is: **the log absorbs the volume, the reports absorb the argument.**
`FIELD-NOTES.md` can run long — nobody reads it end to end, it is there to be
searched and cited. The reports stay inside a budget:

| Document | Budget | Shape |
|---|---|---|
| `TUTORIAL-NONCODER.md` | ~1 page | verdict up top, timeline table, blockers |
| `TUTORIAL-CODER.md` | ~1 page | same shape, for side-by-side reading |
| `REPORT.md` | ~2–3 pages | ranked findings table, then the argument |

Enforced by structure, not willpower:

- **Every report opens with its verdict in ≤5 bullets** that stand alone if the
  reader stops there. Most will.
- **Findings are table rows, not essays** — location, expected vs. actual, and
  the proposed fix, each in a line or two. A finding needing more than that goes
  in the log and is *linked*, not inlined.
- **Evidence is compressed, not dropped.** The falsifiable parts still travel
  with the claim: a number, the three lines of error output that matter, the
  diff hunk — not the whole traceback or the whole file. A reader with no
  checkout can still check me; they just are not made to read a transcript.
- **Screenshots must earn their place** — only where a picture shows something
  prose cannot. Captured via the Playwright setup already in
  [tests/](tests/test_dashboard.py), stored under `docs/dims/images/`.
- **No restating the same finding in three sections.** Cross-reference instead.

If a report is over budget, the fix is to move detail into the log, never to
drop a finding.

---

## Files

| Path | Role |
|---|---|
| `docs/dims/FIELD-NOTES.md` | append-only running log (starts Phase 0) |
| `docs/dims/TUTORIAL-NONCODER.md` | walkthrough report, written before any source read |
| `docs/dims/TUTORIAL-CODER.md` | walkthrough report, coder path |
| `docs/dims/REPORT.md` | the final evaluation, drawing on both |
| `docs/dims/images/` | screenshots, so the reports stand alone |
| `dims_adapter/` | export gaitpdb → DIMS; reuses `gaitdata` queries |
| `gaitdata.py` | dual-task `_10` support: `record_filename`, schema, `Subject` |
| `figures.py` | `foot_map_figure` ported into DIMS, not rewritten |
| fork `GAIT-attempt/gait-media-panel` | feet-in-video-slot + demographics panel |

## Verification

- `python -m pytest tests/ -q` against a running `python app.py` still passes;
  the existing dashboard must not regress when `_10` recordings land.
- Adapter round-trips: ingest → DIMS → export → diff against `gait.db`.
- The replacement branch renders a real recording, scrubs correctly against the
  DIMS playhead, and shows demographics for the selected subject — screenshotted
  into the report.
- E1–E7 each have a recorded numeric result, **including the failures**.
- The dual-task contrast reproduces the known direction (dual-task raises
  stride-time variability) before I claim anything from it.
- **The DTW tab is checked against its own null first**: real pairings must not
  be distinguishable from surrogate pairings on this dataset, because nobody
  here walked together. If they are, my pipeline is finding structure that is not
  there — a leak, a normalisation artefact, or the speed confound — and the tab
  is wrong before it is interesting. Passing this is the precondition for
  trusting anything else the tab says.

## Open

Waiting only on permission to open the DIMS page. Everything in Phases 0 and 2
can start without it.
