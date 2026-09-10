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

