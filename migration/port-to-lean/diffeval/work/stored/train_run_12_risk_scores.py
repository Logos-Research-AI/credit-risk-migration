    risk_scores_train = logit_scored_train.with_columns(
        base_score=pl.lit(600.0),
        score_range=pl.lit(250.0),
    ).with_columns(
        # Q15 (b7b1cd4): the score is not rounded
        credit_risk_score=pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))
    )
    risk_scores_train = risk_scores_train.with_columns(
        # Q18 (e1df983): graded on the probability; a missing probability is graded F
        risk_grade=pl.when(pl.col("pd_logistic").is_null())
        .then(pl.lit("F"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.10))
        .then(pl.lit("A"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.15))
        .then(pl.lit("B"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.25))
        .then(pl.lit("C"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.35))
        .then(pl.lit("D"))
        .when(sas_compat.le(pl.col("pd_logistic"), 0.50))
        .then(pl.lit("E"))
        .otherwise(pl.lit("F"))
    )
    risk_scores_train = risk_scores_train.with_columns(
        recommendation=pl.when(pl.col("risk_grade").is_in(["A", "B"]))
        .then(pl.lit("Approve"))
        .when(pl.col("risk_grade") == "C")
        .then(pl.lit("Review"))
        .otherwise(pl.lit("Decline")),
        base_rate=pl.lit(0.05),
    )
    risk_scores_train = risk_scores_train.with_columns(
        interest_rate=pl.when(pl.col("risk_grade") == "A")
        .then(pl.col("base_rate"))
        .when(pl.col("risk_grade") == "B")
        .then(pl.col("base_rate") + 0.02)
        .when(pl.col("risk_grade") == "C")
        .then(pl.col("base_rate") + 0.04)
        .when(pl.col("risk_grade") == "D")
        .then(pl.col("base_rate") + 0.07)
        .when(pl.col("risk_grade") == "E")
        .then(pl.col("base_rate") + 0.10)
        .otherwise(pl.col("base_rate") + 0.15)
    )  # format interest_rate percent8.2 -> applied at export

    # train.sas:271-300 data work.risk_scores_validation
    risk_scores_validation = logit_scored_valid.with_columns(
        base_score=pl.lit(600.0),
        score_range=pl.lit(250.0),
    ).with_columns(
        # Q15 (b7b1cd4): the score is not rounded
        credit_risk_score=pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))
    )
    risk_scores_validation = risk_scores_validation.with_columns(
        # Q18 (e1df983): graded on the probability; a missing probability is graded F
        risk_grade=pl.when(pl.col("pd_logistic").is_null())
        .then(pl.lit("F"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.10))
        .then(pl.lit("A"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.15))
        .then(pl.lit("B"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.25))
        .then(pl.lit("C"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.35))
        .then(pl.lit("D"))
        .when(sas_compat.le(pl.col("pd_logistic"), 0.50))
        .then(pl.lit("E"))
        .otherwise(pl.lit("F"))
    )
    risk_scores_validation = risk_scores_validation.with_columns(
        recommendation=pl.when(pl.col("risk_grade").is_in(["A", "B"]))
        .then(pl.lit("Approve"))
        .when(pl.col("risk_grade") == "C")
        .then(pl.lit("Review"))
        .otherwise(pl.lit("Decline")),
        base_rate=pl.lit(0.05),
    )
    risk_scores_validation = risk_scores_validation.with_columns(
        interest_rate=pl.when(pl.col("risk_grade") == "A")
        .then(pl.col("base_rate"))
        .when(pl.col("risk_grade") == "B")
        .then(pl.col("base_rate") + 0.02)
        .when(pl.col("risk_grade") == "C")
        .then(pl.col("base_rate") + 0.04)
        .when(pl.col("risk_grade") == "D")
        .then(pl.col("base_rate") + 0.07)
        .when(pl.col("risk_grade") == "E")
        .then(pl.col("base_rate") + 0.10)
        .otherwise(pl.col("base_rate") + 0.15)
    )  # format interest_rate percent8.2 -> applied at export
