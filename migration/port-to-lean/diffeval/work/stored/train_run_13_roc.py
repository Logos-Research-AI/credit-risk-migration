    roc_train = sas_compat.roc_association(
        risk_scores_train.get_column("default_flag"),
        risk_scores_train.get_column("pd_logistic"),
        label="Training Set",
    )
    roc_valid = sas_compat.roc_association(
        risk_scores_validation.get_column("default_flag"),
        risk_scores_validation.get_column("pd_logistic"),
        label="Validation Set",
    )
    # train.sas:325-331: when the rows the step uses (outcome and probability present) hold no event or
    # no non-event, SAS stops the step ("All observations have the same response") and work.roc_valid
    # is not created (small-inputs.md (a); judge/runs/gen_s15, s19, s23, s29)
    roc_valid_used = risk_scores_validation.filter(
        pl.col("default_flag").is_not_null() & pl.col("pd_logistic").is_not_null()
    ).get_column("default_flag")
    roc_valid_created = bool((roc_valid_used == 1).any()) and bool((roc_valid_used != 1).any())
