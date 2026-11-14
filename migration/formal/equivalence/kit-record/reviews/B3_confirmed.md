# B3 — confirmed findings for the fixer (both reviewers agree on 1; 2 from reviewer 1, verified by its evidence)

1. `def:proc_rank_apply_groups_precond`: the unit differs from Python for k < 0 (after `.sort("g")`
   the group minima `lo` are decreasing and numpy bisects an unsorted array; the Lean counts).
   Reproducer: reference = [1,2,3,4], x = [0.5,1,2.5,4,5,null,NaN,-inf,inf,3,2], k = -2:
   Python [-2,-1,-1,-1,-1,null,null,-2,-1,-1,-1], Lean [-2,-2,-2,-1,-1,null,null,-2,-1,-1,-2].
   Fix: add the conjunct `0 ≤ k` to the precondition (a recorded narrowing: Python does not raise
   there; say so in a comment). Do NOT change the body of `def:proc_rank_apply_groups`, except its
   comment "lo is sorted …", which must say that sortedness holds for k ≥ 0 and is what the
   precondition secures — change the comment only if the server lets you edit the unit without
   clearing dependents; otherwise leave the body untouched and report.
2. `def:proc_rank_groups_precond`: vacuously true when x has no non-null value, while Python raises
   OverflowError for a k too large for float64 (x empty or all-null, k = 10**400). Fix: state the
   bound on k independently of the elements of x (the cast of k to float64 must be finite:
   `RealLike.isFinite (Pl.ofInt k)`), in addition to the existing range condition.
Not for the fixer: the Null-dtype padding clause of `def:merge_one_to_one_precond` (prelude batch).
