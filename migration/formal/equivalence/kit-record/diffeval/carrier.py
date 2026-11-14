"""Carrier for differential evaluation (harness only, not part of the package).

`eval_decl` resolves its `decl` only among the declarations of the item it evaluates, but the
input terms may mention anything that item depends on. The blueprint item `def:zz_carrier`
translates this identity function and depends on every unit, so any unit can be evaluated and
its result rendered exactly:  eval_decl(item_id="def:zz_carrier", decl="zz_carrier",
inputs=["(<term of type List Int built from the unit's result>)"]).  The item is removed
before the freeze.
"""


def zz_carrier(xs: list[int]) -> list[int]:
    return xs
