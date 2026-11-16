    train_income_medians = sas_compat.proc_import_csv(income_medians)
    # SAS names are case-blind: the three columns the join reads take the spelling it uses
    medians_upper = [name.upper() for name in train_income_medians.columns]
    train_income_medians = train_income_medians.rename(
        {
            name: name.lower()
            for i, name in enumerate(train_income_medians.columns)
            if name.upper() in ("AGE_GROUP", "MEDIAN_INCOME", "OVERALL_MEDIAN_INCOME")
            and name.upper() not in medians_upper[:i]
            and (name.lower() == name or name.lower() not in train_income_medians.columns)
        }
    )
