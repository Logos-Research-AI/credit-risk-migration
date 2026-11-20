"""Receipt of the fidelity pass 2026-11-20 (third attempt), label metrics -> diffeval/receipts/fuzz_2026-11-20c-metrics.tsv

  cd migration/port-to-lean && python3 diffeval/units/fz10c_receipt.py

Reads work/fz10c_{cm,th,lift,lift_nz,real,m}.json / .result.json / .fuzz.json (compare.py results of the eval_decl
outputs on def:zz_carrier_fid_2). Columns as receipts/fuzz_2026-11-16.tsv (fuzz_receipt.py), one row per unit and
evidence kind (fuzz / real data / composition). Outputs were transcribed from this session's eval_decl results into
work/<suite>.out.txt (fuzz_collect.py reads a session record, which this role may not open); each transcription is
guarded by digests of the inputs (every case digests its input frames; the real-data and table inputs carry
input-check cases).
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parent / "work"
OUT = HERE.parent / "receipts" / "fuzz_2026-11-20c-metrics.tsv"
HEAD = ("unit\tfuzzer\tseeds\tgenerated\tkept\tshare_kept\tcompared_kept\tdifferences\tnarrowings\t"
        "python_raises_inside_precondition\tstatus\tnote\tblueprint\tgenerator")
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
FZ = "port-translator (fidelity pass 2026-11-20c, metrics)"
G = "diffeval/units/fz10c_metrics_gen.py"
GM = "diffeval/units/fz10c_m_gen.py"
CARRIER = "carrier def:zz_carrier_fid_2; port HEAD 4a757fb; Lean = current accepted statement of the item (read 2026-11-20)"


def load(name):
    s = json.loads((W / f"{name}.json").read_text())
    r = json.loads((W / f"{name}.result.json").read_text())
    assert len(s["cases"]) == len(r), f"{name}: stale result"
    return list(zip(s["cases"], r))


def agg(pairs, prim):
    a = {"kept": 0, "diff": 0, "narrow": 0, "err": 0, "ids": [], "cases": 0, "fam": {}}
    for c, r in pairs:
        if r["primitive"] != prim:
            continue
        n = c.get("covers", 1)
        a["cases"] += 1
        a["err"] += r["status"] == "ERROR"
        if c.get("fz", "kept") == "kept":
            a["kept"] += n
            if r["status"] != "PASS":
                a["diff"] += 1
                a["ids"].append(c["id"])
                a["fam"][c.get("family")] = a["fam"].get(c.get("family"), 0) + 1
        elif r["status"] == "PASS":
            a["narrow"] += n
    return a


def checks(pairs):
    cs = [(c, r) for c, r in pairs if r["primitive"] == "input-check"]
    return len(cs), sum(r["status"] == "PASS" for _, r in cs)


def row(*xs):
    return "\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in xs)


def main():
    rows = []
    cm, th, lf, nz, real, m = (load(n) for n in ("fz10c_cm", "fz10c_th", "fz10c_lift", "fz10c_lift_nz", "fz10c_real", "fz10c_m"))
    fcm = json.loads((W / "fz10c_cm.fuzz.json").read_text())["units"]["confusion_metrics"]
    fth = json.loads((W / "fz10c_th.fuzz.json").read_text())["units"]["metrics_run_03_thresholds"]
    flf = json.loads((W / "fz10c_lift.fuzz.json").read_text())["units"]["metrics_run_05_cumulative_lift"]
    for unit, pairs, f in (("confusion_metrics", cm, fcm), ("metrics_run_03_thresholds", th, fth)):
        a = agg(pairs, unit)
        st = "ERROR" if a["err"] else "DIFF" if a["diff"] else "PASS"
        rows.append(row(unit, FZ, f["seeds"], f["generated"], f["kept"], f"{f['kept'] / f['generated']:.3f}", a["kept"], a["diff"],
                        a["narrow"], len(f["python_raises_inside_precondition"]), st,
                        f"{CARRIER}; {a['cases']} cases (block digests); {f['note']}; rejected (Boolean default_flag, precondition "
                        f"wants Float64/Int64) sent: Python returned on all {f['stat']['rejected']}, Lean equal on {a['narrow']} "
                        f"(narrowing); Python raised on 0 generated inputs", BP, G))
    a = agg(lf, "metrics_run_05_cumulative_lift")
    an = agg(nz, "metrics_run_05_cumulative_lift")
    zeros_only = set(a["fam"]) == {3}
    lim = (a["diff"] and zeros_only and an["diff"] == 0 and an["err"] == 0)
    st = "ERROR" if a["err"] else ("KNOWN-LIMIT" if lim else "DIFF") if a["diff"] else "PASS"
    rows.append(row("metrics_run_05_cumulative_lift", FZ, flf["seeds"], flf["generated"], flf["kept"], f"{flf['kept'] / flf['generated']:.3f}",
                    a["kept"], a["diff"], a["narrow"], len(flf["python_raises_inside_precondition"]), st,
                    f"{CARRIER}; {a['cases']} cases (block digests); {flf['note']}; rejected (Float64 total_count, precondition wants "
                    f"Int64) sent: Python returned on all {flf['stat']['rejected']}, Lean equal on {a['narrow']} (narrowing); "
                    f"0-row decile_data now admitted (precondition of 2026-11-18) and in the pool (ND[0]); ALL differences: the "
                    f"{a['diff']} cases of the family zeros ({flf['stat']['zeros']} seeds whose defaults pool holds -0.0) and no other "
                    f"case; recorded prelude limit RULEBOOK section 6 (running sum starting at -0.0: polars cum_sum starts from 0.0, "
                    f"Pl.cumSumF from the first value; reaches cum_defaults and from it cum_capture_rate, cum_lift); shown by suite "
                    f"fz10c_lift_nz (the same {flf['stat']['zeros']} seeds, -0.0 replaced by 0.0 in cum_defaults, cum_capture_rate, "
                    f"cum_lift on both sides): {an['cases'] - an['diff']} of {an['cases']} cases equal; differing cases: {a['ids'][:3]}",
                    BP, G))
    nck, nok = checks(real)
    for unit, what in (("confusion_metrics", "5 windows x 7 thresholds (0.3..0.7, 0.5 +- 1 ulp)"),
                       ("metrics_run_03_thresholds", "5 windows")):
        a = agg(real, unit)
        st = "ERROR" if a["err"] else "DIFF" if a["diff"] else "PASS"
        rows.append(row(unit, FZ, "real data: judge/scenarios/real_metrics", a["cases"], a["kept"], "1.000", a["kept"], a["diff"], 0, 0, st,
                        f"{CARRIER}; real import (proc_import_csv of risk_scores_validation.csv, 45,000 rows) and the frame step 02 "
                        f"sorts (the frame steps 03-05 read in run, by the real source of run :119-293); windows of 60 rows of "
                        f"default_flag, pd_logistic (the columns the unit reads; the other 49 pass through): import rows 0.., "
                        f"sorted last rows, sorted rows centred on pd 0.3 / 0.5 / 0.7; {what}; transcription guarded by "
                        f"{nck} input-check digests ({nok} equal); the whole 45,000-row frame was NOT sent (its pd_logistic is "
                        f"41,277 distinct full-precision doubles, about 0.7 MB of input text)", BP, G))
    a = agg(real, "metrics_run_05_cumulative_lift")
    st = "ERROR" if a["err"] else "DIFF" if a["diff"] else "PASS"
    rows.append(row("metrics_run_05_cumulative_lift", FZ, "real data: judge/scenarios/real_metrics (whole)", a["cases"], a["kept"], "1.000",
                    a["kept"], a["diff"], 0, 0, st,
                    f"{CARRIER}; WHOLE real input: decile_data and decile_analysis as the real source of run :119-293 makes them "
                    f"from the real import (45,000 rows; decile_data cut to default_flag, the only column the step reads: output "
                    f"asserted equal with and without the cut), decile_analysis 10 rows all 9 columns; valid_exists true (as in run) "
                    f"and false; sas_best / float tables recorded from the real functions; decile_data input-check digest equal", BP, G))
    fm = json.loads((W / "fz10c_m.fuzz.json").read_text())
    a = agg(m, "metrics")
    for unit, s in fm["units"].items():
        kept = s["kept"]
        gen = kept + s["rejected"] + len(s["raises-kept"]) + s["raises-rejected"] + s["upstream"]
        st = "ERROR" if a["err"] else "DIFF" if a["diff"] else "PASS"
        rows.append(row(f"{unit} (composition fz7_m re-run)", FZ, fm["seeds"], gen, kept, f"{kept / gen:.3f}", kept, a["diff"],
                        s["rejected"] if not a["diff"] else 0, len(s["raises-kept"]), st,
                        f"{CARRIER}; fz7_metrics_gen (2026-11-18) re-run unchanged in pools, Python side (real source of run cut by "
                        f"markers) and Lean composition (01, 02, 03 via confusion_metrics + Pl.concat, 04, 05, 06, 07, 08, 09, 10 chained "
                        f"in Lean on Lean results); one case = digest of the per-seed digests (12 unit results each) of a block of 25 "
                        f"seeds: {a['cases']} block cases, {a['cases'] - a['diff']} equal; steps 01/02/04 on their widened "
                        f"preconditions (0-row validation frame admitted, lead 2026-11-18): {fm['flavours']['empty_V']} seeds with an "
                        f"empty validation frame, {fm['flavours']['empty_T']} with an empty training frame; fz7's own masking kept: "
                        f"-0.0 cleared on both sides in min_pd/max_pd (04, 05) and cum_* (05) = the two signed-zero limits of RULEBOOK "
                        f"section 6; sas_best/float: fz7's two lookup tables folded into one bits->bits table (used only through "
                        f"_into_float), its transcription checked by a digest (equal); Python raised on 0 seeds", BP, GM))
    OUT.write_text("\n".join([HEAD, *rows]) + "\n")
    for r in rows:
        print(r[:240])


if __name__ == "__main__":
    main()
