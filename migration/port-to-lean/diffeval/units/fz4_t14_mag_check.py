"""Check of the magnitude clauses added to def:train_run_14_final_and_summary_precond (2026-11-17), after the
fuzz finding of fz4_t14_probe.py: write_sas_csv raises decimal.InvalidOperation when a Float64 value that it
formats with 'percent8.2' or '8.4' is finite with magnitude >= 9.999999999999996e75 (sas_compat._fixed:
quantize under Context(prec=80)).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz4_t14_mag_check.py

The precondition rendered in Python = rv_td_pre14.pre (G30 clauses, as before) and the two new clauses:
  (a) in each scored set, a Float64 column interest_rate holds no finite value outside (-T, T);
  (b) when roc_valid_created, each of the ten formatted names that is a Float64 column of
      merge_one_to_one(the four frames as the unit builds them) holds no finite value outside (-T, T);
  T = 9.999999999999996e75. (A non-Float64 column needs no clause: Int64 / Boolean values are below 2**63,
  Null holds no value, Date takes the date9 path.)
Asserted: rendering == "the real step 14 (train.py:742-841, td_gen.run_slice) returns", on
  (1) the inputs of fz4_t14_probe.py, (2) a boundary table on every formatted column (both signs, both values
  of roc_valid_created, NaN, +-inf, 5e-324, 1e22, 1e300, the largest double), (3) the 3,000 seeds of suite
  fz4_t14 (300000..302999), whose inputs are unchanged.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz4_t14_gen as g  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

rp, td, fz = g.rp, g.td, g.fz
T = 9.999999999999996e75
TEN = rp.TEN


def bad(s: pl.Series) -> bool:
    return s.dtype == pl.Float64 and any(v is not None and math.isfinite(v) and not (-T < v < T) for v in s.to_list())


def mag(e: dict) -> bool:
    for f in (e["risk_scores_train"], e["risk_scores_validation"]):
        if "interest_rate" in f.columns and bad(f.get_column("interest_rate")):
            return False
    if e["roc_valid_created"]:
        m = sc.merge_one_to_one(
            e["roc_train"].filter(pl.col("ROCModel") == "Training Set").select(Train_AUC=pl.col("Area")),
            e["roc_valid"].filter(pl.col("ROCModel") == "Validation Set").select(Valid_AUC=pl.col("Area")),
            e["training_metrics"], e["validation_metrics"])
        for k in TEN:
            if k in m.columns and bad(m.get_column(k)):
                return False
    return True


def pre_new(e: dict) -> bool:
    return rp.pre(e) and mag(e)


def returns(e: dict) -> tuple[bool, str]:
    try:
        td.run_slice("s14", e)
        return True, ""
    except Exception as ex:  # noqa: BLE001
        return False, type(ex).__name__


def main():
    base = g.env14(300002)
    rows = []

    def case(name, **ch):
        e = dict(base)
        e.update(ch)
        rows.append((name, rp.pre(e), pre_new(e), *returns(e)))

    tm, vm, rs, rt, rv = (base[k] for k in ("training_metrics", "validation_metrics", "risk_scores_train", "roc_train",
                                             "roc_valid"))
    case("as generated (seed 300002)")
    # (1) the probe's inputs
    for big in (9.999999999999994e75, 9.999999999999996e75, 1e76, -1e76, 1e300):
        n = tm.height
        case(f"probe: train_precision = {big}", training_metrics=tm.with_columns(
            train_precision=pl.Series([big] * n, dtype=pl.Float64)) if n else tm)
        case(f"probe: interest_rate = {big} (train set)", risk_scores_train=rs.with_columns(
            interest_rate=pl.Series([big] * rs.height, dtype=pl.Float64)) if rs.height else rs)
        case(f"probe: Area (roc_train) = {big}", roc_train=rt.with_columns(
            Area=pl.Series([big] * rt.height, dtype=pl.Float64)))
    r1 = pl.DataFrame({"interest_rate": pl.Series([1e76], dtype=pl.Float64)})
    case("probe: risk_scores_train = [interest_rate 1e76]", risk_scores_train=r1)
    case("probe: risk_scores_validation = [interest_rate 1e76]", risk_scores_validation=r1)
    case("probe: risk_scores_train = [interest_rate 9.999999999999994e75]",
         risk_scores_train=r1.with_columns(interest_rate=pl.lit(9.999999999999994e75)))
    case("probe: risk_scores_train = [interest_rate 1e76, age 1e300]", risk_scores_train=r1.with_columns(age=pl.lit(1e300)))
    # (2) boundary table: one row everywhere, each formatted column in turn
    one_tm = pl.DataFrame({c: [0.5] for c in ("train_precision", "train_recall", "train_f1_score", "train_accuracy")})
    one_vm = pl.DataFrame({c: [0.5] for c in ("valid_precision", "valid_recall", "valid_f1_score", "valid_accuracy")})
    one_rt = pl.DataFrame({"ROCModel": ["Training Set"], "Area": [0.5]})
    one_rv = pl.DataFrame({"ROCModel": ["Validation Set"], "Area": [0.5]})
    one_rs = pl.DataFrame({"interest_rate": [0.09], "age": [40.0]})
    small = dict(base, training_metrics=one_tm, validation_metrics=one_vm, roc_train=one_rt, roc_valid=one_rv,
                 risk_scores_train=one_rs, risk_scores_validation=one_rs)
    vals = [9.999999999999994e75, 9.999999999999996e75, 1e76, 1e300, 1.7976931348623157e308, math.inf, math.nan,
            5e-324, 1e22, 0.0, -0.0]
    targets = [("risk_scores_train", "interest_rate"), ("risk_scores_validation", "interest_rate"),
               ("roc_train", "Area"), ("roc_valid", "Area")] + \
              [("training_metrics", c) for c in one_tm.columns] + [("validation_metrics", c) for c in one_vm.columns]
    for created in (True, False):
        for frame, col in targets:
            for v in vals:
                for sgn in (1.0, -1.0):
                    x = sgn * v
                    e = dict(small, roc_valid_created=created)
                    e[frame] = e[frame].with_columns(pl.Series(col, [x], dtype=pl.Float64))
                    rows.append((f"table: {frame}.{col} = {x!r}, created {created}", rp.pre(e), pre_new(e), *returns(e)))
    # a value at the boundary in a row the filter drops (label x) stays out of the clause
    e = dict(small, roc_train=pl.DataFrame({"ROCModel": ["Training Set", "x"], "Area": [0.5, 1e76]}))
    rows.append(("table: roc_train Area 1e76 in a row labelled x", rp.pre(e), pre_new(e), *returns(e)))
    # an Int64 interest_rate at the largest Int64 (no raise, no clause)
    e = dict(small, risk_scores_train=pl.DataFrame({"interest_rate": pl.Series([2**63 - 1], dtype=pl.Int64)}))
    rows.append(("table: interest_rate Int64 2**63-1", rp.pre(e), pre_new(e), *returns(e)))

    hand_bad = 0
    old_admits_raise = 0
    for name, p_old, p_new, r, msg in rows:
        ok = p_new == r
        hand_bad += not ok
        old_admits_raise += p_old and not r
        print(f"{'ok' if ok else 'MISMATCH':8s} old={p_old!s:5s} new={p_new!s:5s} returns={r!s:5s} {msg:18s} {name}")
    print(f"hand-made inputs: {len(rows)}; new precondition == Python returns on {len(rows) - hand_bad}; "
          f"admitted by the old precondition and raising: {old_admits_raise}")

    # (3) the suite's seeds
    # the suite's rejected class (a column `shared` Float64 in one metrics frame and text in the other) is an
    # existing narrowing: excluded, Python returns. It is counted apart.
    n = same = changed = narrowing = admits_raise = 0
    for s in range(300000, 303000):
        e = g.env14(s)
        p_old, p_new, (r, _) = rp.pre(e), pre_new(e), returns(e)
        n += 1
        same += p_new == r
        changed += p_old != p_new
        narrowing += (not p_new) and r
        admits_raise += p_new and not r
    print(f"suite fz4_t14 seeds 300000..302999: {n}; new precondition == Python returns on {same}; "
          f"excluded and Python returns (the suite's known narrowing): {narrowing}; admitted and Python raises: "
          f"{admits_raise}; seeds whose class the new clauses change: {changed}")
    assert hand_bad == 0 and admits_raise == 0 and changed == 0 and narrowing == n - same


if __name__ == "__main__":
    main()
