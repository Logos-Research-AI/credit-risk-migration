"""Evaluation carriers def:zz_carrier_fid_<n> (harness only, not part of the package; remove at the close).

Added 2026-11-20 for the fidelity pass (update-2026-11-20-carriers.md). `eval_decl` resolves
`decl` only among the declarations of the item it evaluates, while the input terms may use
everything that item depends on (transitively). Each carrier is the identity on List Int and
depends on the units it makes visible; inputs build a List Int from a unit's result with the
kit's digest / token lambdas (diffeval/kit.py), so a Float is never printed. Nothing depends on
a carrier.
"""


def zz_carrier_fid_1(xs: list[int]) -> list[int]:
    return xs


def zz_carrier_fid_2(xs: list[int]) -> list[int]:
    return xs
