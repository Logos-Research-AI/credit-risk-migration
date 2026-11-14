"""Bundle B9, reviewer 2: the differential test of b9_gen.py (train.run = def:run_py_py_py and its
fifteen steps) on NEW samples. All the machinery is b9_gen's (imported, unchanged); only the data
differ: rows drawn with a seeded generator from the real feature files, with a chosen share of
events, optional planted nulls, in random row order.

  uv run python migration/diffeval/units/b9_r2_gen.py explore <sample> <seed> [<seed> ...]
      -> one line per seed: does the real train.run finish, stepwise path, validation events,
         null pd counts (nothing is written to work/)
  uv run python migration/diffeval/units/b9_r2_gen.py <sample>
      -> work/b9r2_<sample>.json + .inputs.json (ONE eval_decl input)
  uv run python migration/diffeval/units/b9_r2_gen.py <sample> --mask <integer>
      -> the labels of the compared values whose bit is set in the localisation mask
  uv run python migration/diffeval/units/b9_r2_gen.py <sample> --probes
      -> the exp / log probe arguments with Python's results (to name a probe that differs)

The full feature files are produced by the real feature_engineering.run on data/cs-training.csv
with inputs/split_ids.csv into FE_DIR (a temp dir outside the workspace, built once).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))

import b9_gen as b9  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

ROOT = HERE.parents[2]
TMP = Path(os.environ.get("B9R2_TMP", "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration-formal-python/"
                                      "aa9ba63a-dfbb-4dbd-bc0a-805359ea00aa/scratchpad/b9r2"))
FE_DIR = TMP / "fe_out"

# sample -> seed, rows, share of events (None: as drawn), planted nulls (row position, column)
SAMPLES: dict[str, dict] = {}


def full_frames() -> tuple[pl.DataFrame, pl.DataFrame]:
    if not (FE_DIR / "model_features_validation.csv").exists():
        import contextlib
        import io

        with contextlib.redirect_stdout(io.StringIO()):
            fe.run(ROOT / "data", FE_DIR, split_ids=ROOT / "inputs" / "split_ids.csv")
    return (sc.proc_import_csv(FE_DIR / "model_features_train.csv", guessingrows=None),
            sc.proc_import_csv(FE_DIR / "model_features_validation.csv", guessingrows=None))


def draw(df: pl.DataFrame, n: int, events: int | None, rng: np.random.Generator) -> pl.DataFrame:
    """n rows in random order; `events` of them with default_flag = 1 when given."""
    if events is None:
        idx = rng.choice(df.height, size=n, replace=False)
    else:
        y = df.get_column("default_flag").to_numpy()
        ev, ne = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
        idx = np.concatenate([rng.choice(ev, size=events, replace=False), rng.choice(ne, size=n - events, replace=False)])
        rng.shuffle(idx)
    return df[[int(i) for i in idx]]


def write_sample(cfg: dict, seed: int, ind: Path) -> None:
    tr, va = full_frames()
    rng = np.random.default_rng(seed)
    ind.mkdir(parents=True, exist_ok=True)
    for name, df, n, ev, nulls in [("model_features_train.csv", tr, cfg["n_train"], cfg.get("ev_train"), cfg.get("nulls_train", [])),
                                   ("model_features_validation.csv", va, cfg["n_valid"], cfg.get("ev_valid"), cfg.get("nulls_valid", []))]:
        d = draw(df, n, ev, rng)
        assert d.height == n and all(t == pl.Float64 for t in d.dtypes)
        for row, col in nulls:
            d = d.with_columns(pl.when(pl.int_range(pl.len()) == row).then(None).otherwise(pl.col(col)).alias(col))
        d.write_csv(ind / name)


def describe(rec: dict) -> str:
    L, sw = rec["locals"], rec["stepwise"]
    rsv, rst = L["risk_scores_validation"], L["risk_scores_train"]
    yv = rsv.get_column("default_flag")
    return (f"fit rows {L['n_obs']}; path {[(s.step, s.entered, s.removed) for s in sw.steps]}; final {sw.final.names[1:]}; "
            f"valid events {int((yv == 1).sum())} / non-events {int((yv == 0).sum())} / null {yv.null_count()}; "
            f"null pd train {rst.get_column('pd_logistic').null_count()} valid {rsv.get_column('pd_logistic').null_count()}; "
            f"grades train {sorted(set(rst.get_column('risk_grade').to_list()))} valid {sorted(set(rsv.get_column('risk_grade').to_list()))}; "
            f"cm train {L['confusion_matrix_train'].rows()} cm valid {L['confusion_matrix'].rows()}; "
            f"valid metrics {L['validation_metrics'].rows()}; AUC {L['roc_train'].get_column('Area').to_list()} {L['roc_valid'].get_column('Area').to_list()}")


def explore(sample: str, seeds: list[int]) -> None:
    cfg = SAMPLES[sample]
    for seed in seeds:
        ind = TMP / "explore" / f"{sample}_{seed}"
        write_sample(cfg, seed, ind)
        try:
            rec = b9.real_run(ind, encoded=False)
            print(f"seed {seed}: OK  {describe(rec)}")
        except Exception as e:  # noqa: BLE001
            print(f"seed {seed}: {type(e).__name__}: {str(e)[:200]}")


def build(sample: str, mask: int | None = None, probes: bool = False):
    cfg = SAMPLES[sample]
    ind = TMP / "in" / sample
    if not (ind / "model_features_validation.csv").exists():
        write_sample(cfg, cfg["seed"], ind)
    b9.sample_inputs = lambda: ind
    b9.NULLS_TRAIN, b9.NULLS_VALID = cfg.get("nulls_train", []), cfg.get("nulls_valid", [])
    mft = sc.proc_import_csv(ind / "model_features_train.csv", guessingrows=None)
    mfv = sc.proc_import_csv(ind / "model_features_validation.csv", guessingrows=None)
    guard = b9.fd(mft) + b9.fd(mfv)  # the input tables as Lean decoded them (guards the typed input)

    class GuardedSuite(Suite):
        def ints(self, lets, body, cases, **kw):
            head, exp = "(let P : List (List Int) := [", 'let EXP : Array Int := ("'
            assert body.startswith(head) and body.count(exp) == 1
            body = head + "FD fT, FD fV, " + body[len(head):]
            body = body.replace(exp, exp + "".join(chr(97 + e % b9.SHORT) for e in guard))
            cases = ([("input: model_features_train as decoded by Lean", "run_py_py_py", b9.w(b9.fd(mft)), {"covers": mft.width + 1}),
                      ("input: model_features_validation as decoded by Lean", "run_py_py_py", b9.w(b9.fd(mfv)), {"covers": mfv.width + 1})]
                     + list(cases[:-1]) + [(cases[-1][0], cases[-1][1], cases[-1][2] + len(guard))])
            super().ints(lets, body, cases, **kw)

        def write(self):
            units = dict.fromkeys(c["primitive"] for c in self.cases)
            tag = f"reviewer 2 samples (sample {sample}, seed {cfg['seed']}, {mft.height}/{mfv.height} rows)"
            self.notes = {u: tag + ("; " + self.notes[u] if u in self.notes else "") for u in units}
            return super().write()

    b9.Suite = lambda _name: GuardedSuite(f"b9r2_{sample}")
    if mask is not None:  # the first len(guard) bits are the input columns
        names = b9.labels_fd("input fT", mft) + b9.labels_fd("input fV", mfv)
        for k, lab in enumerate(names):
            if (mask >> k) & 1:
                print("input", k, lab)
        mask >>= len(guard)
    if probes:
        rec = b9.real_run(ind, encoded=True)
        for lab, fn, x, r in b9.routine_tables(rec)["explog"]:
            print(f"{fn}\t{b9.fb(x)}\t{b9.fb(r)}\t{x!r}\t{r!r}\t{lab}")
        return
    rec = b9.build(mask=mask)
    if rec is not None:
        print(f"{sample} (seed {cfg['seed']}): {describe(rec)}")


SAMPLES.update({
    # A: no nulls, events as drawn in validation but at least some (seed chosen so)
    "a": {"seed": 1, "n_train": 60, "n_valid": 30, "ev_train": 20, "ev_valid": 9},
    # B: larger, events oversampled
    "b": {"seed": 11, "n_train": 90, "n_valid": 40, "ev_train": 30, "ev_valid": 12},
    # C: planted nulls in candidates that the stepwise fit often selects (train and validation), in
    # default_flag and in a non-candidate column (age_group)
    "c": {"seed": 7, "n_train": 60, "n_valid": 30, "ev_train": 18, "ev_valid": 8,
          "nulls_train": [(4, "has_delinquency"), (11, "financial_health"), (19, "default_flag"), (27, "credit_util_category"),
                          (38, "total_late_payments"), (52, "age_group"), (58, "monthly_income")],
          "nulls_valid": [(2, "has_delinquency"), (7, "financial_health"), (12, "default_flag"), (16, "credit_util_category"),
                          (21, "total_late_payments"), (25, "age_group"), (28, "monthly_income")]},
    # D: the stepwise path enters one effect and removes it: the final model is the intercept alone
    "d": {"seed": 12, "n_train": 60, "n_valid": 30, "ev_train": 18, "ev_valid": 8,
          "nulls_train": [(4, "total_late_payments"), (11, "age"), (19, "default_flag"), (27, "credit_utilization_capped"),
                          (38, "num_late_90_plus"), (52, "age_group"), (58, "monthly_income")],
          "nulls_valid": [(2, "total_late_payments"), (7, "age"), (12, "default_flag"), (16, "credit_utilization_capped"),
                          (21, "num_late_90_plus"), (25, "age_group"), (28, "has_delinquency")]},
})

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "explore":
        explore(a[1], [int(s) for s in a[2:]])
    elif len(a) > 2 and a[1] == "--mask":
        build(a[0], mask=int(a[2]))
    elif len(a) > 1 and a[1] == "--probes":
        build(a[0], probes=True)
    else:
        build(a[0])
