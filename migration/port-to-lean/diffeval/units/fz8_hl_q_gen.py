"""Re-evaluation of def:_hl_groups / def:_hl_groups_precond after the change of 2026-11-18 (n / g as
ONE correctly rounded division of the two ints; OverflowError clauses in the precondition).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz8_hl_q_gen.py <kind> <base> <N>
  ... fz8_hl_q_gen.py term <kind> <base> <N>     (the Lean term for that chunk)
  ... fz8_hl_q_gen.py check0                     (kind 0 mirrors the fz5 cases)

Inputs are generated inside Lean from the seed (the term printed by `term`, evaluated with
eval_decl(item_id="def:zz_carrier_e", decl="pr_ints", inputs=[term])) and mirrored here with the
same integer arithmetic. Per chunk the Lean returns [kept, skipped, digest]: a seed is skipped when
def:_hl_groups_precond (decided at Float) is false, kept otherwise, and the digest folds, over the
kept seeds, the seed and the output of _hl_groups. Python: a seed is skipped when
sas_compat._hl_groups raises, kept otherwise; same digest. Equal triples = equal outputs on every
kept seed AND the precondition rejects exactly the seeds on which Python raises (up to a digest
collision mod the prime 2^61 - 1).

DEC_PRECOND (not stored here: no item Lean is saved locally) is typed into the call as
  (decidable_of_iff _ (Iff.rfl : (fun (blocks : List Int) (n : Int) (g : Int) => <body of
  def:_hl_groups_precond with α := Float>) c.1 c.2.1 c.2.2 ↔ _hl_groups_precond (α := Float) c.1 c.2.1 c.2.2))
  The term elaborates only when the typed body is definitionally the item's (a wrong copy is
  refused: checked with the body `10 ≠ 0`), so the Decidable instance decides the item itself.
  (Tactic blocks are refused inside eval_decl inputs, so `by unfold ...` is not available.)

kind 0: the generator of fz5_hl_groups_gen.py (its code, not its docstring); seeds 700000..702199
        hold the fuzzer's 2000 kept cases (check0 compares with work/fz5_hl_groups.cases.json).
kind 1: division-targeted: g of 1..1100 bits (high bit set, random middle, random low bit), integer
        part k of the quotient up to 2^64 or scaled up to about 2^960, n = k g + floor(g/2) + d
        (quotient near k + 1/2, the boundary of floor(. + 0.5)) or k g + d, d in -3..3, or a small n
        against g; random signs; blocks [1, 2k + e] (they reveal m) or [1, 2k + e, small], e in -2..2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import kit  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

h = kit.hsh
P = 2305843009213693951
BS = [0, 1, 1, 2, 3, 5, 10, 15, 20, -1, -5, 7, 4503599627370496, 9007199254740992, 9007199254740993,
      4611686018427387904, 18446744073709551619, 10**20]
NP = [0, 1, 2, 5, 9, 10, 11, 14, 15, 16, 19, 20, 21, 25, 59, 60, 61, 100, -1, -10, 4503599627370496, 4503599627370497,
      9007199254740992, 9007199254740993, 1152921504606846976, 10**20, 10**310]
GP = [1, 2, 3, 4, 5, 7, 10, 20, 100, -1, -10, 0, 9007199254740993, 10**20, 8]


def gen0(s):
    L = (h(s, 1) >> 8) % 13
    mode = (h(s, 2) >> 8) % 10
    bl = []
    for i in range(L):
        u = h(s + 1000, i)
        bl.append((u >> 20) % 31 if mode < 8 else BS[(u >> 20) % 18] if mode < 9 else BS[12 + (u >> 20) % 6])
    if (h(s, 3) >> 8) % 10 < 8:
        n = sum(bl)
    else:
        k = (h(s, 3) >> 20) % 3
        n = NP[(h(s, 3) >> 24) % len(NP)] if k < 2 else (h(s, 3) >> 24) % 201
    g = 10 if (h(s, 4) >> 8) % 20 < 14 else GP[(h(s, 4) >> 20) % len(GP)]
    return bl, n, g


def gen1(s):
    u1, u2, u3, u4 = h(s, 11), h(s, 12), h(s, 13), h(s, 14)
    gb = 1 + (u1 >> 12) % 60 if (u1 >> 32) % 4 == 0 else 1 + (u1 >> 12) % 1100
    top = 2 ** (gb - 1)
    g = top + ((u2 * 2**64 + u3) * 2 ** max(0, gb - 129)) % top + u4 % 2
    if g > 2 * top - 1:
        g = 2 * top - 1
    v = h(s, 16)
    k = h(s, 15) >> (v % 64)
    if (v >> 8) % 5 == 0:
        k = h(s, 15) * 2 ** ((v >> 16) % 900)
    w = h(s, 17)
    d = w % 7 - 3
    if (w >> 16) % 4 == 0:
        n = h(s, 20) % 1000 - 500
    elif (w >> 8) % 3 == 0:
        n = k * g + d
    else:
        n = k * g + g // 2 + d
    sg = h(s, 18) % 4
    if sg in (0, 2):
        n = -n
    if sg in (1, 2):
        g = -g
    e = h(s, 19) % 5 - 2
    bl = [1, 2 * k + e] if (h(s, 19) >> 8) % 2 == 0 else [1, 2 * k + e, (h(s, 19) >> 16) % 30]
    return bl, n, g


def hs(r):
    x = len(r)
    for v in r:
        x = (x * 1000003 + v % P) % P
    return x


def chunk(kind, base, N):
    kept = skipped = 0
    D = 0
    for s in range(base, base + N):
        bl, n, g = (gen0 if kind == 0 else gen1)(s)
        try:
            r = sc._hl_groups(list(bl), n, g)
        except (ZeroDivisionError, OverflowError):
            skipped += 1
            continue
        kept += 1
        D = ((D * 1000003 + s) % P * 1000003 + hs(r)) % P
    return [kept, skipped, D]


TERM = r"""(let hsh : Nat → Nat → Nat := fun (s i : Nat) =>
    let z : UInt64 := s.toUInt64 * 0x9E3779B97F4A7C15 + i.toUInt64 * 0xD1B54A32D192ED03 + 1
    let z : UInt64 := (z ^^^ (z >>> 30)) * 0xBF58476D1CE4E5B9
    let z : UInt64 := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB
    (z ^^^ (z >>> 31)).toNat
  let P : Int := 2305843009213693951
  let BS : List Int := [0, 1, 1, 2, 3, 5, 10, 15, 20, -1, -5, 7, 4503599627370496, 9007199254740992, 9007199254740993, 4611686018427387904, 18446744073709551619, 10 ^ 20]
  let NP : List Int := [0, 1, 2, 5, 9, 10, 11, 14, 15, 16, 19, 20, 21, 25, 59, 60, 61, 100, -1, -10, 4503599627370496, 4503599627370497, 9007199254740992, 9007199254740993, 1152921504606846976, 10 ^ 20, 10 ^ 310]
  let GP : List Int := [1, 2, 3, 4, 5, 7, 10, 20, 100, -1, -10, 0, 9007199254740993, 10 ^ 20, 8]
  let gen0 : Nat → List Int × Int × Int := fun (s : Nat) =>
    let L : Nat := (hsh s 1 / 256) % 13
    let mode : Nat := (hsh s 2 / 256) % 10
    let bl : List Int := (List.range L).map (fun (i : Nat) =>
      let u : Nat := hsh (s + 1000) i
      if mode < 8 then (((u / 2 ^ 20) % 31 : Nat) : Int)
      else if mode < 9 then BS.getD ((u / 2 ^ 20) % 18) 0 else BS.getD (12 + (u / 2 ^ 20) % 6) 0)
    let n : Int := if (hsh s 3 / 256) % 10 < 8 then bl.foldl (· + ·) 0
      else if (hsh s 3 / 2 ^ 20) % 3 < 2 then NP.getD ((hsh s 3 / 2 ^ 24) % NP.length) 0
      else (((hsh s 3 / 2 ^ 24) % 201 : Nat) : Int)
    let g : Int := if (hsh s 4 / 256) % 20 < 14 then 10 else GP.getD ((hsh s 4 / 2 ^ 20) % GP.length) 0
    (bl, n, g)
  let gen1 : Nat → List Int × Int × Int := fun (s : Nat) =>
    let u1 : Nat := hsh s 11
    let u2 : Nat := hsh s 12
    let u3 : Nat := hsh s 13
    let u4 : Nat := hsh s 14
    let gb : Nat := if (u1 / 2 ^ 32) % 4 = 0 then 1 + (u1 / 2 ^ 12) % 60 else 1 + (u1 / 2 ^ 12) % 1100
    let top : Nat := 2 ^ (gb - 1)
    let g0 : Nat := top + ((u2 * 2 ^ 64 + u3) * 2 ^ (gb - 129)) % top + u4 % 2
    let g1 : Int := ((if g0 > 2 * top - 1 then 2 * top - 1 else g0 : Nat) : Int)
    let v : Nat := hsh s 16
    let k : Int := if (v / 256) % 5 = 0 then ((hsh s 15 * 2 ^ ((v / 2 ^ 16) % 900) : Nat) : Int)
      else ((hsh s 15 / 2 ^ (v % 64) : Nat) : Int)
    let w : Nat := hsh s 17
    let d : Int := ((w % 7 : Nat) : Int) - 3
    let n1 : Int := if (w / 2 ^ 16) % 4 = 0 then ((hsh s 20 % 1000 : Nat) : Int) - 500
      else if (w / 256) % 3 = 0 then k * g1 + d
      else k * g1 + g1 / 2 + d
    let sg : Nat := hsh s 18 % 4
    let n : Int := if sg = 0 || sg = 2 then -n1 else n1
    let g : Int := if sg = 1 || sg = 2 then -g1 else g1
    let e : Int := ((hsh s 19 % 5 : Nat) : Int) - 2
    let bl : List Int := if (hsh s 19 / 256) % 2 = 0 then [1, 2 * k + e]
      else [1, 2 * k + e, (((hsh s 19 / 2 ^ 16) % 30 : Nat) : Int)]
    (bl, n, g)
  let hs : List Int → Int := fun (r : List Int) =>
    r.foldl (fun (x v : Int) => (x * 1000003 + v % P) % P) (r.length : Int)
  let st : Int × Int × Int := (List.range NN).foldl (fun (st : Int × Int × Int) (j : Nat) =>
      let s : Nat := BASE + j
      let c : List Int × Int × Int := if KIND = 0 then gen0 s else gen1 s
      if @decide (_hl_groups_precond (α := Float) c.1 c.2.1 c.2.2)
          DEC_PRECOND then
        (st.1 + 1, st.2.1, ((st.2.2 * 1000003 + (s : Int)) % P * 1000003
          + hs (_hl_groups (α := Float) c.1 c.2.1 c.2.2)) % P)
      else (st.1, st.2.1 + 1, st.2.2))
    (0, 0, 0)
  [st.1, st.2.1, st.2.2])"""


def term(kind, base, N):
    return TERM.replace("NN", str(N)).replace("BASE", str(base)).replace("KIND", str(kind))


if __name__ == "__main__":
    if sys.argv[1] == "check0":
        cs = json.loads((HERE.parent / "work" / "fz5_hl_groups.cases.json").read_text())
        bad = [c["seed"] for c in cs if [list(x) if isinstance(x, list) else x for x in gen0(c["seed"])] != [c["blocks"], c["n"], c["g"]]]
        print("fz5 cases", len(cs), "seeds", cs[0]["seed"], "..", cs[-1]["seed"], "mirror differs on", len(bad), bad[:5])
    elif sys.argv[1] == "term":
        print(term(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])))
    else:
        kind, base, N = map(int, sys.argv[1:4])
        print(kind, base, N, chunk(kind, base, N))
