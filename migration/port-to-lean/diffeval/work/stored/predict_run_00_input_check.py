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
    age_name = "age"
    if test_raw is not None:
        # predict.sas:132-143 the expected columns and no others (SAS names: any case)
        # SAS names are case-blind, so a table cannot hold two names that differ only in case:
        # PROC IMPORT names the later one VARn, n its place (ev10 header_variants 10: VAR12)
        test_raw_names = test_raw.columns
        upper_names = [name.upper() for name in test_raw_names]
        sas_names = [
            f"VAR{i + 1}" if name.upper() in upper_names[:i] else name
            for i, name in enumerate(test_raw.columns)
        ]
        columns_ok = int(
            len(sas_names) == 12
            and sum(name.upper() in [c.upper() for c in EXPECTED] for name in sas_names) == 12
        )
        # SAS names are case-blind: the columns take the spelling the steps below use (the first
        # column of each name; a column of no expected name is not read below); a column
        # the check names and the table lacks is a numeric column of missing values
        by_upper = {c.upper(): c for c in EXPECTED}
        raw = test_raw.select(
            [
                pl.col(name).alias(by_upper[name.upper()])
                for i, name in enumerate(test_raw.columns)
                if name.upper() in by_upper and name.upper() not in upper_names[:i]
            ]
        )
        raw = raw.with_columns(
            [pl.lit(None, dtype=pl.Float64).alias(c) for c in EXPECTED if c not in raw.columns]
        )
        if columns_ok == 1:
            test_raw = raw
            # the test file's spelling of age, which the export below writes (predict.sas:246 a.age
            # keeps the imported name: ev11_round5_before 14 writes AGE)
            age_name = test_raw_names[upper_names.index("AGE")]

        # predict.sas:117-126 %num: a numeric column as it is; a character column read as a number,
        # missing when the text is no number or is longer than 32 characters
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

        # predict.sas:148-171 DATA input_check
        input_check = raw.select(
            pl.col("VAR1"),
            bad_row=sas_compat.flag(
                num("VAR1").is_null()
                | (stated("SeriousDlqin2yrs") & ~num("SeriousDlqin2yrs").is_in([0.0, 1.0]).fill_null(False))
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
        )
        # predict.sas:173-178 bad rows, repeated row ids (count(distinct) leaves a missing id out)
        bad_rows = int(input_check.get_column("bad_row").sum())
        duplicate_ids = input_check.height - input_check.get_column("VAR1").drop_nulls().n_unique()

    # predict.sas:180-187
    if test_raw is None or columns_ok != 1 or bad_rows != 0 or duplicate_ids != 0:
        print(
            "ERROR: cs-test.csv does not meet the input conditions: "
            f"columns_ok={columns_ok} bad_rows={bad_rows} duplicate_ids={duplicate_ids}."
        )
        print("ERROR: Test set scoring stopped. Nothing is exported.")
        raise ValueError("Test set scoring stopped. Nothing is exported.")
