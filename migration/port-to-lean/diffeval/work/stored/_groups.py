def _groups(ss: FloatArray, eps: float) -> npt.NDArray[np.int64]:
    """SAS groups the probabilities from the largest down: a value joins the current group while it is
    within `eps` of the group's largest value, else it opens a new group (finding P1; X07, X08).
    The group number is larger for a higher probability."""
    gg = np.zeros(len(ss), dtype=np.int64)
    top, g = 0.0, 0
    for k, i in enumerate(np.argsort(ss, kind="stable")[::-1].tolist()):
        v = float(ss[i])
        if k == 0 or top - v > eps:
            top, g = v, g - 1
        gg[i] = g
    return gg
