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
