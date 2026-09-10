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

