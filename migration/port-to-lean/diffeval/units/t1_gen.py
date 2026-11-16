"""T1 of the update after verification (2026-11-16): _SE_EPS, _SQRTBIG, _groups, _pairs,
roc_association, association_table against the port as it stands.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t1_gen.py
      -> diffeval/work/t1_roc.json, t1_roc.inputs.json, t1_roc.in<k>.txt (one eval_decl input each)
  eval_decl each input on def:zz_carrier_s / zz_carrier_s; outputs, one per line, in work/t1_roc.out.txt
  ... python diffeval/compare.py diffeval/work/t1_roc.json diffeval/work/t1_roc.out.txt

math.fsum is the explicit parameter `fsum` of roc_association (RULEBOOK 2.7 G15). On the Lean side
it is a lookup table: digest of the bits of the list the unit passes -> bits of the value the
port's math.fsum returned on that list (recorded here by wrapping math.fsum during the real
calls). A list the port never passed gives the sentinel Float.ofBits 4660, which no result holds.

Data:
  scen   (default_flag, pd_logistic) of risk_scores_validation.csv as sas_compat.proc_import_csv
         (guessingrows=20) returns them, for the scenarios of the plan. The six fix_* scenarios
         and edge_metrics_a/b/c whole; real_metrics (45,000 rows) in slices (the input of
         eval_decl is text sent through the tool, and the Lean is quadratic).
         Scores are sent as integers over a power of ten; the generator asserts that the float
         quotient is the imported value bit for bit.
  hand   the explicit sets of b4_gen.C and new ones around _SE_EPS, classes of one observation,
         limits at 0 and 1
  rand   seeded sets generated on both sides (kit.gF / kit.gI)
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

SCEN = HERE.parents[3] / "judge" / "scenarios"
ITEM, DECL = "def:zz_carrier_s", "zz_carrier_s"
LABEL = "Logistic Model"
nan, inf = float("nan"), float("inf")
up, dn = (lambda x: math.nextafter(x, inf)), (lambda x: math.nextafter(x, -inf))
raw, lf, w, o = b4.raw, b4.lf, b4.w, b4.o


def fb(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b & ((1 << 64) - 1)))[0]


# ---------------------------------------------------------------- the recorded math.fsum
FSUM: dict[int, int] = {}
_orig_fsum = math.fsum


def _rec_fsum(xs):
    xs = list(xs)
    r = _orig_fsum(xs)
    FSUM[w([cmp.fbits(x) for x in xs])] = raw(r)
    return r


math.fsum = _rec_fsum


def four(y: pl.Series, s: pl.Series) -> list[int]:
    """digests of _pairs, roc_association without label, with label, association_table, _groups x 2"""
    q = sc._pairs(y, s)
    r0 = sc.roc_association(y, s)
    r1 = sc.roc_association(y, s, LABEL)
    a = sc.association_table(y, s)
    d = pl.DataFrame({"y": y.cast(pl.Float64), "s": s.cast(pl.Float64)}).drop_nulls()
    ss = np.asarray(d.get_column("s").to_numpy(), dtype=np.float64)
    g = [w([int(x) for x in sc._groups(ss, e).tolist()]) for e in (sc._TIE_EPS, sc._SE_EPS)]
    return [w([q.conc, q.disc, q.tied, q.n1, q.n0] + b4.fa(q.v10) + b4.fa(q.v01)),
            w([0] + b4.roc_tok(r0)), w([1] + b4.frame_tok(r1)),
            w(o(a.concordant_pct) + o(a.discordant_pct) + o(a.tied_pct) + [a.pairs] + o(a.somers_d)
              + o(a.gamma) + o(a.tau_a) + o(a.c)), w(g)]


UNITS = ["_pairs", "roc_association", "roc_association", "association_table", "_groups"]
WHAT = ["", " (no label -> record)", " (label -> frame)", "", " (the _TIE_EPS and the _SE_EPS groups of the usable scores)"]

PRE = (b4.FCOL + b4.W + b4.FA + b4.OF + b4.TS + b4.TCOL
       + "let P := fun (y s : Pl.Col Float) => let q := _pairs (α := Float) y s; W ([q.conc, q.disc, q.tied, q.n1, q.n0] ++ fa q.v10 ++ fa q.v01); "
       + "let R := fun (y s : Pl.Col Float) (l : Option String) => W (match roc_association (α := Float) FS y s l with "
         "| .inl r => 0 :: (o r.area ++ o r.std_err ++ o r.lower ++ o r.upper ++ o r.somers_d ++ o r.gamma ++ o r.tau_a) "
         "| .inr fr => 1 :: (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2) : List Int); "
       + "let A := fun (y s : Pl.Col Float) => let r := association_table (α := Float) y s; W (o r.concordant_pct ++ o r.discordant_pct ++ o r.tied_pct ++ [r.pairs] ++ "
         "o r.somers_d ++ o r.gamma ++ o r.tau_a ++ o r.c); "
       + "let GR := fun (y s : Pl.Col Float) => let ss : List Float := (List.zip (Pl.Col.asF64 y) (Pl.Col.asF64 s)).filterMap "
         "(fun (r : Option Float × Option Float) => (match r.1, r.2 with | some _, some b => some b | _, _ => none : Option Float)); "
         "W [W (_groups (α := Float) (Np.NDArray.d1 ss) _TIE_EPS), W (_groups (α := Float) (Np.NDArray.d1 ss) _SE_EPS)]; "
       + "let ALL := fun (d : Pl.Col Float × Pl.Col Float) => [P d.1 d.2, R d.1 d.2 none, R d.1 d.2 (some \"" + LABEL + "\"), A d.1 d.2, GR d.1 d.2]; "
       # compact encodings of imported columns
       + "let YS := fun (s : String) => (Pl.Col.f64 (s.toList.map (fun (c : Char) => if c == '1' then some (1.0 : Float) else if c == '0' then some (0.0 : Float) else none)) : Pl.Col Float); "
       + "let SK := fun (d : Float) (ks : List Nat) => (Pl.Col.f64 (ks.map (fun (k : Nat) => some (k.toFloat / d))) : Pl.Col Float); ")


def fs_let(keys) -> str:
    """the Lean `fsum` for the lists recorded under `keys`"""
    tbl = ", ".join(f"({k}, {FSUM[k]})" for k in sorted(keys))
    return (b4.W + f"let TBL : List (Int × UInt64) := [{tbl}]; "
            "let FS := fun (xs : List Float) => (match TBL.lookup (W (xs.map (fun (x : Float) => (x.toBits.toNat : Int)))) with "
            "| some b => Float.ofBits b | none => Float.ofBits 4660 : Float); ")


class Group:
    """one eval_decl input: data sets, each giving the five digests"""

    def __init__(self, st: Suite, extra_lets: str = "", gen: bool = False):
        self.st, self.extra, self.gen = st, extra_lets, gen
        self.terms, self.cases, self.keys = [], [], set()

    def add(self, name: str, y: pl.Series, s: pl.Series, term: str):
        before = set(FSUM)
        FSUM_snapshot = dict(FSUM)
        FSUM.clear()
        f = four(y, s)
        self.keys |= set(FSUM)
        FSUM_snapshot.update(FSUM)
        FSUM.update(FSUM_snapshot)
        del before
        self.terms.append(term)
        self.cases += [(name + WHAT[i], UNITS[i], f[i]) for i in range(5)]

    def flush(self):
        if not self.terms:
            return
        lets = fs_let(self.keys) + PRE.replace(b4.W, "", 1) + self.extra
        body = "([" + ", ".join(self.terms) + "] : List (Pl.Col Float × Pl.Col Float)).flatMap ALL"
        self.st.ints(lets, body, self.cases, gen=self.gen, use_kit=False)
        self.terms, self.cases, self.keys = [], [], set()


def imported(name: str):
    f = sc.proc_import_csv(SCEN / name / "risk_scores_validation.csv", guessingrows=20)
    return f.get_column("default_flag"), f.get_column("pd_logistic")


def enc(y: pl.Series, s: pl.Series, dec: int) -> str:
    """Lean term of the pair of columns: y as a string of 0 / 1, the scores as integers / 10^dec"""
    assert y.dtype == pl.Float64 and s.dtype == pl.Float64 and y.null_count() == 0 and s.null_count() == 0
    yl, sl = y.to_list(), s.to_list()
    assert all(v in (0.0, 1.0) for v in yl)
    d = float(10**dec)
    ks = [round(x * d) for x in sl]
    assert all(raw(k / d) == raw(x) and 0 <= k < 2**53 for k, x in zip(ks, sl, strict=True))
    return f'(YS "{"".join("1" if v == 1.0 else "0" for v in yl)}", SK {lf(d)} [{", ".join(map(str, ks))}])'


def suite() -> Suite:
    st = Suite("t1_roc")
    st.item, st.decl = ITEM, DECL
    # ---- constants
    st.ints("", "[((_SE_EPS (α := Float)).toBits.toNat : Int), ((_SQRTBIG (α := Float)).toBits.toNat : Int), ((_TIE_EPS (α := Float)).toBits.toNat : Int)]",
            [("_SE_EPS bits", "_SE_EPS", cmp.fbits(sc._SE_EPS)), ("_SQRTBIG bits", "_SQRTBIG", cmp.fbits(sc._SQRTBIG)),
             ("_TIE_EPS bits", "_TIE_EPS", cmp.fbits(sc._TIE_EPS))], use_kit=False)
    # ---- the fix scenarios, whole
    g = Group(st)
    for name in ("fix_Q26_small", "fix_Q26_ties", "fix_Q26_nodefaulter", "fix_Q23_alldefaulters", "fix_Q23_tie", "fix_Q23_nodefaulter"):
        y, s = imported(name)
        g.add(f"scenario {name}, whole ({y.len()} rows)", y, s, enc(y, s, 4))
    g.flush()
    # ---- edge_metrics a, b, c, whole (one input each)
    for name in ("edge_metrics_a", "edge_metrics_b", "edge_metrics_c"):
        y, s = imported(name)
        g = Group(st)
        g.add(f"scenario {name}, whole ({y.len()} rows)", y, s, enc(y, s, 4))
        g.flush()
    # ---- edge_metrics a, b, c, first 300 rows (fallback if the whole files do not run)
    g = Group(st)
    for name in ("edge_metrics_a", "edge_metrics_b", "edge_metrics_c"):
        y, s = imported(name)
        g.add(f"scenario {name}, rows 1-300", y.head(300), s.head(300), enc(y.head(300), s.head(300), 4))
    g.flush()
    # ---- real_metrics: slices
    y, s = imported("real_metrics")
    for nm, idx in (("rows 1-300", list(range(300))), ("every 150th row (300 rows)", list(range(0, 45000, 150))),
                    ("rows 20001-20300", list(range(20000, 20300)))):
        g = Group(st)
        ys, ss_ = y.gather(idx), s.gather(idx)
        g.add(f"scenario real_metrics, {nm}", ys, ss_, enc(ys, ss_, 10))
        g.flush()
    # ---- hand-made sets
    X = dict(b4.C)
    e, t = sc._SE_EPS, sc._TIE_EPS
    for i, top in enumerate((0.5, 0.3, 0.85, 1.0, 2 * e, 1e-3)):
        for dlt in (-2, -1, 0, 1, 2):
            v = fb(raw(top - e) + dlt)
            X[f"se_eps top={top!r} v=(top-eps){dlt:+d}ulp"] = ([1., 0., 1., 0.], "f64", [top, v, v, top], "f64")
    h = 2.0**-53
    X["x10 1000 ulps of 0.5"] = ([1., 0.], "f64", [0.5, 0.5 - 1000 * h], "f64")
    X["x10 1001 ulps of 0.5"] = ([1., 0.], "f64", [0.5, 0.5 - 1001 * h], "f64")
    X["x10 999 ulps of 0.5 rev"] = ([0., 1.], "f64", [0.5, 0.5 - 999 * h], "f64")
    X["tied for area, different for se (1e-9), 1/1"] = ([1., 0.], "f64", [0.5, 0.5 - 1e-9], "f64")
    X["tied for area, different for se (1e-9), 1/1 rev"] = ([0., 1.], "f64", [0.5, 0.5 - 1e-9], "f64")
    X["tied for both, 1/1"] = ([1., 0.], "f64", [0.5, 0.5], "f64")
    X["1e-9 apart, 3/3"] = ([1., 0., 1., 0., 1., 0.], "f64", [0.5, 0.5 - 1e-9, 0.5 - 2e-9, 0.5 - 3e-9, 0.5 - 1.2e-8, 0.5 - 1.25e-8], "f64")
    X["one defaulter, two others (x10)"] = ([1., 0., 0.], "f64", [0.5, 0.2, 0.7], "f64")
    X["one non-defaulter, three defaulters"] = ([0., 1., 1., 1.], "f64", [0.4, 0.2, 0.7, 0.4], "f64")
    X["area 0, 1/1"] = ([1., 0.], "f64", [0.2, 0.7], "f64")
    X["area 1, 1/1"] = ([0., 1.], "f64", [0.2, 0.7], "f64")
    X["area 0.25: lower below 0"] = ([1., 0., 1., 0.], "f64", [0.1, 0.2, 0.3, 0.4], "f64")
    X["area 0, 2/2"] = ([1., 1., 0., 0.], "f64", [0.1, 0.2, 0.3, 0.4], "f64")
    X["area 1, 2/2"] = ([0., 0., 1., 1.], "f64", [0.1, 0.2, 0.3, 0.4], "f64")
    X["chain se_eps"] = ([1., 0.] * 5, "f64", [0.6 - 0.7 * e * i for i in range(10)], "f64")
    X["chain between eps"] = ([0., 1., 1., 0., 1., 0., 0., 1.], "f64", [0.6 - 0.4 * t * i for i in range(8)], "f64")
    X["nan and near ties"] = ([1., 0., 1., 0., 1., 0.], "f64", [nan, 0.5, 0.5 - e / 2, 0.5 - 2 * e, nan, 0.5 - t], "f64")
    X["nulls and near ties"] = ([1., None, 0., 1., 0., 1.], "f64", [0.5, 0.4, None, 0.5 - 2 * e, 0.5 - e, 0.5 - t / 2], "f64")
    X["null dtype y"] = ([None, None], "null", [0.1, 0.2], "f64")
    X["y other values"] = ([2., 1., 0., 3., 1., 0.], "f64", [0.9, 0.8, 0.8 - e, 0.1, 0.8 - 2 * e, 0.3], "f64")

    def lcol(vals, kind):
        return f"(Pl.Col.null {len(vals)} : Pl.Col Float)" if kind == "null" else b4.col(vals, kind)

    def pser(vals, kind):
        return pl.Series(vals, dtype=pl.Null) if kind == "null" else (
            pl.Series(vals, dtype=pl.Float64, nan_to_null=False) if kind == "f64" else b4.ser(vals, kind))

    names = list(X)
    for k in range(0, len(names), 20):
        g = Group(st)
        for n in names[k:k + 20]:
            yv, yk, sv, sk = X[n]
            g.add(f"hand: {n}", pser(yv, yk), pser(sv, sk), f"({lcol(yv, yk)}, {lcol(sv, sk)})")
        g.flush()
    # ---- seeded random sets, generated on both sides
    EL = "[" + ", ".join("none" if x is None else f"some {lf(x)}" for x in b4.EDGE) + "]"
    J2 = [0.0, e, -e, e / 2, up(e), dn(e), 2 * e, 0.75 * e, t, -t, t / 2, 1e-9]
    RG = ("let RI := fun (s n : Nat) => (Pl.Col.int (gI s n 5 3 0) : Pl.Col Float); "
          f"let RC := fun (s n : Nat) (pe eh : UInt64) => (Pl.Col.f64 (gF s n pe eh {EL}) : Pl.Col Float); "
          f"let J : List Float := [{', '.join(lf(j) for j in J2)}]; "
          "let RG := fun (s n : Nat) (m : UInt64) => (Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => some (Float.ofInt a / 100.0 + J.getD b.toNat 0.0) | _, _ => none : Option Float)) "
          f"(gI s n 4 m 0) (gI (s + 1) n 0 {len(J2)} 0)) : Pl.Col Float); ")
    g = Group(st, RG, gen=True)
    for seed, n, mode in [(1211, 200, "cont"), (1221, 250, 50), (1231, 150, "mix"), (1241, 130, 6), (1251, 9, "cont"), (1261, 17, 3),
                          (1271, 40, "mix"), (1281, 64, 12), (1291, 120, 2), (1301, 100, 1)]:
        y = pl.Series(kit.gI(seed, n, 5, 3, 0), dtype=pl.Int64)
        if isinstance(mode, int):
            k_, j = kit.gI(seed + 1, n, 4, mode, 0), kit.gI(seed + 2, n, 0, len(J2), 0)
            sv = [None if a is None else float(a) / 100.0 + J2[b] for a, b in zip(k_, j, strict=True)]
            term = f"(RI {seed} {n}, RG {seed + 1} {n} {mode})"
        else:
            pe, eh = (0, 3) if mode == "cont" else (8, 40)
            sv = kit.gF(seed + 1, n, pe, eh, b4.EDGE)
            term = f"(RI {seed} {n}, RC {seed + 1} {n} {pe} {eh})"
        g.add(f"random seed={seed} n={n} {mode if isinstance(mode, str) else f'grid of {mode} levels + offsets of the size of the two eps'}",
              y, pl.Series(sv, dtype=pl.Float64, nan_to_null=False), term)
    g.flush()
    return st


if __name__ == "__main__":
    st = suite()
    st.write()
    for i, inp in enumerate(st.inputs):
        (HERE.parent / "work" / f"t1_roc.in{i}.txt").write_text(inp["text"])
        print(i, len(inp["text"]), "chars;", sum(1 for c in st.cases if c["input"] == i), "cases")
