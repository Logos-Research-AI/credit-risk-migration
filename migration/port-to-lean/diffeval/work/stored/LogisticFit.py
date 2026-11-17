@dataclass
class LogisticFit:
    """A fitted logistic model P(y = 1) on columns `names`. `names[0]` is "Intercept";
    `loglik` is the log-likelihood (-2 Log L = -2 * loglik). `converged` is False after a singular
    system, complete or quasi-complete separation, an exhausted line search or the iteration cap.
    `separation` is "complete" or "quasicomplete" on the estimates `_fit_separated` keeps."""

    names: list[str]
    beta: FloatArray
    cov: FloatArray  # inverse information matrix (NaN when it cannot be computed)
    loglik: float
    n_iter: int
    converged: bool
    separation: str | None = None
