"""Lean text of the judge's lambdas, and the Python mirror of the Lean data generators.

Three ways to get a Lean result back exactly (a `Float` prints with 6 decimals, so never print one):

1. DUMP_* lambdas, used with decl `Pl.zipB` on item `def:ExprOrNum`:
       inputs = [f"{DUMP_FRAME} [{term1}, {term2}] [()]"]
   The output is a Lean list of nested dumps (names, kinds, Option UInt64 / Int / Bool / String),
   parsed by compare.parse_lean and converted by compare.dump_to_canon.
2. token streams / digests (TOK kit), through a carrier `List Int -> List Int`:
   - units: decl `zz_carrier` on item `def:zz_carrier` (the identity; depends on both preludes and
     on every unit) -- the default of suite.Suite;
   - prelude suites: decl `Np.cumsumInt` on item `def:FloatArray_` (both preludes are in scope
     there); it returns the running sums of the integers we give it, compare.py takes the
     differences back (Suite(..., carrier="cumsum")).
       digest mode: `(KIT; [dg (tR frame1), dg (tC col2), ...])`   one 64-bit digest per case
       tokens mode: `(KIT; tk (tR frame))`                          the whole value, decodable
"""
from __future__ import annotations

M64 = (1 << 64) - 1
NAN_BITS = 0x7FF8000000000000  # Lean's Float.toBits returns this for every NaN

# ----------------------------------------------------------------------------- dump lambdas
_CT = "String × List (Option UInt64) × List (Option Int) × List (Option Bool) × List (Option String)"
_DC = (
    '(match c with '
    '| .f64 v => ("f64", v.map (fun o => o.map Float.toBits), [], [], []) '
    '| .int v => ("int", [], v, [], []) '
    '| .bool v => ("bool", [], [], v, []) '
    '| .str v => ("str", [], [], [], v) '
    '| .cell v => ("cell", v.map (fun x => (match x with | .num o => o.map Float.toBits | .str _ => none : Option UInt64)), [], '
    'v.map (fun x => (match x with | .num _ => some true | .str _ => some false : Option Bool)), '
    'v.map (fun x => (match x with | .str o => o | .num _ => none : Option String))) '
    f'| .null n => ("null", [], List.replicate n none, [], []) : {_CT})'
)
# Pl.Col Float -> (kind, f64 bits, ints, bools, strings); only the list of the kind is filled
# (a Null-dtype column `.null n` is the kind "null" with n nulls in the ints list)
DUMP_COL = f"(fun (c : Pl.Col Float) (_ : Unit) => {_DC})"
# Pl.Frame Float -> [(name, (kind, bits, ints, bools, strings)), ...]
DUMP_FRAME = f"(fun (fr : Pl.Frame Float) (_ : Unit) => fr.map (fun (p : String × Pl.Col Float) => (p.1, (fun (c : Pl.Col Float) => {_DC}) p.2)))"
# Tabular.Table Float -> rows of (name, kind, Option bits, Option String)
DUMP_TABLE = (
    "(fun (t : Tabular.Table Float) (_ : Unit) => t.map (fun (r : Tabular.Row Float) => r.map (fun (p : String × Tabular.Cell Float) => "
    '(match p.2 with | .num o => (p.1, "num", o.map Float.toBits, none) '
    '| .str o => (p.1, "str", none, o) : String × String × Option UInt64 × Option String))))'
)
# List Float / List (Option Float) -> bits
DUMP_FLOATS = "(fun (x : Float) (_ : Unit) => x.toBits)"
DUMP_OPTFLOATS = "(fun (x : Option Float) (_ : Unit) => x.map Float.toBits)"

# ----------------------------------------------------------------------------- token kit
# Every value becomes a List UInt64 (mirrored by compare.tok_*): tS string, tF/tI/tB/tT lists of
# Option Float/Int/Bool/String, tX a cell, tC a column, tR a frame, tA a table.
# tC is exhaustive over Pl.Col: .f64 1, .int 2, .bool 3, .str 4, .cell 5, .null 6 (`[6, n]`).
# dg = 64-bit digest of a token list (each step is a bijection of the state, so two streams that
# differ in exactly one token never collide); tk = the raw tokens.
_BASE = (
    "let mx := fun (h x : UInt64) => let g := (h ^^^ x) * 1099511628211; g ^^^ (g >>> 32); "
    "let dg := fun (t : List UInt64) => ((t.foldl mx 14695981039346656037).toNat : Int); "
    "let tk := fun (t : List UInt64) => t.map (fun x => (x.toNat : Int)); "
    "let tS := fun (s : String) => s.length.toUInt64 :: s.toList.map (fun c => c.toNat.toUInt64); "
    "let tF := fun (v : List (Option Float)) => v.length.toUInt64 :: v.flatMap (fun o => (match o with | none => [0] | some x => [1, x.toBits] : List UInt64)); "
    "let tI := fun (v : List (Option Int)) => v.length.toUInt64 :: v.flatMap (fun o => (match o with | none => [0] | some n => [if n < 0 then 2 else 1, n.natAbs.toUInt64] : List UInt64)); "
    "let tB := fun (v : List (Option Bool)) => v.length.toUInt64 :: v.flatMap (fun o => (match o with | none => [0] | some b => [1, if b then 1 else 0] : List UInt64)); "
    "let tT := fun (v : List (Option String)) => v.length.toUInt64 :: v.flatMap (fun o => (match o with | none => [0] | some s => 1 :: tS s : List UInt64)); "
)
_TX = "let tX := fun (c : Tabular.Cell Float) => (match c with | .num none => [1, 0] | .num (some x) => [1, 1, x.toBits] | .str none => [2, 0] | .str (some s) => 2 :: 1 :: tS s : List UInt64); "
_TC = "let tC := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: tF v | .int v => 2 :: tI v | .bool v => 3 :: tB v | .str v => 4 :: tT v | .cell v => {cell} | .null n => [6, n.toUInt64] : List UInt64); "
_TR = "let tR := fun (fr : Pl.Frame Float) => fr.length.toUInt64 :: fr.flatMap (fun p => tS p.1 ++ tC p.2); "
_TA = "let tA := fun (t : Tabular.Table Float) => t.length.toUInt64 :: t.flatMap (fun r => r.length.toUInt64 :: r.flatMap (fun p => tS p.1 ++ tX p.2)); "
# full kit (columns with cells, frames, tables)
KIT = _BASE + _TX + _TC.format(cell="5 :: v.length.toUInt64 :: v.flatMap tX") + _TR + _TA
# shorter kit for suites without tables or cell columns (a cell column tokenises as [5, length])
KIT_NOTABLE = _BASE + _TC.format(cell="[5, v.length.toUInt64]") + _TR

# ----------------------------------------------------------------------------- generators
# Seeded data generated INSIDE Lean (keeps the eval_decl inputs short) and mirrored bit for bit
# in Python (integer arithmetic only). hsh = splitmix64-style hash of (seed, index).
#   gF s n pe eh E : n Option Floats; with probability pe% an element of the edge list E (which may
#                    contain none), else a random float, random sign, exponent in [-eh, eh]
#   gI s n pn m off: n Option Ints; null with probability pn%, else a value in [-off, m - off)
GEN = (
    "let hsh := fun (s i : Nat) => let z : UInt64 := s.toUInt64 * 0x9E3779B97F4A7C15 + i.toUInt64 * 0xD1B54A32D192ED03 + 1; "
    "let z := (z ^^^ (z >>> 30)) * 0xBF58476D1CE4E5B9; let z := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB; z ^^^ (z >>> 31); "
    "let gF := fun (s n : Nat) (pe eh : UInt64) (E : List (Option Float)) => (List.range n).map (fun (i : Nat) => let u := hsh s i; let k : UInt64 := u >>> 52; "
    "if (u >>> 8) % 100 < pe then E.getD ((u >>> 20) % E.length.toUInt64).toNat none else "
    "some (Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)))); "
    "let gI := fun (s n : Nat) (pn m : UInt64) (off : Int) => (List.range n).map (fun (i : Nat) => let u := hsh s i; "
    "if (u >>> 8) % 100 < pn then (none : Option Int) else some ((((u >>> 20) % m).toNat : Int) - off)); "
)


def hsh(s: int, i: int) -> int:
    z = (s * 0x9E3779B97F4A7C15 + i * 0xD1B54A32D192ED03 + 1) & M64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return z ^ (z >> 31)


def gF(s: int, n: int, pe: int, eh: int, E: list) -> list:
    import struct

    out = []
    for i in range(n):
        u = hsh(s, i)
        if (u >> 8) % 100 < pe:
            out.append(E[(u >> 20) % len(E)])
        else:
            b = ((u >> 63) << 63) | (((1023 - eh + (u >> 52) % (2 * eh + 1)) << 52) & M64) | (u & 0xFFFFFFFFFFFFF)
            out.append(struct.unpack("<d", struct.pack("<Q", b))[0])
    return out


def gI(s: int, n: int, pn: int, m: int, off: int) -> list:
    out = []
    for i in range(n):
        u = hsh(s, i)
        out.append(None if (u >> 8) % 100 < pn else ((u >> 20) % m) - off)
    return out
