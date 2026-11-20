"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): the four log columns of def:run at
FULL bits, on the seeds of suite fz10_run.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_run_logbits_gen.py
      -> diffeval/work/fz10c_run_logbits.{json,inputs.json}

fz10_run (fz10_run_gen.py) compares the columns log_monthly_income, log_num_credit_lines,
log_total_late_payments and age_income_interaction without their low 20 bits, folded over a block of 400
seeds (fz_run_gen.py docstring: "the last bit of log is outside the model, RULEBOOK 6"). This suite removes
that coarsening: same seeds (1_000_000..1_002_399), same frames, same split files (fz10_run_gen.split, the
4a757fb split modes), same real feature_engineering.run, and one integer PER SEED: the fold W of the tokens
of those four columns in every written file, row by row, each value (x.toBits + 2) (0 null, 1 NaN, -1 column
absent). A case that differs is a value of a log column that differs in some bit; it is then reduced and
classified separately (an RULEBOOK 6 last-bit-of-log case only when shown to be one).
Carrier: def:zz_carrier_fid_2 / zz_carrier_fid_2 (update-2026-11-20-carriers.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz10_run_gen  # noqa: E402,F401  (patches fz_run_gen: LETS and split for 4a757fb)
import fz_run_gen as g  # noqa: E402
import compare as cmp  # noqa: E402
import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")
from suite import Suite  # noqa: E402

OLD_LG = "((x.toBits >>> 20).toNat : Int) + 2"
NEW_LG = "(x.toBits.toNat : Int) + 2"
assert g.LETS.count(OLD_LG) == 1
LETS = g.LETS.replace(OLD_LG, NEW_LG)


def logtokens_full(df) -> list[int]:
    out = []
    for r in df.iter_rows(named=True):
        for c in g.LOGS:
            if c not in r:
                out.append(-1)
            else:
                x = r[c]
                out.append(0 if x is None else 1 if x != x else cmp.fbits(x) + 2)
    return out


def main() -> None:
    calls, per, base0 = 6, 400, 1_000_000
    s = Suite("fz10c_run_logbits", generator="port-to-lean/diffeval/units/fz10c_run_logbits_gen.py")
    n_cases = n_completed = n_values = 0
    for c in range(calls):
        base = base0 + c * per
        bad, cases = [], []
        for seed in range(base, base + per):
            df, sp = g.mk(seed), g.split(seed)
            r = g.pyrun(g.csv_text(df), "row_id\n" + "".join(f"{int(i)}\n" for i in sp), df)
            if not r["held"]:
                bad.append(seed)
                continue
            ok = g.precond(df, r["stop"], sp) if r["raised"] is None else g.check_precond(df) and len(sp) > 0
            if r["raised"] is not None:
                bad.append(seed)
                continue
            toks = [] if r["stop"] else [t for _, x in r["files"] for t in logtokens_full(x)]
            n_values += sum(1 for t in toks if t > 1)
            n_completed += 0 if r["stop"] else 1
            cases.append((f"seed {seed}: the four log columns at full bits ({'none' if r['stop'] else 'completed'})",
                          g.UNIT, g.wfold(toks), {"fz": "kept" if ok else "rejected"}))
        off = [b - base for b in bad]
        lets = (g.TAB + LETS + f"let BAD : List Nat := {off}; "
                f"let R := (((List.range {per}).filter (fun (i : Nat) => !(BAD.contains i))).map (fun (i : Nat) => (i, one ({base} + i)))); ")
        body = "R.map (fun (p : Nat × Int × List Int) => W p.2.2)"
        n_cases += len(cases)
        s.ints(g.MINI + lets, body, cases, gen=True, use_kit=False)
    s.write()
    print({"cases": n_cases, "completed": n_completed, "log values": n_values})
    print([len(i["text"]) for i in s.inputs])


if __name__ == "__main__":
    main()
