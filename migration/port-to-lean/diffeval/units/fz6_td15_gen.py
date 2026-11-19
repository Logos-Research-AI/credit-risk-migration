"""Fuzz 2026-11-18 of def:train_run_15_printed_roc + def:train_run_15_printed_roc_precond
(revisions 221f3ea4... / 066b5069...), by a non-author.  Suite fz6_td15 on def:zz_carrier_t.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz6_td15_gen.py [first [n [chunk]]]

Per seed s every input is built INSIDE Lean (kit.GEN) and mirrored here (kit.hsh / gF / gI):
  k = H(s,9100,4): roc_train_created = k//2 == 0, roc_valid_created = k%2 == 0 (all four flag pairs)
  ROC frame (a = 8s+1 train, 8s+2 valid): rows from [0,1,1,2,3,5]; ROCModel: constant "Training Set" /
     random from a pool with null, "", "A", "é", " " / ALL NULL / random non-null; the seven statistics
     gF(...,70% pool E: none, NaN, +-inf, +-0, 1, 0.5, 1e-5 and 0.99995 each one ulp either side, 5e-324, 1e300 ...);
     an extra column (none / Int64 / Boolean / String) and the column order rotated and maybe reversed
  confusion matrices (a = 8s+3, 8s+4): width 0..4 (0 in 1 of 7), 0..5 rows, each column Float64 / Int64 / Boolean /
     String / Null dtype
  sas_d8 := injective encoding of the argument on both sides (t18_gen ENCODERS['sas_d8']).
Expected: lines of train.run from `roc_cols = [` to the %put block executed verbatim (compiled from the file),
write_sas_csv recording (name, frame) and still writing. Precondition (def:train_run_15_printed_roc_precond): seven
Float64 statistics and a String ROCModel (always true here, asserted) and: an exported ROC frame with rows has a
non-null label. A seed outside it is counted (rejected) and not sent. One case = one seed.
"""
from __future__ import annotations

import contextlib, io, json, struct, sys, tempfile, textwrap
from collections import Counter
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import t18_gen as t  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402
import suite as suite_mod  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
NAN, INF = float("nan"), float("inf")


def ulp(x, k):
    b = struct.unpack("<Q", struct.pack("<d", x))[0]
    return struct.unpack("<d", struct.pack("<Q", b + k))[0]


E = [None, None, NAN, INF, -INF, 0.0, -0.0, 1.0, 0.5, 1e-5, ulp(1e-5, 1), ulp(1e-5, -1), 0.99995, ulp(0.99995, 1), ulp(0.99995, -1),
     5e-324, 1e300, -3.5, 123456.789, 100.0, ulp(100.0, -1), 99999.99995]
LB = [None, "", "A", "Training Set", "é", " "]
SP = [None, "x", "", "é", "a,b", "l\nm"]
RC = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
HTS = [0, 1, 1, 2, 3, 5]
WS = [0, 1, 2, 3, 4, 4, 2]
H = lambda s, k, m: kit.hsh(s, k) % m  # noqa: E731


def lf(x): return "none" if x is None else f"(some (Float.ofBits {t.fb(x)}))"
def lstr(x): return "none" if x is None else "(some " + json.dumps(x, ensure_ascii=False) + ")"


LETS = (
    t.W + t.BI + t.TS + t.TX + t.TD + t.FMT
    + "let E : List (Option Float) := [" + ", ".join(lf(x) for x in E) + "]; "
    + "let LB : List (Option String) := [" + ", ".join(lstr(x) for x in LB) + "]; "
    + "let SP : List (Option String) := [" + ", ".join(lstr(x) for x in SP) + "]; "
    + "let RC : List String := " + json.dumps(RC) + "; "
    + "let H := fun (s k m : Nat) => (hsh s k).toNat % m; "
    + "let FC := fun (s n : Nat) => (Pl.Col.f64 (gF s n 70 30 E) : Pl.Col Float); "
    + "let IC := fun (s n : Nat) => (Pl.Col.int (gI s n 20 7 3) : Pl.Col Float); "
    + "let BC := fun (s n : Nat) => (Pl.Col.bool ((gI s n 20 2 0).map (fun (o : Option Int) => o.map (fun (k : Int) => k == 1))) : Pl.Col Float); "
    + "let TC := fun (s n : Nat) => (Pl.Col.str ((gI s n 0 6 0).map (fun (o : Option Int) => (match o with | some k => SP.getD k.toNat none | none => none : Option String))) : Pl.Col Float); "
    + f"let HT := fun (s k : Nat) => ({HTS} : List Nat).getD (H s k 6) 1; "
    + "let ROC := fun (a : Nat) => let n := HT a 9102; let m := H a 9101 4; "
      "let lab : List (Option String) := (if m == 0 then List.replicate n (some \"Training Set\") else if m == 1 then "
      "(gI (a * 16) n 0 6 0).map (fun (o : Option Int) => (match o with | some k => LB.getD k.toNat none | none => none : Option String)) "
      "else if m == 2 then List.replicate n none else "
      "(gI (a * 16) n 0 5 0).map (fun (o : Option Int) => (match o with | some k => LB.getD (k.toNat + 1) none | none => none : Option String))); "
      "let base : Pl.Frame Float := (\"ROCModel\", Pl.Col.str lab) :: (List.range 7).map (fun (j : Nat) => (RC.getD j \"\", FC (a * 16 + 1 + j) n)); "
      "let ex : Pl.Frame Float := (match H a 9105 4 with | 1 => [(\"Extra\", IC (a * 16 + 9) n)] | 2 => [(\"Extra\", BC (a * 16 + 9) n)] | 3 => [(\"Extra\", TC (a * 16 + 9) n)] | _ => []); "
      "let al : Pl.Frame Float := base ++ ex; let r := H a 9104 al.length; let rot := al.drop r ++ al.take r; "
      "(if H a 9106 3 == 0 then rot.reverse else rot : Pl.Frame Float); "
    + "let CM := fun (a : Nat) => let n := HT a 9151; let w := ([0, 1, 2, 3, 4, 4, 2] : List Nat).getD (H a 9152 7) 0; "
      "((List.range w).map (fun (j : Nat) => (\"c\" ++ toString j, (match H a (9160 + j) 5 with | 0 => FC (a * 16 + j) n | 1 => IC (a * 16 + j) n | 2 => BC (a * 16 + j) n | 3 => TC (a * 16 + j) n | _ => Pl.Col.null n : Pl.Col Float))) : Pl.Frame Float); "
    + "let ONE := fun (s : Nat) => let k := H s 9100 4; "
      "let o := train_run_15_printed_roc d8 (CM (s * 8 + 3)) (CM (s * 8 + 4)) (ROC (s * 8 + 1)) (ROC (s * 8 + 2)) (k / 2 == 0) (k % 2 == 0); "
      "W ((o.length : Int) :: o.flatMap TDN); "
)


def lab_py(a, n):
    m = H(a, 9101, 4)
    if m == 0: return ["Training Set"] * n
    if m == 1: return [None if k is None else LB[k] for k in kit.gI(a * 16, n, 0, 6, 0)]
    if m == 2: return [None] * n
    return [None if k is None else LB[k + 1] for k in kit.gI(a * 16, n, 0, 5, 0)]


def FC(name, s, n): return pl.Series(name, kit.gF(s, n, 70, 30, E), dtype=pl.Float64)
def IC(name, s, n): return pl.Series(name, kit.gI(s, n, 20, 7, 3), dtype=pl.Int64)
def BC(name, s, n): return pl.Series(name, [None if k is None else k == 1 for k in kit.gI(s, n, 20, 2, 0)], dtype=pl.Boolean)
def TC(name, s, n): return pl.Series(name, [None if k is None else SP[k] for k in kit.gI(s, n, 0, 6, 0)], dtype=pl.String)


def roc_py(a):
    n = HTS[H(a, 9102, 6)]
    cols = [pl.Series("ROCModel", lab_py(a, n), dtype=pl.String)] + [FC(c, a * 16 + 1 + j, n) for j, c in enumerate(RC)]
    x = H(a, 9105, 4)
    if x == 1: cols.append(IC("Extra", a * 16 + 9, n))
    elif x == 2: cols.append(BC("Extra", a * 16 + 9, n))
    elif x == 3: cols.append(TC("Extra", a * 16 + 9, n))
    r = H(a, 9104, len(cols))
    cols = cols[r:] + cols[:r]
    if H(a, 9106, 3) == 0: cols.reverse()
    return pl.DataFrame(cols)


def cm_py(a):
    n = HTS[H(a, 9151, 6)]
    w = WS[H(a, 9152, 7)]
    cols = []
    for j in range(w):
        k = H(a, 9160 + j, 5)
        cols.append([FC, IC, BC, TC][k](f"c{j}", a * 16 + j, n) if k < 4 else pl.Series(f"c{j}", [None] * n, dtype=pl.Null))
    return pl.DataFrame(cols)


def env_of(s):
    k = H(s, 9100, 4)
    return {"confusion_matrix_train": cm_py(s * 8 + 3), "confusion_matrix": cm_py(s * 8 + 4),
            "roc_train": roc_py(s * 8 + 1), "roc_valid": roc_py(s * 8 + 2),
            "roc_train_created": k // 2 == 0, "roc_valid_created": k % 2 == 0}


def labelled(f): return f.height == 0 or f["ROCModel"].null_count() < f.height


def pre(e):
    for f in (e["roc_train"], e["roc_valid"]):
        assert f.schema["ROCModel"] == pl.String and all(f.schema[c] == pl.Float64 for c in RC)
    return (not e["roc_train_created"] or labelled(e["roc_train"])) and (not e["roc_valid_created"] or labelled(e["roc_valid"]))


def code():
    L = Path(train.__file__).read_text().splitlines(keepends=True)
    a = next(i for i, l in enumerate(L) if l.strip().startswith("roc_cols = ["))
    b = next(i for i, l in enumerate(L) if "train.sas:426-432" in l)
    src = "".join(L[a:b])
    assert "confusion_matrix.width > 0" in src and "roc_train_created" in src
    return compile(textwrap.dedent(src), "train_slice", "exec"), a + 1, b


CODE, LA, LB_ = code()


def run(e):
    writes, ns = [], dict(vars(train)); ns.update(e)
    o_w, o_d = sc.write_sas_csv, sc.sas_d8

    def w_write(df, path, formats=None):
        writes.append((Path(path).name, df)); return o_w(df, path, formats=formats)

    sc.write_sas_csv, sc.sas_d8 = w_write, t.ENCODERS["sas_d8"]
    try:
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            ns["output_dir"] = Path(d); exec(CODE, ns)  # noqa: S102
    finally:
        sc.write_sas_csv, sc.sas_d8 = o_w, o_d
    return writes


def digest(writes):
    return t.w([len(writes)] + [x for n, df in writes for x in t.tdn(n, df)])


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 600000
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 2800
    chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 350
    name = sys.argv[4] if len(sys.argv) > 4 else "fz6_td15"
    st = Suite(name); st.item, st.decl = "def:zz_carrier_t", "zz_carrier_t"
    cnt, raises = Counter(), []
    for c0 in range(first, first + n, chunk):
        seeds, cases, c1 = [], [], min(c0 + chunk, first + n)
        for s in range(c0, c1):
            e = env_of(s); cnt["generated"] += 1
            ok = pre(e)
            try:
                wr = run(e)
            except Exception as ex:  # noqa: BLE001
                raises.append((s, ok, type(ex).__name__, str(ex)[:80])); cnt["raises_in" if ok else "raises_out"] += 1; continue
            if not ok:
                cnt["rejected_python_returns"] += 1; continue
            cnt["kept"] += 1
            cnt["files:" + ",".join(nm[8:-4] for nm, _ in wr)] += 1
            k = H(s, 9100, 4); cnt[f"flags t={k//2==0} v={k%2==0}"] += 1
            cnt["cm_width0"] += e["confusion_matrix"].width == 0
            cnt["alllabelnull_unexported_rows"] += any(f.height > 0 and f["ROCModel"].null_count() == f.height and not c
                                                       for f, c in ((e["roc_train"], e["roc_train_created"]), (e["roc_valid"], e["roc_valid_created"])))
            seeds.append(s); cases.append((f"seed{s}", "train_run_15_printed_roc", digest(wr), {"fz": "kept"}))
        X = [s for s in range(c0, c1) if s not in set(seeds)]
        body = f"(let X : List Nat := {X}; ((List.range' {c0} {c1 - c0}).filter (fun (s : Nat) => !X.contains s)).map ONE)"
        st.ints(LETS, body, cases, gen=True, use_kit=False)
    st.write()
    print(dict(cnt)); print("raises", raises[:10])
    (HERE.parent / "work" / f"{name}.fuzz.json").write_text(json.dumps(
        {"generated": cnt["generated"], "kept": cnt["kept"], "counts": dict(cnt), "raises": raises, "slice_lines": [LA, LB_]}, indent=1))


main()
