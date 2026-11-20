"""Fidelity pass 2026-11-20c, label train-d: def:train_run_13_roc (train.py:803-830) and
def:train_run_14_final_and_summary (train.py:836-941) on blueprint 5365851c, carrier def:zz_carrier_fid_2.
(def:train_run_15_printed_roc: fz6_td15_gen.py run with the suite name fz10_td15, then this script's `retarget`.)

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_traind_gen.py [13|14|retarget NAME]

Step 13 (new suite fz10_td13; the unit now returns roc_train, roc_valid, roc_train_created, roc_valid_created):
  frames of fz_td_gen.frame13 (columns of fz_t1_gen: outcome Float64 from {0, 1, null, NaN, -0.0, 2, 0.5} / Int64 /
  Boolean / Null dtype; probability on a grid with offsets of _SE_EPS / _TIE_EPS size, edges, random, Int64, Boolean,
  Null dtype; rows 0..40; alone or with a third Int64 column, three orders); training frame from s, validation frame
  from s + 500000. NEW: in 1 of 10 seeds the validation frame has no default_flag (the x27 path, no_flag), and in half
  of those it has no row (polars .clear(), Lean takeRows []). Expected: the CURRENT lines 803-830 executed verbatim
  (td_gen.run_slice), math.fsum = CPython's algorithm as the Lean let FS (fz_t1_gen, mirror checked).
  Precondition in Python (def:train_run_13_roc_precond): pd_logistic in both frames, default_flag in the training
  frame, roc_association_precond on (train flag, train pd) and (valid flag or Float64 [], valid pd), both outcomes
  Float64 or Int64 (comparable). Unequal column lengths (not a pl.DataFrame) are dropped. Every other seed is run in
  Python: kept (inside), rejected-and-Python-returns (compared as its own class), Python raises outside (dropped,
  counted). One value per seed: digest of (roc_train tokens, roc_valid tokens, the two Booleans).
Step 14: fz5_t14_gen (seeds 700000..702999), suite name fz10_td14, expected recomputed now on HEAD.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import fz5_t14_gen as f5  # noqa: E402  (loads td_gen with SLICES s14 = 836-941, and fz_td_gen)

td, fz = f5.td, f5.fz
td.SLICES["s13"] = (803, 830, "roc_valid_created = bool((roc_valid_used == 1).any()) and bool((roc_valid_used != 1).any())")
td.CODE["s13"] = td.slice_code("s13")

import suite as suite_mod  # noqa: E402
import b4_gen as b4  # noqa: E402
import fz_t1_gen as t1  # noqa: E402
from suite import Suite  # noqa: E402

CAR = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")
suite_mod.CARRIERS["identity"] = CAR
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
WORK = HERE.parent / "work"
U13 = "train_run_13_roc"
w, h = b4.w, t1.h
D, CH, S13, N13, PER = 500000, 25, 800000, 3625, 29


def equal_len(s):
    return h(s, 1003) % 25 != 0


def valid13(s):
    """the validation frame of seed s (s already shifted by D)"""
    f = fz.frame13(s)
    if h(s, 1020) % 10 == 0:
        f = f.drop("default_flag")
        if h(s, 1021) % 2 == 0:
            f = f.clear()
    return f


def comparable(dt):
    return dt in (pl.Float64, pl.Int64)


def pre13(a, b):
    for f in (a, b):
        if len(set(f.columns)) != f.width or "pd_logistic" not in f.columns:
            return False
    if "default_flag" not in a.columns:
        return False
    vf = b["default_flag"] if "default_flag" in b.columns else pl.Series("default_flag", [], pl.Float64)
    return (t1.pre_roc(a["default_flag"], a["pd_logistic"]) and t1.pre_roc(vf, b["pd_logistic"])
            and comparable(a.schema["default_flag"]) and comparable(vf.dtype))


def val13(ns):
    return w(b4.frame_tok(ns["roc_train"]) + b4.frame_tok(ns["roc_valid"])
             + [int(ns["roc_train_created"]), int(ns["roc_valid_created"])])


FRV = ("let FRV := fun (s : Nat) => (if h s 1020 % 10 == 0 then "
       "(let g : Pl.Frame Float := List.filter (fun (p : String × Pl.Col Float) => p.1 != \"default_flag\") (FR s); "
       "if h s 1021 % 2 == 0 then g.takeRows [] else g) else FR s : Pl.Frame Float); ")


def suite13():
    st = Suite("fz10_td13")
    kept, rej, cnt = {}, {}, {"dropped_len": 0, "raises_out": 0, "noflag": 0, "noflag_norow": 0,
                              "train_created": 0, "valid_created": 0}
    raises_in, raises_out_kinds = [], {}
    for s in range(S13, S13 + N13):
        if not (equal_len(s) and equal_len(s + D)):
            cnt["dropped_len"] += 1
            continue
        a, b = fz.frame13(s), valid13(s + D)
        ok = pre13(a, b)
        try:
            ns, _, _ = td.run_slice("s13", {"risk_scores_train": a, "risk_scores_validation": b})
        except Exception as ex:  # noqa: BLE001
            if ok:
                raises_in.append((s, type(ex).__name__, str(ex)[:80]))
            else:
                cnt["raises_out"] += 1
                k = type(ex).__name__
                raises_out_kinds[k] = raises_out_kinds.get(k, 0) + 1
            continue
        (kept if ok else rej)[s] = val13(ns)
        if ok:
            cnt["noflag"] += "default_flag" not in b.columns
            cnt["noflag_norow"] += "default_flag" not in b.columns and b.height == 0
            cnt["train_created"] += bool(ns["roc_train_created"])
            cnt["valid_created"] += bool(ns["roc_valid_created"])
    lets = (t1.BASE + t1.COLS + b4.OF + b4.TS + b4.TCOL + fz.FR + FRV + t1.FS_LET
            + "let tf := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
            + "let bi := fun (b : Bool) => (if b then 1 else 0 : Int); "
            + f"let R := fun (s : Nat) => let r := train_run_13_roc (α := Float) FS (FR s) (FRV (s + {D})); "
              "W (tf r.1 ++ tf r.2.1 ++ [bi r.2.2.1, bi r.2.2.2]); ")
    # kept = (cheap class filter K, mirrored in Lean) minus an explicit list X (roc_association_precond false
    # or Python raising); asserted below. Rejected-and-Python-returns seeds are compared as their own list.
    lets += (f"let K := fun (s : Nat) => h s 1003 % 25 != 0 && h (s + {D}) 1003 % 25 != 0 && h s 1001 % 10 < 8 && "
             f"(if h (s + {D}) 1020 % 10 == 0 then (h (s + {D}) 1021 % 2 == 0 || nn (s + {D}) == 0) else h (s + {D}) 1001 % 10 < 8); ")

    def K(s):
        sd = s + D
        return (equal_len(s) and equal_len(sd) and h(s, 1001) % 10 < 8
                and ((h(sd, 1021) % 2 == 0 or t1.nn(sd) == 0) if h(sd, 1020) % 10 == 0 else h(sd, 1001) % 10 < 8))

    X = [s for s in range(S13, S13 + N13) if K(s) and s not in kept]
    assert all(K(s) for s in kept), "kept outside the class filter"
    nch = N13 // CH
    cases = []
    for i in range(nch):
        lo, hi = S13 + CH * i, S13 + CH * (i + 1)
        c = [s for s in sorted(kept) if lo <= s < hi]
        cases.append((f"13 seeds {lo}..{hi - 1} kept", U13, w([kept[s] for s in c]), {"fz": "kept", "covers": len(c)}))
    rl = sorted(rej)
    if rl:
        cases.append(("13 rejected, Python returns", U13, w([rej[s] for s in rl]), {"fz": "rejected", "covers": len(rl)}))
    body = (f"(let X : List Nat := {X}; ((List.range {nch}).map (fun (i : Nat) => W (((List.range' ({S13} + {CH} * i) {CH}).filter "
            "(fun (s : Nat) => K s && !X.contains s)).map R)))" + (f" ++ [W ({rl}.map R)]" if rl else "") + ")")
    st.ints(lets, body, cases, gen=True, use_kit=False)
    cnt["X_len"] = len(X)
    info = {"seeds": f"{S13}..{S13 + N13 - 1}", "generated": N13, "kept": len(kept), "rejected_python_returns": len(rej),
            "python_raises_inside_precondition": raises_in, "raises_outside": raises_out_kinds, "counts": cnt}
    return st, info


def retarget(name):
    p = WORK / f"{name}.inputs.json"
    d = json.loads(p.read_text())
    for c in d:
        c["item"], c["decl"] = CAR
    p.write_text(json.dumps(d))
    j = WORK / f"{name}.json"
    dj = json.loads(j.read_text())
    for i in dj["inputs"]:
        i["item"], i["decl"] = CAR
    j.write_text(json.dumps(dj))
    print("retargeted", name, len(d), "calls")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "13"
    if what == "13":
        st, info = suite13()
        st.write()
        (WORK / "fz10_td13.fuzz.json").write_text(json.dumps(info, indent=1))
        print(json.dumps(info)[:1500], "| input chars", [len(i["text"]) for i in st.inputs])
    elif what == "14":
        fz.NBLOCK, fz.BLOCK = 5, 600
        mism = 0
        for s in range(f5.S0, f5.S0 + fz.NBLOCK * fz.BLOCK):
            e = f5.env14(s)
            p, (r, msg) = f5.rp.pre(e), f5.rp.returns(e)
            mism += p != r
        print("precondition vs Python mismatches:", mism)
        st, units = fz.suite_files("fz10_td14", fz.U14, "s14", f5.S0, f5.env14, f5.rp.pre, f5.LETS,
                                   "a column `shared` Float64 in one metrics frame and text in the other", f5.POOLS)
        st.write()
        (WORK / "fz10_td14.fuzz.json").write_text(json.dumps(units, indent=1))
        for u, d in units.items():
            print(u, d["generated"], d["kept"], d["python_raises_inside_precondition"][:5], d["note"][-300:])
        print("input chars", [len(i["text"]) for i in st.inputs], st.inputs[0]["item"])
    elif what == "retarget":
        retarget(sys.argv[2])
    elif what == "merge":
        merge(sys.argv[2])
    elif what == "fold15":
        fold15()
    elif what == "real":
        real()


def fold15():
    """fz10_td15 (fz6_td15_gen.py run as `... 600000 2800 350 fz10_td15`, then `retarget fz10_td15`) as ONE input
    whose result is one fold W per chunk of 350 seeds (expected = W of the per-seed digests in seed order).
    Lean-side harness fix: `al.drop r ++ al.take r` (rotation of the generated ROC frame) is written
    `List.drop r al ++ List.take r al`: on this blueprint `al.drop` now resolves to Pl.Frame.drop (drop columns by
    name), so the 2026-11-18 text no longer elaborates. Same list on both sides."""
    W_ = lambda t: __import__("functools").reduce(lambda h_, x: (h_ * 1099511628211 + x + 7) % (1 << 64), t, 14695981039346656037)  # noqa: E731
    j = json.loads((WORK / "fz10_td15.json").read_text())
    texts = [i["text"] for i in j["inputs"]]
    a = texts[0][:texts[0].rindex("(let X")]
    bodies = [t[len(a):-1] for t in texts]
    assert all(a + b + ")" == t for b, t in zip(bodies, texts))
    assert a.count("al.drop r ++ al.take r") == 1
    a = a.replace("al.drop r ++ al.take r", "List.drop r al ++ List.take r al")
    text = a + "(" + " ++ ".join("[W " + b + "]" for b in bodies) + "))"
    cases = []
    for ii in range(len(texts)):
        cs = sorted([c for c in j["cases"] if c["input"] == ii], key=lambda c: c["pos"])
        assert [c["pos"] for c in cs] == list(range(len(cs)))
        cases.append({"id": f"fz10_td15_c/chunk {ii}: {cs[0]['id']}..{cs[-1]['id']} ({len(cs)} kept seeds)",
                      "primitive": "train_run_15_printed_roc", "input": 0, "pos": ii, "kind": "int",
                      "expected": W_([c["expected"] for c in cs]), "fz": "kept", "covers": len(cs)})
    inp = dict(j["inputs"][0], text=text)
    (WORK / "fz10_td15_c.json").write_text(json.dumps(dict(j, suite="fz10_td15_c", inputs=[inp], cases=cases)))
    (WORK / "fz10_td15_c.inputs.json").write_text(json.dumps([{"item": inp["item"], "decl": inp["decl"], "inputs": [text]}]))
    print("fz10_td15_c", len(text), "chars", len(cases), "cases", sum(c["covers"] for c in cases), "seeds")


def real():
    """Real data (legacy/data through the real port): the locals of the real train.run at the entry of steps 13,
    14, 15, run on work/fz10_trainb_real (the feature files that fe.run wrote from legacy/data, train-b's run).
      15: the exact real inputs (ROC frames, confusion matrices, both flags); sas_d8 = the REAL sas_compat.sas_d8
          as a lookup table over the values met (an unlisted value gives "?MISSING").
      14: real final (Some/None), coefficients, metrics, ROC frames, flags; the scored sets are their first row
          (all real columns, names and dtypes; the unit is row-wise there). today = the text cell TODAY on both
          sides (out_digest replaces training_date).
      13: the first 80 rows of each real scored set, columns default_flag and pd_logistic (the full sets, 105000 and
          45000 rows, do not fit an eval input). FS = CPython's fsum (fz_t1_gen).
    Expected: the CURRENT slices executed verbatim (td.run_slice)."""
    import compare as cmp  # noqa: PLC0415
    import kit  # noqa: PLC0415
    import leanterm as lt  # noqa: PLC0415
    from credit_risk import sas_compat as sc  # noqa: PLC0415
    td.SLICES["s15"] = (945, 968, "if roc_valid_created:  # the judge's export")
    td.CODE["s15"] = td.slice_code("s15")
    snap, _, end, names = td.traced(WORK / "fz10_trainb_real")
    print("real train.run:", end, names)
    e13, e14, e15 = (dict(snap[k, "in"]) for k in ("s13", "s14", "s15"))
    keys13 = ["risk_scores_train", "risk_scores_validation"]
    rt = e13["risk_scores_train"].select(["default_flag", "pd_logistic"]).head(80)
    rv = e13["risk_scores_validation"].select(["default_flag", "pd_logistic"]).head(80)
    ns13, _, _ = td.run_slice("s13", {keys13[0]: rt, keys13[1]: rv})
    v13 = val13(ns13)
    k14 = ["model_coefficients", "training_metrics", "validation_metrics", "risk_scores_train", "risk_scores_validation",
           "roc_train", "roc_valid", "roc_train_created", "roc_valid_created", "final"]
    env14 = {k: e14[k] for k in k14}
    env14["risk_scores_train"] = env14["risk_scores_train"].head(1)
    env14["risk_scores_validation"] = env14["risk_scores_validation"].head(1)
    _, w14, _ = td.run_slice("s14", env14)
    d14 = fz.out_digest(w14)
    k15 = ["confusion_matrix_train", "confusion_matrix", "roc_train", "roc_valid", "roc_train_created", "roc_valid_created"]
    env15 = {k: e15[k] for k in k15}
    _, w15, _ = td.run_slice("s15", env15)
    d15 = fz.out_digest(w15)
    vals = [v for f in (env15["roc_train"], env15["roc_valid"]) for c in ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
            for v in f.get_column(c).to_list()]
    d8 = {cmp.fbits(v): sc.sas_d8(v) for v in vals if v is not None}
    for k in k14 + k15:
        v = env14.get(k, env15.get(k))
        print(k, (v.shape, dict(v.schema)) if isinstance(v, pl.DataFrame) else (v if not hasattr(v, "beta") else "LogisticFit"))
    print("13 sample: train defaults", int((rt["default_flag"] == 1).sum()), "valid defaults", int((rv["default_flag"] == 1).sum()),
          "created", ns13["roc_train_created"], ns13["roc_valid_created"], "| writes 14", [n for n, _ in w14], "| writes 15", [n for n, _ in w15])
    lets = (b4.W + b4.OF + b4.TS + b4.TCOL + t1.FS_LET
            + "let tf := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
            + "let bi := fun (b : Bool) => (if b then 1 else 0 : Int); "
            + "let OUT := fun (o : List (String × Tabular.Table Float)) => dg (o.length.toUInt64 :: o.flatMap (fun (p : String × Tabular.Table Float) => tS p.1 ++ tA p.2)); "
            + "let FIT : LogisticFit Float := { names := [], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [], loglik := 0.0, n_iter := 0, converged := true }; "
            + "let D : List (UInt64 × String) := [" + ", ".join(f"({k}, {lt.lean_str(t)})" for k, t in d8.items()) + "]; "
            + f"let d8 := fun (o : Option Float) => (match o with | none => {lt.lean_str(sc.sas_d8(None))} | some x => (D.lookup x.toBits).getD \"?MISSING\"); "
            + lt.lean_frame_let("RT13", rt) + lt.lean_frame_let("RV13", rv)
            + "".join(lt.lean_frame_let(k.upper(), env14[k]) for k in k14[:7])
            + lt.lean_frame_let("CMT", env15["confusion_matrix_train"]) + lt.lean_frame_let("CMV", env15["confusion_matrix"])
            + lt.lean_frame_let("RT15", env15["roc_train"]) + lt.lean_frame_let("RV15", env15["roc_valid"]))
    b = lambda x: "true" if x else "false"  # noqa: E731
    body = ("(let r := train_run_13_roc (α := Float) FS RT13 RV13; "
            "[W (tf r.1 ++ tf r.2.1 ++ [bi r.2.2.1, bi r.2.2.2]), "
            f"OUT (train_run_14_final_and_summary (Tabular.Cell.str (some \"TODAY\")) {'(some FIT)' if env14['final'] is not None else 'none'} "
            "MODEL_COEFFICIENTS TRAINING_METRICS VALIDATION_METRICS RISK_SCORES_TRAIN RISK_SCORES_VALIDATION ROC_TRAIN ROC_VALID "
            f"{b(env14['roc_train_created'])} {b(env14['roc_valid_created'])}), "
            f"OUT (train_run_15_printed_roc d8 CMT CMV RT15 RV15 {b(env15['roc_train_created'])} {b(env15['roc_valid_created'])})])")
    st = Suite("fz10_td_real")
    st.ints(lets, body, [("real 13 (first 80 rows of each real scored set)", U13, v13, {"fz": "real"}),
                         ("real 14 (real inputs, scored sets first row)", "train_run_14_final_and_summary", d14, {"fz": "real"}),
                         ("real 15 (exact real inputs, real sas_d8 table)", "train_run_15_printed_roc", d15, {"fz": "real"})],
            gen=False, table=True)
    st.write()
    print("input chars", [len(i["text"]) for i in st.inputs], "| D8", len(d8))


def merge(name):
    """One input instead of several: the shared lets once, the bodies concatenated with ++ (same cases, same
    expected values, positions renumbered). Writes work/<name>_m.json / .inputs.json."""
    j = json.loads((WORK / f"{name}.json").read_text())
    texts = [i["text"] for i in j["inputs"]]
    k = 0
    while all(len(t) > k and t[k] == texts[0][k] for t in texts):
        k += 1
    a = texts[0][:k]
    a = a[:a.rindex("(let X")]  # each body is "(let X : List Nat := [...]; ...)"
    bodies = [t[len(a):-1] for t in texts]
    assert all(a + b + ")" == t for b, t in zip(bodies, texts))
    text = a + "(" + " ++ ".join(bodies) + "))"
    off, cases = {}, []
    o = 0
    for ii in range(len(texts)):
        off[ii] = o
        o += sum(1 for c in j["cases"] if c["input"] == ii)
    for c in j["cases"]:
        c = dict(c)
        c["pos"] = off[c["input"]] + c["pos"]
        c["input"] = 0
        cases.append(c)
    inp = dict(j["inputs"][0])
    inp["text"] = text
    j2 = dict(j, suite=name + "_m", inputs=[inp], cases=cases)
    (WORK / f"{name}_m.json").write_text(json.dumps(j2))
    (WORK / f"{name}_m.inputs.json").write_text(json.dumps([{"item": inp["item"], "decl": inp["decl"], "inputs": [text]}]))
    print(name + "_m", len(text), "chars,", len(cases), "cases")


if __name__ == "__main__":
    main()
