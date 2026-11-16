    EXPECTED = (
        "VAR1",
        "SeriousDlqin2yrs",
        "age",
        "MonthlyIncome",
        "NumberOfDependents",
        "RevolvingUtilizationOfUnsecuredL",
        "DebtRatio",
        "NumberOfTime30-59DaysPastDueNotW",
        "NumberOfTime60-89DaysPastDueNotW",
        "NumberOfTimes90DaysLate",
        "NumberOfOpenCreditLinesAndLoans",
        "NumberRealEstateLoansOrLines",
    )
    columns_ok = 0
    bad_rows = 1
    duplicate_ids = 1
    known_incomes = 0
    if credit_raw is not None:
        # :68-79 the expected columns and no others (SAS names: any case)
        columns_ok = int(
            len(credit_raw.columns) == 12
            and sum(name.upper() in [c.upper() for c in EXPECTED] for name in credit_raw.columns) == 12
        )
        # SAS names are case-blind: the columns take the spelling the steps below use; a column
        # the check names and the table lacks is a numeric column of missing values
        by_upper = {c.upper(): c for c in EXPECTED}
        raw = credit_raw.rename({name: by_upper.get(name.upper(), name) for name in credit_raw.columns})
        raw = raw.with_columns(
            [pl.lit(None, dtype=pl.Float64).alias(c) for c in EXPECTED if c not in raw.columns]
        )
        if columns_ok == 1:
            credit_raw = raw

        # :50-61 %num: a numeric column as it is; a character column read as a number, missing
        # when the text is no number or is longer than 32 characters
        def num(v: str) -> pl.Expr:
            if raw.schema[v] != pl.String:
                return pl.col(v)
            text = pl.col(v).str.strip_chars(" ")
            return pl.when(text.str.len_chars() <= 32).then(sas_compat.input_best32(text))

        # upcase(cats(v)) not in ('', '.', 'NA'): the cell states a value
        def stated(v: str) -> pl.Expr:
            if raw.schema[v] != pl.String:
                return pl.col(v).is_not_null()
            return ~pl.col(v).fill_null("").str.strip_chars(" ").str.to_uppercase().is_in(["", ".", "NA"])

        # x >= 0 and x = int(x): a whole number, zero or more (a missing x is not)
        def count_ok(x: pl.Expr) -> pl.Expr:
            return sas_compat.ge(x, 0) & sas_compat.eq(x, pl.when(x >= 0).then(x.floor()).otherwise(x.ceil()))

        # :84-107 DATA input_check
        input_check = raw.select(
            pl.col("VAR1"),
            bad_row=sas_compat.flag(
                num("VAR1").is_null()
                | ~num("SeriousDlqin2yrs").is_in([0.0, 1.0]).fill_null(False)
                | num("age").is_null()
                | num("RevolvingUtilizationOfUnsecuredL").is_null()
                | num("DebtRatio").is_null()
                | num("NumberRealEstateLoansOrLines").is_null()
                | ~count_ok(num("NumberOfTime30-59DaysPastDueNotW"))
                | ~count_ok(num("NumberOfTime60-89DaysPastDueNotW"))
                | ~count_ok(num("NumberOfTimes90DaysLate"))
                | ~count_ok(num("NumberOfOpenCreditLinesAndLoans"))
                | (stated("MonthlyIncome") & num("MonthlyIncome").is_null())
                | (num("MonthlyIncome").is_not_null() & sas_compat.lt(num("MonthlyIncome"), 0))
                | (stated("NumberOfDependents") & ~count_ok(num("NumberOfDependents")))
            ),
            known_income=sas_compat.flag(num("MonthlyIncome").is_not_null()),
        )
        # :109-114 bad rows, repeated row ids (count(distinct) leaves a missing id out), known incomes
        bad_rows = int(input_check.get_column("bad_row").sum())
        duplicate_ids = input_check.height - input_check.get_column("VAR1").drop_nulls().n_unique()
        known_incomes = int(input_check.get_column("known_income").sum())

    # :116-123
    if credit_raw is None or columns_ok != 1 or bad_rows != 0 or duplicate_ids != 0 or known_incomes < 1:
        print(
            "ERROR: cs-training.csv does not meet the input conditions: "
            f"columns_ok={columns_ok} bad_rows={bad_rows} duplicate_ids={duplicate_ids} "
            f"known_incomes={known_incomes}."
        )
        print("ERROR: Feature engineering stopped. Nothing is exported.")
        raise ValueError("Feature engineering stopped. Nothing is exported.")
