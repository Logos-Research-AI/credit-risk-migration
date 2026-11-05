# Gate decisions

Durable record of human sign-offs. The rulebook (Step 1) supersedes this file
for translation rules once it exists.

## Feasibility gate — signed off 2026-11-05

- Verdict: **migrate now**, kit scaled to 4 units; build the judge first (prompt 00b).
- Posture: structure-preserving (one .sas script -> one Python module). Forced
  exception: the WORK-library model store (train.sas:151, predict.sas:208)
  becomes an on-disk artifact. Duplicated feature engineering is preserved
  during the port and deduplicated post-parity (prompt 06).
- Model plan:
  - Rulebook authorship / amendments: claude-opus-5-5
  - Skeptic reviewers, judge build (00b): claude-opus-5-5
  - Translation implementers, fixers: claude-sonnet-5-5
- Target stack: Python 3.13 (uv), **polars** for data (not pandas), numpy for
  model fitting (statsmodels where it helps). Rules for null semantics,
  `maintain_order=True`, and `best12.` CSV formatting go in the rulebook.
- Old-code oracle: **SAS OnDemand for Academics via saspy** (judge/ env;
  profiles in ~/.config/saspy/sascfg_personal.py; Java = Homebrew openjdk).
  Frozen goldens in output/ remain the reference if a re-run diverges.
  Basis for using ODA (non-commercial license): per the user, this is a
  non-commercial trial run of the migration kit, not production work.

## ODA connection — verified 2026-11-05

- saspy profile `oda_eu` (region euw1), user u64643823, home `/home/u64643823`.
- SAS version on ODA: 9.04.01M9P06052025. The frozen goldens in output/ were
  produced on another account (/home/u64352077), SAS version unknown.
- Judge build (prompt 00b) kicked off by the feasibility sign-off.

## Judge (prompt 00b) — built 2026-11-05, SIGNED OFF 2026-11-05

- Judge: `judge/` (see judge/README.md). Reference = fresh unmodified SAS run on ODA
  (`judge/reference/`, 31 files), byte-identical to the frozen `output/` goldens on the
  9 shared files. The frozen `output/` is NOT a usable fallback (lacks 22 judged files).
- Validation: 18/19 SAS mutations CAUGHT, 1 EQUIVALENT (train_slentry: outputs
  byte-identical), 0 MISSED; positive control (converged refit) PASSES; 75/75 self-test.
- Port contract: 4 stages judged on reference inputs + 4 edge scenarios + e2e smoke.
- Split: taken as an input (reference row_ids). SAS's own split drifted in 1 of 17 runs.

### Deviations from the kit (prompt 00b)
1. Steps 1–2 (categorize / rewrite existing tests): not applicable, the repo has 0 tests.
   Substituted: real-world scenarios + edge-case input scenarios, as 00b allows.
2. Reviewers A and B reviewed code that was edited while they worked (B noted it).
   Mitigation: review C re-reviewed the final state with no knowledge of A/B.
3. Review C's findings were fixed by the orchestrator and verified by the self-test
   and a full re-validation, but not re-reviewed by a fourth reviewer.
4. Orchestrator (this session) ran on claude-opus-5-5 (model plan: judge build = Opus).
   All three reviewers ran on Opus per the model plan. No deviation.

### Judge sign-off — 2026-11-05
- User approved the judge, its comparison policy (judge/README.md), and committing.
- Reference storage: plain git (user approved without choosing; plain git is the
  simpler default for a trial; largest file 23 MB). Switch to Git LFS if the repo grows.
- This sign-off kicks off Step 1 (prompts 01 dependency map, 02 gap inventory, rulebook).

## Step 1 — dependency map + rulebook draft signed off 2026-11-05
- Dependency map (4 files, 5 edges, 0 cycles) and manifest (4 units) accepted.
- RULEBOOK.md v1.0: user accepted all five proposed defaults (in-loop ruff+pyright;
  statsmodels/scikit-learn banned; SGPLOT not ported; listing-only PROCs not ported;
  predict.sas duplication kept until parity). DEV-004 sanctioned.
- Next: prompt 02 gap inventory; stops after the first 20 rows.
