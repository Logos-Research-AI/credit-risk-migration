"""X19: designed data for a singular information matrix in PROC LOGISTIC (singular-information.md).

cases(): name -> (variables, rows [(y, x...)], MODEL text, options). SAS's results of every case are in
x19_sas_singular_results.json (iteration lines, parameter estimates, global tests, summary, removal table,
warnings), collected from ITPRINT/DETAILS runs on SAS OnDemand; the driver that made them is
out/singular/run.py (git-ignored: data step with datalines, PROC LOGISTIC with the options below, ODS OUTPUT
of IterHistory ConvergenceStatus ParameterEstimates ModelBuildingSummary GlobalTests EffectInModel
EffectNotInModel CovB written with 32-character numbers).
"""
STEP = "selection=stepwise slentry=0.05 slstay=0.05 itprint details covb"
NONE = "itprint covb"
def noise(i, m=7): return (i * 37 + 11) % m
def flagged(n, k, m=1):
    """n rows, k events, the first m events have flag 1; z is noise"""
    return [(1, 1 if i < m else 0, noise(i)) for i in range(k)] + [(0, 0, noise(i + k)) for i in range(n - k)]
def cases():
    c = {}
    c["G1_n45_one_event_flagged"] = (["x1", "z"], flagged(45, 1), "x1 z", STEP)
    c["G2_n60_one_event_flagged"] = (["x1", "z"], flagged(60, 1), "x1 z", STEP)
    c["G3_n120_three_events_one_flagged"] = (["x1", "z"], flagged(120, 3), "x1 z", STEP)
    c["G4a_n202_k5_below"] = (["x1", "z"], flagged(202, 5), "x1 z", STEP)
    c["G4b_n283_k7_above"] = (["x1", "z"], flagged(283, 7), "x1 z", STEP)
    c["G5_n100_two_events_both_flagged"] = (["x1", "z"], flagged(100, 2, 2), "x1 z", STEP)
    # G6: a (4 events + 6 others) enters first, then the flag of one of the two a = 0 events
    rows = [(1, 1, 0, noise(i)) for i in range(4)] + [(0, 1, 0, noise(i)) for i in range(6)] + [(1, 0, 1, 3)] + [(1, 0, 0, 2)] + [(0, 0, 0, noise(i)) for i in range(248)]
    c["G6_flag_enters_second"] = (["a", "x1", "z"], rows, "a x1 z", STEP)
    c["G6n_same_not_stepwise"] = (["a", "x1", "z"], rows, "a x1", NONE)
    # G7: x2 = x1 + flag of the one event: once that row's weight is 0, x1 and x2 are collinear on the rest
    base = [(int(i == 0), i % 5) for i in range(60)]
    c["G7a_collinear_after_x1_x2"] = (["x1", "x2"], [(y, v, v + y) for y, v in base], "x1 x2", NONE)
    c["G7b_collinear_after_x2_x1"] = (["x1", "x2"], [(y, v, v + y) for y, v in base], "x2 x1", NONE)
    for tag, d in (("G8a_near_1e-5", 1e-5), ("G8b_near_1e-7", 1e-7), ("G8c_near_3e-6", 3e-6), ("G8d_near_3e-7", 3e-7)):
        c[tag] = (["x1", "x2"], [(y, v, v + y + d * ((i * 7) % 11)) for i, (y, v) in enumerate(base)], "x1 x2", NONE)
    c["G8e_near_1e-7_x2_times_1000"] = (["x1", "x2"], [(y, v, 1000 * (v + y + 1e-7 * ((i * 7) % 11))) for i, (y, v) in enumerate(base)], "x1 x2", NONE)
    for tag, d in (("G8f_near_3e-5", 3e-5), ("G8g_near_6e-5", 6e-5), ("G8h_near_1e-4", 1e-4), ("G8i_near_2e-4", 2e-4), ("G8j_near_3e-4", 3e-4), ("G8k_near_1e-3", 1e-3), ("G8l_near_1e-2", 1e-2)):
        c[tag] = (["x1", "x2"], [(y, v, v + y + d * ((i * 7) % 11)) for i, (y, v) in enumerate(base)], "x1 x2", NONE)
    for d in (1.2e-5, 1.6e-5, 2.0e-5, 2.3e-5, 2.7e-5):
        c[f"G8m_near_{d:g}"] = (["x1", "x2"], [(y, v, v + y + d * ((i * 7) % 11)) for i, (y, v) in enumerate(base)], "x1 x2", NONE)
    # mirrored: one flagged non-event among events (the weight that goes to 0 belongs to a probability near 0)
    mir = lambda rows: [(1 - r[0], *r[1:]) for r in rows]
    c["G9a_mirror_n45"] = (["x1", "z"], mir(flagged(45, 1)), "x1 z", STEP)
    c["G9b_mirror_n60"] = (["x1", "z"], mir(flagged(60, 1)), "x1 z", STEP)
    c["G9c_mirror_n120_k3"] = (["x1", "z"], mir(flagged(120, 3)), "x1 z", STEP)
    c["G9d_mirror_n202_k5_below"] = (["x1", "z"], mir(flagged(202, 5)), "x1 z", STEP)
    c["G9e_mirror_n283_k7_above"] = (["x1", "z"], mir(flagged(283, 7)), "x1 z", STEP)
    for d in (1e-5, 2.3e-5, 2.7e-5, 3e-5):  # x1 times 1000: its diagonal element is then the largest
        c[f"H1_x1_times_1000_near_{d:g}"] = (["x1", "x2"], [(y, 1000 * v, v + y + d * ((i * 7) % 11)) for i, (y, v) in enumerate(base)], "x1 x2", NONE)
    import random
    for seed in (5, 6):  # J: a regular variable enters first, then the flag of one event: a singular parameter beside another
        rng = random.Random(seed); n, k = 1000, 20
        rows = [(1, round(rng.gauss(2.0, 1.0), 3), int(i == 0), noise(i)) for i in range(k)] + [(0, round(rng.gauss(0.0, 1.0), 3), 0, noise(i)) for i in range(n - k)]
        c[f"J{seed}_regular_then_flag"] = (["a", "x1", "z"], rows, "a x1 z", STEP)
        c[f"J{seed}n_not_stepwise"] = (["a", "x1", "z"], rows, "a x1", NONE)
    return c
