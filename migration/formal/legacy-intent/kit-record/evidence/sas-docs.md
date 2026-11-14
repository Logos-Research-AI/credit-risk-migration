# SAS 9.4 / SAS/STAT 15.x documentary evidence (D1..D15)

Scope: behaviour of SAS language elements and procedures, quoted from SAS documentation.
Retrieved 2026-11-10.

Conventions

- Base URL forms. Base SAS 9.4 docsets: `https://documentation.sas.com/doc/en/<docset>/9.4/<page>`.
  SAS/STAT: `https://documentation.sas.com/doc/en/statug/15.2/<page>`. The text was read through the
  site's content API (`https://documentation.sas.com/api/docsets/<docset>/<version>/content/<page>?locale=en`),
  which serves the same page body.
- "Quote" blocks are verbatim, except that (a) line breaks are removed, and (b) formulas, which the
  site renders as images/MathML, are transcribed into plain notation; every transcribed formula is
  marked `[formula]`.
- Status tags: **DOCUMENTED** (the docs state the rule), **PARTLY DOCUMENTED** (stated in general
  terms, or only by example), **NOT DOCUMENTED** (docs silent; do not rely on it without a run).
- Secondary evidence (SAS usage notes, blogs, community answers) is labelled SECONDARY. Where a
  secondary page could not be opened and only a search-engine summary was seen, it is labelled
  SECONDARY, UNVERIFIED and is not quoted.
- Version caveat: the Base SAS pages are the current "9.4" docset (pages carry "Last updated"
  dates from 2023 to 2026). The SAS/STAT pages are 15.2 ("Last updated: October 28, 2020"); 15.1 and
  14.1 were consulted where the text changed between releases (see D12).

---

## D1. ROUND function (one argument / rounding unit 1), ROUNDE, ROUNDZ

URLs

- ROUND: https://documentation.sas.com/doc/en/lefunctionsref/9.4/p0tj6cmga7p8qln1ejh6ebevm0c9.htm
- ROUNDZ: https://documentation.sas.com/doc/en/lefunctionsref/9.4/p1u0w0omad7fyxn1unu83odr6vy2.htm
- ROUNDE: https://documentation.sas.com/doc/en/lefunctionsref/9.4/n02h2rvq30k869n164ccmcwvhqyk.htm
- Function syntax (invalid arguments): https://documentation.sas.com/doc/en/lefunctionsref/9.4/p1u7ioka3nk1azn1acbxzqz4n3ii.htm

Quotes (ROUND page)

> "Rounds the first argument to the nearest multiple of the second argument, or to the nearest integer when the second argument is omitted."

> "The ROUND function rounds the first argument to a value that is very close to a multiple of the second argument. The result might not be an exact multiple of the second argument."

> "When the value to be rounded is approximately halfway between two multiples of the rounding unit, the ROUND function rounds up the absolute value and restores the original sign."

> "The approximation is relative to the size of the value to be rounded, and is computed in a manner that is shown in the following DATA step. This DATA step code will not always produce results exactly equivalent to the ROUND function."

```sas
data testfile;
   do i=1 to 17;
      value=0.5 - 10**(-i);
      epsilon=min(1e-6, value * 1e-12);
      temp=value + .5 + epsilon;
      fraction=modz(temp, 1);
      round=temp - fraction;
      output;
   end;
run;
```

> "In general, ROUND(argument, rounding-unit) produces the result that you expect from decimal arithmetic if the result has no more than nine significant digits and any of the following conditions are true: The rounding unit is an integer. The rounding unit is a power of 10 greater than or equal to 1e-15. [...] The result that you expect from decimal arithmetic has no more than four decimal places."

Quotes (Comparisons section, identical on the ROUND and ROUNDZ pages)

> "ROUND returns the multiple with the larger absolute value when the first argument is approximately halfway between the two nearest multiples of the second argument."

> "ROUNDE returns an even multiple when the first argument is approximately halfway between the two nearest multiples of the second argument."

> "ROUNDZ returns an even multiple when the first argument is exactly halfway between the two nearest multiples of the second argument."

> "When the rounding unit is less than one and not the reciprocal of an integer, the result that is returned by ROUNDZ might not agree exactly with the result from decimal arithmetic. ROUND and ROUNDE perform extra computations, called fuzzing, to try to make the result agree with decimal arithmetic in the most common situations. ROUNDZ does not fuzz the result."

Quote (function syntax page, general rule for all functions)

> "If the value of an argument is invalid (for example, missing or outside the prescribed range), SAS writes a note to the log indicating that the argument is invalid, sets _ERROR_ to 1, and sets the result to a missing value."

Rule

- `ROUND(x)` = `ROUND(x, 1)`: nearest integer; a value "approximately halfway" is rounded away from
  zero (round up |x|, restore the sign).
- The documented model of "approximately halfway" for unit 1 and x >= 0 is:
  `eps = min(1e-6, x * 1e-12); t = x + 0.5 + eps; result = t - modz(t, 1)` (i.e. truncate `t`); for
  x < 0 apply it to |x| and negate. So a value within a relative 1e-12 (capped at an absolute 1e-6)
  below a half is treated as the half and rounds away from zero.
- ROUNDE: same "approximately halfway" test, tie goes to the even multiple. ROUNDZ: no fuzz; only an
  exact half is a tie, and it goes to the even multiple.

NOT DOCUMENTED / caveats

- The exact production algorithm is NOT DOCUMENTED: SAS says the DATA step above "will not always
  produce results exactly equivalent to the ROUND function". Treat the epsilon formula as the
  documented approximation, not a bit-exact specification.
- The docs give the epsilon code only for a positive `value`; the sign handling for negatives is
  given only in prose ("rounds up the absolute value and restores the original sign").
- ROUND of a missing argument: the ROUND page is silent. Only the general function rule above
  applies (result missing). Whether a log note is written for `ROUND(.)` is NOT DOCUMENTED on the
  ROUND page.

---

## D2. Numeric missing values, invalid operations, Boolean values

URLs

- Order of Missing Values: https://documentation.sas.com/doc/en/lrcon/9.4/p0tmoipp0ci6wkn0z27ev47sv0ov.htm
- When Missing Values Are Generated by SAS: https://documentation.sas.com/doc/en/lrcon/9.4/p17j9efnrdlz0gn1d19ete4ik8sb.htm
- Working with Missing Values: https://documentation.sas.com/doc/en/lrcon/9.4/p175x77t7k6kggn1io94yedqagl3.htm
- SAS Operators in Expressions: https://documentation.sas.com/doc/en/lrcon/9.4/p00iah2thp63bmn1lt20esag14lh.htm
- LOG: https://documentation.sas.com/doc/en/lefunctionsref/9.4/p0urbseuxrkrlyn1tr04y30nt25s.htm
- EXP: https://documentation.sas.com/doc/en/lefunctionsref/9.4/n0ocutx9jgosdln17xg1z75jmkbv.htm
- Function syntax: https://documentation.sas.com/doc/en/lefunctionsref/9.4/p1u7ioka3nk1azn1acbxzqz4n3ii.htm

Quotes

> "Within SAS, a missing value for a numeric variable is smaller than all numbers. If you sort your data set by a numeric variable, observations with missing values for that variable appear first in the sorted data set."

Sort-order table (same page): smallest `._`, then `.`, then `.A`-`.Z`, then negative numbers, zero, positive numbers.

> "A missing numeric value is smaller than any other numeric value, and missing numeric values have their own sort order." (Operators, Numeric Comparisons)

> "Group V operators are comparison operators. The result of a comparison operation is 1 if the comparison is true and 0 if it is false. Missing values are the lowest in any comparison operation." (Operators, footnote 7)

> "If the comparison is true, the result is 1. If the comparison is false, the result is 0." (Operators, Comparison Operators)

> "If a missing value is an operand for an arithmetic operator, the result is a missing value." (Operators, Arithmetic Operators)

> "If you use a missing value in an arithmetic calculation, SAS sets the result of that calculation to missing. Then, if you use that result in another calculation, the next result is also missing. This action is called propagation of missing values." [...] "However, processing continues."

> "SAS prints a note in the log and assigns a missing value to the result if you try to perform an invalid operation, such as the following: dividing by zero / taking the logarithm of zero / using an expression to produce a number too large to be represented as a floating-point number (known as overflow)"

> "The result of any numeric missing value in a SAS expression is a period. Thus, both special missing values and ordinary numeric missing values propagate as a period."

> LOG: "Range: must be positive."

> EXP: "The result is limited by the maximum value of a floating-point value on the computer."

> "If the value of an argument is invalid (for example, missing or outside the prescribed range), SAS writes a note to the log indicating that the argument is invalid, sets _ERROR_ to 1, and sets the result to a missing value." (function syntax)

> "In SAS, any numeric value other than 0 or missing is true, and a value of 0 or missing is false. Therefore, a numeric variable or expression can stand alone in a condition. If its value is a number other than 0 or missing, the condition is true. If its value is 0 or missing, the condition is false." (Operators, Boolean Numeric Expressions)

> "The result of NOT in front of a quantity whose value is missing is also 1 (true)."

> "If both of the quantities linked by AND are 1 (true), then the result of the AND operation is 1. Otherwise, the result is 0." / "If either of the quantities linked by an OR is 1 (true), then the result of the OR operation is 1 (true). Otherwise, the OR operation produces a 0."

> "Note: Missing values have a value of false when you use them with logical operators such as AND or OR." (Working with Missing Values)

Rule

- Ordering: `.` < every number (and `._` < `.` < `.A` < ... < `.Z` < numbers). So `. < 0`, `. <= x`
  are true (1); `. = .` is true. There is no three-valued logic: a comparison always yields 1 or 0.
- Arithmetic (`+ - * / **`) with a missing operand yields `.` (ordinary missing), with a log note.
- Division by zero, LOG(0), and overflow yield `.` with a log note, and the step continues.
- LOG of a negative argument and EXP overflow: result `.` by the general "outside the prescribed
  range" / overflow rules.
- A numeric expression used as a condition is true iff it is neither 0 nor missing.
  AND/OR/NOT return 1 or 0; `NOT .` is 1.

NOT DOCUMENTED / caveats

- LOG of a negative number is not listed by name among the "invalid operations"; it is covered only
  by the LOG "Range: must be positive" plus the general invalid-argument rule. PARTLY DOCUMENTED.
- EXP overflow is covered only by "limited by the maximum value of a floating-point value" plus the
  general overflow rule; the exact threshold argument is NOT DOCUMENTED.
- Whether `_ERROR_` is set to 1 on division by zero is NOT stated on these pages (it is stated only
  for invalid function arguments). SECONDARY: the SAS blog "Dividing by zero with SAS - myths and
  realities" (L. Batkhan, then SAS consultant),
  https://blogs.sas.com/content/sgf/2019/05/08/dividing-by-zero-with-sas-myths-and-realities, says
  SAS "sets the result of division by zero to a missing value" and writes "NOTE: Division by zero
  detected at line XXX column XX.", and shows a log dump with `_ERROR_=1`.

---

## D3. SUM/MIN/MAX functions with missing; sum statement; RETAIN

URLs

- SUM: https://documentation.sas.com/doc/en/lefunctionsref/9.4/n0zxive1z1ctqin12w06c85jfigd.htm
- MIN: https://documentation.sas.com/doc/en/lefunctionsref/9.4/p1525p9momafkwn15gm707mtsbat.htm
- MAX: https://documentation.sas.com/doc/en/lefunctionsref/9.4/n00bjr4jof59pwn1bfzk9f5i0ujr.htm
- Sum statement: https://documentation.sas.com/doc/en/lestmtsref/9.4/n1dfiqj146yi2cn1maeju9wo7ijs.htm
- RETAIN: https://documentation.sas.com/doc/en/lestmtsref/9.4/p0t2ac0tfzcgbjn112mu96hkgg9o.htm

Quotes

> SUM: "Returns the sum of the nonmissing arguments." [...] "If all the arguments have missing values, then one of these actions occurs: If you use only one argument, the value of that argument is returned. If you use two or more arguments, a standard missing value (.) is returned. Otherwise, the result is the sum of the nonmissing values."

> MIN: "The MIN function returns a missing value (.) only if all arguments are missing."

> MAX: "The MAX function returns a missing value (.) only if all arguments are missing."

> (MIN page, operator contrast) "The MIN operator (><) returns a missing value if either operand is missing."

> Sum statement, syntax `variable+expression;`: "The variable is automatically set to 0 before SAS reads the first observation. The variable's value is retained from one iteration to the next, as if it had appeared in a RETAIN statement." / "To initialize a sum variable to a value other than 0, include it in a RETAIN statement with an initial value." / "The expression is evaluated and the result added to the accumulator variable." / "SAS treats an expression that produces a missing value as zero."

> "The sum statement is equivalent to using the SUM function and the RETAIN statement, as shown here: `retain variable 0; variable=sum(variable,expression);`"

> RETAIN, initial-value: "If you omit initial-value, the initial value is missing. Initial-value is assigned to all the elements that precede it in the list."

> RETAIN: "If there are more variables than initial values, the remaining variables are assigned an initial value of missing and SAS issues a warning message."

> RETAIN: "Without a RETAIN statement, SAS automatically sets variables that are assigned values by an INPUT or assignment statement to missing before each iteration of the DATA step."

> RETAIN: "You can also use RETAIN to assign an initial value other than the default value of 0 to a variable whose value is assigned by a sum statement."

> RETAIN: "If a variable name is specified only in the RETAIN statement and you do not specify an initial value, the variable is not written to the data set, and a note stating that the variable is uninitialized is written to the SAS log."

> RETAIN (redundant to name): "variables that are read with a SET, MERGE, MODIFY or UPDATE statement" / "a variable whose value is assigned in a sum statement"

Rule

- `SUM(a, b, ...)` ignores missing arguments; with two or more arguments all missing, the result is
  `.`. `MIN`/`MAX` functions ignore missing arguments and return `.` only if all are missing.
- `x + expr;` is `retain x 0; x = sum(x, expr);`: x starts at 0, is retained, and a missing `expr`
  adds nothing.
- `retain a b;` (no initial value): `a` and `b` start as missing and are not reset at the top of each
  iteration. If the variable is also the target of a sum statement its start value is 0 unless
  RETAIN gives another value.

NOT DOCUMENTED / caveats

- The equivalence `variable=sum(variable,expression)` implies that if the accumulator itself is
  missing (e.g. set to missing by an assignment) and `expr` is nonmissing, the result is `expr`; and
  if both are missing the result is `.`. This follows from the quoted equivalence; it is not spelled
  out separately.

---

## D4. DATA step character variables: length, padding, comparison, IN

URLs

- Ways to Create Variables: https://documentation.sas.com/doc/en/lrcon/9.4/n0bbin3txgxlown1v2v5d8qbc9vq.htm
- SAS Operators in Expressions: https://documentation.sas.com/doc/en/lrcon/9.4/p00iah2thp63bmn1lt20esag14lh.htm
- Order of Missing Values: https://documentation.sas.com/doc/en/lrcon/9.4/p0tmoipp0ci6wkn0z27ev47sv0ov.htm

Quotes

> "In SAS, you do not have to declare a variable before assigning a value to it. The variable is automatically declared the first time you specify it in an assignment statement. SAS assigns the variable's type and length based on its first occurrence in the DATA step. SAS assigns the variable the same type and length as the expression on the right side of the assignment operator."

Table row (same page): Expression "Character literal", example `data test; x='ABC'; x='ABCDE'; run;`, resulting type "Character", resulting length "3 bytes", explanation "Length of first literal encountered".

> "When SAS assigns a value to a character variable, it pads the value with blanks or truncates the value on the right side to make it match the length of the target variable."

> "You cannot change the length of a character variable with a subsequent LENGTH or ATTRIB statement within the same DATA step. You should use the longest possible value in the first statement that references the character variable. You can change the length of a numeric variable by using a subsequent LENGTH statement."

> "Two-character values of unequal length are compared as if blanks were attached to the end of the shorter value before the comparison is made. A blank, or missing character value, is smaller than any other printable character value." (Operators, Character Comparisons)

> "Since trailing blanks are ignored in a comparison, 'fox ' is equivalent to 'fox'. However, because blanks at the beginning and in the middle of a character value are significant to SAS, ' fox' is not equivalent to 'fox'."

> "You can perform comparisons on character operands, but the comparison always yields a numeric result (1 or 0). Character operands are compared character by character from left to right. Character order depends on the collating sequence, usually ASCII or EBCDIC, used by your computer."

> "You can use the IN operator with character strings to determine whether a variable's value is among a list of character values. The following statements produce the same results: `if state in ('NY','NJ','PA') then region+1;` `if state in ('NY' 'NJ' 'PA') then region+1;` `if state='NY' or state='NJ' or state='PA' then region+1;`"

Rule

- A character variable first created by assignment gets the length of the right-hand side of the
  first assignment in program-text order ("first occurrence in the DATA step"): `risk_grade = 'A'`
  gives length 1; `recommendation = 'Approve'` gives length 7, so later `'Decline'` (7) is stored
  whole and `'Review'` (6) is stored blank-padded to 7. A longer later value would be truncated on
  the right.
- Character comparison (`=`, `<`, ... and `IN`) pads the shorter operand with blanks, so trailing
  blanks never affect equality; `x in ('a','b')` is `x='a' or x='b'`. Result is 1 or 0.
- A blank (missing) character value compares below any printable character.

NOT DOCUMENTED / caveats

- "First occurrence" is positional in the compiled step, not the first statement executed; the docs
  say "first occurrence in the DATA step" and the `x='ABC'; x='ABCDE';` example, which is consistent
  with compile-time determination, but the phrase "compile time" is not on this page.

---

## D5. PROC SORT: stability, missing placement, default order

URLs

- PROC SORT statement: https://documentation.sas.com/doc/en/proc/9.4/p02bhn81rn4u64n1b6l00ftdnxge.htm
- BY statement: https://documentation.sas.com/doc/en/proc/9.4/p00h649h18r3ywn1g3kdu8lppg4s.htm
- Concepts: https://documentation.sas.com/doc/en/proc/9.4/n1c1pczk6ogkbsn168zmf4k1izrh.htm

Quotes

> "EQUALS | NOEQUALS specifies the order of the observations in the output data set. For observations with identical BY-variable values, EQUALS maintains the relative order of the observations within the input data set in the output data set. NOEQUALS does not necessarily preserve this order in the output data set." "Default: EQUALS"

> "The EQUALS | NOEQUALS procedure option overrides the default sort stability behavior that is established with the SORTEQUALS | NOSORTEQUALS system option."

> "While processing, PROC SORT maintains the order of the observations because it uses a stable sorting algorithm. The stable sorting algorithm is used because the EQUALS option is set by default."

> BY statement: "PROC SORT first arranges the data set by the values in ascending order, by default, of the first BY variable. PROC SORT then arranges any observations that have the same value of the first BY variable by the values of the second BY variable in ascending order."

> "DESCENDING reverses the sort order for the variable that immediately follows in the statement so that observations are sorted from the largest value to the smallest value."

> Concepts: "For numeric variables, the following is the smallest-to-largest comparison sequence: SAS missing values (shown as a period or special missing value) / negative numeric values / zero / positive numeric values"

> Concepts (character): "The blank is the smallest character that you can display."

Rule

- PROC SORT is stable by default (EQUALS): rows with equal BY values keep their input order.
- Default direction is ascending per BY variable; DESCENDING applies only to the variable that
  follows it.
- Numeric missing sorts first in ascending order (hence last under DESCENDING); blank character
  values sort before printable characters.

NOT DOCUMENTED / caveats

- The default can be changed by the NOSORTEQUALS system option; the rule above assumes the shipped
  default (SORTEQUALS).

---

## D6. PROC RANK with GROUPS=n

URLs

- PROC RANK statement: https://documentation.sas.com/doc/en/proc/9.4/p16s2o8e4bnqrin1phywxdaxqba7.htm
- Concepts (Treatment of Tied Values): https://documentation.sas.com/doc/en/proc/9.4/n0y7jshlj1odi6n1atnqzerl3uw5.htm
- Results: https://documentation.sas.com/doc/en/proc/9.4/n1j38rdcpvze7sn15rdca2h7jqq8.htm

Quotes

> "GROUPS=number-of-groups assigns group values ranging from 0 to number-of-groups minus 1. Common specifications are GROUPS=100 for percentiles, GROUPS=10 for deciles, and GROUPS=4 for quartiles. For example, GROUPS=4 partitions the original values into four groups. The smallest values receive, by default, a quartile value of 0 and the largest values receiving a quartile value of 3."

> "The formula for calculating group values is as follows: [formula] FLOOR(rank*k/(n+1)) FLOOR is the FLOOR function, rank is the value's order rank, k is the value of GROUPS=, and n is the number of observations having nonmissing values of the ranking variable for TIES=LOW, TIES=MEAN, and TIES=HIGH. For TIES=DENSE, n is the number of observations that have unique nonmissing values."

(The formula image's alt text reads "floor ( rank times k slash ( n plus 1 ) )".)

> "If the number of observations is evenly divisible by the number of groups, each group has the same number of observations, provided there are no tied values at the boundaries of the groups. Grouping observations by a variable that has many tied values can result in unbalanced groups because PROC RANK always assigns observations with the same value to the same group." "Tip: Use DESCENDING to reverse the order of the group values."

> TIES=: "HIGH assigns the largest of the corresponding ranks [...] LOW assigns the smallest of the corresponding ranks [...] MEAN assigns the mean of the corresponding rank [...] DENSE computes scores and ranks by treating tied values as a single-order statistic." "Default: MEAN (unless the FRACTION option or PERCENT option is in effect)."

> "DESCENDING reverses the direction of the ranks. With DESCENDING, the largest value receives a rank of 1, the next largest value receives a rank of 2, and so on. Otherwise, values are ranked from smallest to largest."

> Concepts: "For ranking and scoring methods, when TIES=LOW, TIES=HIGH, or TIES=MEAN, tied values are initially treated as if they are distinguishable. These methods all begin by sorting the values of the analysis variable within a BY group, and then assigning to each nonmissing value an ordinal number that indicates its position in the sequence. Subsequently, for non-scoring methods, PROC RANK resolves tied values by selecting the minimum with TIES=LOW, selecting the maximum with TIES=HIGH, or calculating the average of the ordinals in a group of tied values with TIES=MEAN. PROC RANK then obtains the rank from this value through one or more further transformations such as scaling, translation, and truncation." "Non-scoring methods include ordinal ranking, the default, and those methods that are requested by the FRACTION, NPLUS1, GROUPS=, and PERCENT options."

> Results: "Missing values are not ranked and are left missing when ranks or rank scores replace the original values in the output data set."

> Results: "The output data set contains all the variables from the input data set plus the variables named in the RANKS statement. If you omit the RANKS statement, the rank values replace the original variable values in the output data set."

Rule

- group = FLOOR(rank * k / (n + 1)), where k = GROUPS= value, n = number of observations with a
  nonmissing value of the ranked variable (within the BY group, if any), and rank is the
  tie-resolved rank.
- With GROUPS= and no TIES= option, TIES=MEAN applies: tied values get the average of their
  ordinals (possibly a half-integer), and the FLOOR formula is applied to that average, so all tied
  values land in the same group.
- DESCENDING ranks the largest value 1, so the largest values get group 0.
- A missing value of the ranked variable gets a missing rank/group and is not counted in n.

NOT DOCUMENTED / caveats

- Output row order: NOT DOCUMENTED. The docs say the output contains "all the variables from the
  input data set plus" the rank variables and every documented example prints rows in input order,
  but no sentence guarantees that observation order is preserved.
- The docs do not state the floating-point evaluation order of `rank*k/(n+1)` (multiply then divide
  as written is the natural reading). NOT DOCUMENTED at bit level.

---

## D7. PROC FREQ `TABLES a*b / OUT=ds` (NOPRINT)

URLs

- TABLES statement: https://documentation.sas.com/doc/en/procstat/9.4/procstat_freq_syntax08.htm
- PROC FREQ statement: https://documentation.sas.com/doc/en/procstat/9.4/procstat_freq_syntax01.htm
- Missing Values: https://documentation.sas.com/doc/en/procstat/9.4/procstat_freq_details03.htm
- Output Data Sets: https://documentation.sas.com/doc/en/procstat/9.4/procstat_freq_details112.htm

Quotes

> "OUT=SAS-data-set names an output data set that contains frequency or crosstabulation table counts and percentages. If more than one table request appears in the TABLES statement, the contents of the OUT= data set correspond to the last table request in the TABLES statement. The OUT= data set variable COUNT contains the frequencies and the variable PERCENT contains the percentages."

> Output Data Sets: "The OUT= option in the TABLES statement creates an output data set that contains one observation for each combination of variable values (or table cell) in the last table request. By default, each observation contains the frequency and percentage for the table cell. When the input data set contains missing values, the output data set also contains an observation with the frequency of missing values. The output data set includes the following variables: BY variables / table request variables, such as A, B, C, and D in the table request A*B*C*D / COUNT, which contains the table cell frequency / PERCENT, which contains the table cell percentage"

> Output Data Sets: "If A has two levels (1 and 2), B has three levels (1,2, and 3), and no table cell count is 0 or missing, the output data set D includes six observations, one for each combination of A and B levels. The first observation corresponds to A=1 and B=1; the second observation corresponds to A=1 and B=2; and so on. The data set includes the variables COUNT and PERCENT. The value of COUNT is the number of observations with the given combination of A and B levels. The value of PERCENT is the percentage of the total number of observations with that A and B combination."

> SPARSE: "SPARSE reports all possible combinations of variable values in two-way and multiway tables, even if a combination does not occur in the data. This option applies only to crosstabulation tables that are displayed in LIST format and to OUT= output data sets. [...] When you specify the SPARSE option together with the OUT= option, the OUT= output data set includes empty (zero-frequency) crosstabulation table cells. By default, the OUT= output data set does not include zero-frequency table cells."

> PROC FREQ statement, ORDER=: "By default, ORDER=INTERNAL." (INTERNAL = "Unformatted value") "The ORDER= option does not apply to missing values, which are always ordered first."

> Missing Values: "If an observation has a missing value for a variable in a TABLES request, by default PROC FREQ does not include that observation in the frequency or crosstabulation table. Also by default, PROC FREQ does not include observations with missing values in the computation of percentages and statistics." "PROC FREQ also reports the number of missing values in output data sets. The TABLES statement OUT= data set includes an observation that contains the missing value frequency."

> Missing Values: "MISSPRINT displays missing value frequencies in frequency or crosstabulation tables but does not include them in computations of percentages or statistics. MISSING treats missing values as a valid nonmissing level for all TABLES variables."

> PROC FREQ statement: NOPRINT "Suppresses all displayed output".

Rule

- OUT= has one row per observed (a, b) combination (zero-count cells only with SPARSE), with the
  table variables, COUNT (cell frequency) and PERCENT (100 * COUNT / total frequency of the table,
  i.e. of nonmissing observations by default).
- Row order: levels of a (major) then b (minor), each in ascending internal (unformatted) value
  (ORDER=INTERNAL default); missing levels first.
- By default (no MISSING/MISSPRINT), observations with a missing a or b are excluded from the
  percentage base, but OUT= still contains row(s) carrying the frequency of the missing level(s).

NOT DOCUMENTED / caveats

- That PERCENT is a missing value (`.`) on those missing-level rows of OUT= is PARTLY DOCUMENTED:
  the docs say such rows exist and that missing values are excluded "in the computation of
  percentages"; the MISSPRINT display example shows Percent "." for the missing level. No sentence
  states PERCENT=. in OUT= explicitly.
- Whether, for a two-way table, OUT= has one row per distinct (a, b) combination involving a missing
  value or a single row is described only as "an observation with the frequency of missing values";
  the per-combination layout is NOT DOCUMENTED explicitly.
- The exact arithmetic used for PERCENT (100*COUNT/N versus COUNT/N*100) is NOT DOCUMENTED.

---

## D8. PROC SQL

URLs

- summary-function: https://documentation.sas.com/doc/en/sqlproc/9.4/n123fsko39j44pn16zlt087e1m2h.htm
- Summarizing Data: https://documentation.sas.com/doc/en/sqlproc/9.4/p0xwc73ekemkapn1byhceqrwrisb.htm
- Grouping Data: https://documentation.sas.com/doc/en/sqlproc/9.4/n0tf6s2l1rfv5ln1o04ojc4rotu1.htm
- GROUP BY clause: https://documentation.sas.com/doc/en/sqlproc/9.4/n16ee3ciphxlean1wug0v9i913jw.htm
- ORDER BY clause: https://documentation.sas.com/doc/en/sqlproc/9.4/n0gwogdxntzooun1azrzwrwrqvzq.htm
- Sorting Data: https://documentation.sas.com/doc/en/sqlproc/9.4/p1jr2es0aus2qtn11peo724tt8f4.htm
- Joins (user guide): https://documentation.sas.com/doc/en/sqlproc/9.4/p0o4a5ac71mcchn1kc1zhxdnm139.htm
- joined-table: https://documentation.sas.com/doc/en/sqlproc/9.4/p1bk7i6jqseje7n1lifcip8kzhpp.htm
- sql-expression: https://documentation.sas.com/doc/en/sqlproc/9.4/p020urejdmvi7vn1t9avbvazqapu.htm
- CASE: https://documentation.sas.com/doc/en/sqlproc/9.4/n0a85s0ijz65irn1h3jtariooea5.htm
- CALCULATED: https://documentation.sas.com/doc/en/sqlproc/9.4/n0jxri3yohqdwbn1slekmsc882gz.htm
- INTO clause: https://documentation.sas.com/doc/en/sqlproc/9.4/n1tupenuhmu1j0n19d3curl9igt4.htm
- Using PROC SQL with the SAS Macro Facility: https://documentation.sas.com/doc/en/sqlproc/9.4/p0xlnvl46zgqffn17piej7tewe7p.htm
- PROC SQL and the ANSI Standard: https://documentation.sas.com/doc/en/sqlproc/9.4/p0corah7t43hy7n1r7efplde5c8z.htm
- MEDIAN function: https://documentation.sas.com/doc/en/lefunctionsref/9.4/p10gg32gykwv40n1mfbqkbhlbr2q.htm
- Keywords and Formulas (Base Procedures Guide): https://documentation.sas.com/doc/en/proc/9.4/p0v0y1on1hbxukn0zqgsp5ky8hc0.htm

### (a) MEDIAN: summary function vs row function; missing; even counts

> summary-function list: "MEDIAN the 50th percentile; a value that exceeds half of the sample data values and is exceeded by half of the sample data values" [...] "For a description and the formulas used for these statistics, see SAS Elementary Statistics Procedures in Base SAS Procedures Guide."

> "The number of arguments that is specified in a summary function affects how the calculation is performed. If you specify a single argument, then the values in the column are calculated. If you specify multiple arguments, then the arguments or columns that are listed are calculated for each row."

> "Note: When more than one argument is used within an SQL aggregate function, the function is no longer considered to be an SQL aggregate or summary function. If there is a like-named Base SAS function, then PROC SQL executes the Base SAS function, and the results that are returned are based on the values for the current row."

> MEDIAN function (Base): "The MEDIAN function returns the median of the nonmissing values. If all arguments have missing values, the result is a missing value. Note: The formula that is used in the MEDIAN function is the same as the formula that is used in PROC UNIVARIATE"

> Keywords and Formulas: "MEDIAN is the middle value." Percentile definitions: "Let n be the number of nonmissing values for a variable, and let x_1, x_2, ..., x_n represent the ordered values of the variable [...] For the tth percentile between 0 and 1, let p = t/100. Then specify j as the integer part of np and g as the fractional part of np [...]" Table row QNTLDEF=5, "empirical distribution function with averaging": [formula] y = (x_j + x_{j+1})/2 if g = 0; y = x_{j+1} if g > 0.

Rule: `MEDIAN(col)` with one argument in PROC SQL (SAS 9.4) is an aggregate over the group's
nonmissing values. With the default percentile definition 5 and p = 0.5: odd n gives the middle
value; even n gives the mean of the two middle values. `MEDIAN(a, b, ...)` with several arguments is
the Base row function.

NOT DOCUMENTED: the summary-function page does not itself say which percentile definition the SQL
MEDIAN aggregate uses; it only points to the elementary-statistics formulas, where definition 5 is
the one "with averaging" (the default QNTLDEF=/PCTLDEF= of the procedures, a fact not quoted
above). The choice of definition matters only for an even number of nonmissing values. PARTLY
DOCUMENTED. Also not stated: the result for a group with no nonmissing values (missing, by analogy
with the Base MEDIAN function).

### (b) SUM/MEAN/AVG/MIN/MAX/COUNT: missing values and empty input

> "AVG | MEAN arithmetic mean or average of values / COUNT | FREQ | N number of nonmissing values / MAX largest value / MIN smallest value / NMISS number of missing values / SUM sum of values"

> "The COUNT function counts rows. COUNT(*) returns the total number of rows in a group or in a table. If you use a column name as an argument to COUNT, then the result is the total number of rows in a group or in a table that have a nonmissing value for that column."

> "If the SELECT clause of a table expression contains one or more summary functions and that table expression resolves to no rows, then the summary function results are missing values. The following are exceptions that return zeros: COUNT(*) / COUNT(<DISTINCT> sql-expression) / NMISS(<DISTINCT> sql-expression)"

> Summarizing Data: "When you use an aggregate function with data that contains missing values, the results might not provide the information that you expect because many aggregate functions ignore missing values." "The AVG function returns the average of only the nonmissing values."

> Keywords and Formulas: "summation is over observations that contain nonmissing values of the analyzed variable"

Rule: SUM/AVG/MEAN/MIN/MAX/MEDIAN are computed over the nonmissing values of the group; COUNT(col)
counts nonmissing, COUNT(*) counts rows. On an input that resolves to no rows the statistics are
missing and COUNT(*)/COUNT(x)/NMISS(x) are 0.

NOT DOCUMENTED: the result of SUM/AVG/MIN/MAX for a nonempty group whose values are all missing is
not stated in so many words (it is missing in practice; follows from "summation is over
observations that contain nonmissing values" with n = 0). PARTLY DOCUMENTED.

### (c) Boolean expressions as 0/1

> ANSI appendix, Orthogonal Expressions: "PROC SQL enables the combination of comparison, Boolean, and algebraic expressions. For example, (X=3)*7 yields a value of 7 if X=3 is true because true is defined to be 1."

> ANSI appendix, Three-Valued Logic: "ANSI-compatible SQL has three-valued logic [...] Any value compared with a NULL value evaluates to NULL. PROC SQL follows the SAS convention for handling missing values. When numeric NULL values are compared with non-NULL numbers, the NULL values are less than or smaller than all the non-NULL values. When character NULL values are compared with non-NULL characters, the character NULL values are treated as a string of blanks."

> sql-expression: "Unlike missing values in some versions of SQL, missing values in SAS always appear first in the collating sequence. Therefore, in Boolean and comparison operations, the following expressions resolve to true in a predicate: 3>null / -3>null / 0>null"

Rule: a comparison in PROC SQL evaluates to 1 or 0 (never null); `SUM(x = 0)` counts the rows where
x equals 0. A missing x gives `x = 0` -> 0 and `x < 0` -> 1.

NOT DOCUMENTED: "false is 0" is not written next to "true is defined to be 1" in the SQL book; it is
stated in the Base language concepts (D2).

### (d) GROUP BY: output order; missing as a group

> GROUP BY clause: "The data does not have to be sorted in the order of the group-by values because PROC SQL handles sorting automatically. You can use the ORDER BY clause to specify the order in which rows are displayed in the result table."

> ORDER BY clause: "If an ORDER BY clause is omitted, then a particular order to the output rows, such as the order in which the rows are encountered in the queried table, cannot be guaranteed—even if an index is present. Without an ORDER BY clause, the order of the output rows is determined by the internal processing of PROC SQL, the default collating sequence of SAS, and your operating environment."

> Grouping Data: "When a column contains missing values, PROC SQL treats the missing values as a single group."

> Grouping Data: "When you use a GROUP BY clause without an aggregate function, PROC SQL treats the GROUP BY clause as if it were an ORDER BY clause and displays a message in the log that informs you that this has happened."

Rule: GROUP BY forms one group per distinct value of the grouping columns, missing being one group.
The order of the grouped output is NOT guaranteed without ORDER BY (in practice it comes out
ascending by the group keys because of the internal sort, but the docs explicitly decline to
guarantee it).

### (e) Remerging

> "When you use a summary function in a SELECT clause or a HAVING clause, you might see the following message in the SAS log: NOTE: The query requires remerging summary statistics back with the original data. The process of remerging involves two passes through the data. On the first pass, PROC SQL calculates and returns the value of summary functions. It then uses the result to calculate the arithmetic expressions in which the summary function participates. groups data according to the GROUP BY clause. On the second pass, PROC SQL retrieves any additional columns and rows that it needs to show in the output."

> "Keep in mind that PROC SQL remerges data under these conditions: the values returned by a summary function are used in a calculation. [...] the values returned by a summary function are compared to values of a column that is not specified in the GROUP BY clause. [...] a column from the input table is specified in the SELECT clause and is not specified in the GROUP BY clause. This rule does not refer to columns used as arguments to summary functions in the SELECT clause."

Rule: selecting a non-grouped, non-aggregated column together with an aggregate returns one row per
input row (of the group), each carrying the group's (or the whole table's, if no GROUP BY) summary
value.

### (f) Joins: missing matches missing; row order

> "Most database products treat nulls as distinct entities and do not match them in joins. PROC SQL treats nulls as missing values and as matches for joins. Any null will match with any other null of the same type (character or numeric) in a join."

> joined-table: "The row is considered to be matching if the result of the expression is true (a nonzero, nonmissing value) for that row."

> joined-table: "A left outer join, specified with the keywords LEFT JOIN and ON, has all the rows from the Cartesian product of the two tables for which the SQL expression is true, plus rows from the first (Lefttab) table that do not match any row in the second (Righttab) table." "Columns that do not exist in one table have null (missing) values for those rows in the result table."

> Sorting Data: "In general, if you do not explicitly specify a sort order, then PROC SQL output is not guaranteed to be in any particular order."

Rule: an ON/WHERE equality `a.k = b.k` is true when both keys are missing, so missing keys match
each other. A join result's row order is not guaranteed without ORDER BY; and ORDER BY guarantees
order only on the listed columns (ties are not guaranteed stable, see (j)).

### (g) CALCULATED

> "CALCULATED enables you to use the results of an expression in the same SELECT clause or in the WHERE clause. It is valid only when used to refer to columns that are calculated in the immediate query expression."

Rule: `CALCULATED alias` denotes the value of the expression aliased in the same SELECT list.

### (h) `SELECT ... INTO :macrovar`

> INTO clause: "Values assigned by the INTO clause use the BEST8. format by default." "Large numeric values might be displayed using scientific notation. To display large numeric values without scientific notation, use another format, such as the w. format: `select sum(population) format=16. [...]`"

> INTO clause: "When storing a value in a single macro variable, PROC SQL preserves leading or trailing blanks. The TRIMMED option can be used to trim the leading and trailing blanks from values that are stored in a single macro variable. However, if values are stored in a range of macro variables, or if the SEPARATED BY option is used to store multiple values in a single macro variable, PROC SQL trims leading or trailing blanks unless you specify the NOTRIM option."

> Macro facility page: "If the query produces more than one row of output, then the macro variable contains only the value from the first row. If the query has no rows in its output, then the macro variable is not modified."

Rule: a numeric value stored by `INTO :m` (no FORMAT= on the column) is the BEST8. rendering of the
value, right-aligned in 8 characters with leading blanks preserved (no TRIMMED); so the macro
variable holds at most 8 characters of precision, and the text is what re-enters the program when
`&m` is resolved. With a column FORMAT= that format is used instead.

NOT DOCUMENTED: the exact digits BEST8. produces for a given double (rounding to fit 8 characters)
is specified by the BEST format, not on these pages. PARTLY DOCUMENTED. The loss of precision this
causes when `&m` is used in later arithmetic is a consequence, not a quoted statement.

### (i) CASE with no matching WHEN and no ELSE

> "If when-condition returns a nonzero, nonmissing result, then the WHEN clause is true." "If every when-condition is false, then PROC SQL executes the ELSE expression, and its result becomes the CASE expression's result. If no ELSE expression is present and every when-condition is false, then the result of the CASE expression is a missing value."

Rule: first true WHEN wins; no true WHEN and no ELSE gives missing.

### (j) ORDER BY and missing

> Sorting Data: "PROC SQL sorts nulls, or missing values, before character or numeric data. Therefore, when you specify ascending order, missing values appear first in the query results."

> ORDER BY clause: "If neither ASC nor DESC is specified, the data is ordered in ascending order." "The order of the output rows that are returned is guaranteed only for columns that are specified in the ORDER BY clause. The ORDER BY clause does not guarantee that the order of the rows generated is deterministic. The ANSI standard for SQL allows the SQL implementation to specify whether the ORDER BY clause is stable or unstable. If the joint combination of values that is referenced in an ORDER BY clause for a query are unique in all of the rows that are being ordered, then the order of rows that is generated by ORDER BY is always deterministic."

Rule: ORDER BY is ascending by default with missing first; row order among rows that tie on all
ORDER BY keys is not guaranteed.

### (k) Division by zero and LOG of nonpositive values in PROC SQL

NOT DOCUMENTED in the SQL Procedure User's Guide. What the docs do say:

> sql-expression: "PROC SQL supports many of the functions available to the SAS DATA step."

> ANSI appendix: "PROC SQL follows the SAS convention for handling missing values."

together with the Base rules in D2 ("assigns a missing value to the result if you try to perform an
invalid operation, such as ... dividing by zero / taking the logarithm of zero"; invalid function
argument -> missing). So the result is a missing value by the general SAS rules; the SQL-specific
log messages and any difference in `_ERROR_` handling are NOT DOCUMENTED. Missing operands
propagate (x/. and ./0 are missing).

---

## D9. One-to-one MERGE without BY; WHERE= on a MERGE input; LENGTH after MERGE

URLs

- MERGE statement: https://documentation.sas.com/doc/en/lestmtsref/9.4/n1i8w2bwu1fn5kn1gpxj18xttbb0.htm
- Combining SAS Data Sets: Methods (One-to-One Merging): https://documentation.sas.com/doc/en/lrcon/9.4/n1tgk0uanvisvon1r26lc036k0w7.htm
- WHERE= data set option: https://documentation.sas.com/doc/en/ledsoptsref/9.4/p0ny9o8t8hc5zen1qn3ft9dhtsxx.htm
- Ways to Create Variables: https://documentation.sas.com/doc/en/lrcon/9.4/n0bbin3txgxlown1v2v5d8qbc9vq.htm
- LENGTH statement: https://documentation.sas.com/doc/en/lestmtsref/9.4/p1hgqgmxm3dpqcn1d4w5za5qbz0d.htm

Quotes

> "To perform a one-to-one merge, use the MERGE statement without a BY statement. SAS combines the first observation from all data sets that are named in the MERGE statement into the first observation in the new data set, the second observation from all data sets into the second observation in the new data set, and so on. In a one-to-one merge, the number of observations in the new data set is equal to the number of observations in the largest data set named in the MERGE statement."

> "If a variable exists in more than one data set, the value from the last data set that is read is the one that is written to the new data set. The variables are combined exactly as they are read from each data set." "[...] the value from the last data set read is the one that is written to the new data set even if the value is missing. Once SAS has processed all observations in a data set, all subsequent observations in the new data set have missing values for the variables that are unique to that data set."

> "Execution — Step 1: SAS reads the first observation from each data set into the program data vector, reading the data sets in the order in which they appear in the MERGE statement. If two data sets contain the same variables, the values from the second data set replace the values from the first data set. After reading the first observation from the last data set and executing any other statements in the DATA step, SAS writes the contents of the program data vector to the new data set. Only those variables that are created or assigned values during the DATA step are set to missing."

> "Compilation phase: SAS reads the descriptor information of each data set that is named in the MERGE statement. Then, SAS creates a program data vector that contains all the variables from all data sets as well as variables created by the DATA step."

> MERGE: "(data-set-options) [...] The data set options specify actions that SAS is to take when it reads observations into the DATA step for processing."

> WHERE=: "Use the WHERE= data set option with an input data set to select observations that meet the condition that is specified in the WHERE expression." "The WHERE statement applies to all input data sets, whereas the WHERE= data set option selects observations only from the data set for which it is specified."

> Ways to Create Variables: "IMPORTANT: Place the LENGTH statement first in the DATA step before any other statements that reference the variable." "You cannot change the length of a character variable with a subsequent LENGTH or ATTRIB statement within the same DATA step. [...] You can change the length of a numeric variable by using a subsequent LENGTH statement."

> LENGTH: "If the variable is character or varchar, the length applies to the program data vector and the output data set. If the variable is numeric, the length applies only to the output data set."

Rule

- `merge A B;` with no BY pairs row i of A with row i of B. Output row count = max(nobs(A),
  nobs(B)) (after any WHERE= filtering of each input).
- Same-named variables: the value read from the data set listed later overwrites the earlier one
  for that row, even when it is missing.
- When one input is exhausted, later output rows have missing values for the variables unique to
  that input (same-named variables then come from whichever input still has rows).
- `B(where=(cond))` filters B's rows before pairing, so pairing is by position among the rows that
  pass the filter; the WHERE= applies to that input only.
- A LENGTH statement placed after MERGE cannot change the length of a character variable that the
  MERGE already defined; for a numeric variable it changes only the stored (output) length. For a
  variable not yet defined, LENGTH defines it as usual.

NOT DOCUMENTED / caveats

- The quoted "missing values for the variables that are unique to that data set" covers unique
  variables only. For a same-named variable after the later-listed data set runs out, the docs do
  not spell out the value; by the PDV mechanics it is the value read from the data set that still
  has rows. PARTLY DOCUMENTED.
- Position-based pairing after WHERE= filtering is the natural reading of "select observations ...
  from the data set for which it is specified", but no sentence states the interaction with a
  one-to-one merge explicitly. PARTLY DOCUMENTED.
- The log message when LENGTH tries to change an existing character variable is NOT quoted here.
- Which input supplies the type/length of a same-named variable (the first data set in MERGE order
  that contains it, by the usual PDV rule) is not stated in the quoted passages. NOT DOCUMENTED here.

---

## D10. PROC LOGISTIC: ROC statement with PRED=, MODEL ... / NOFIT, ROCAssociation, ROCEPS=

URLs

- ROC statement: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_syntax29.htm
- PROC LOGISTIC statement (ROCOPTIONS): https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_syntax01.htm
- MODEL statement (NOFIT, ROCEPS=, ROCCI, BINWIDTH=): https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_syntax22.htm
- Receiver Operating Characteristic Curves (incl. ROC Computations): https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details47.htm
- Displayed Output: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details82.htm
- OUTROC= data set: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details70.htm
- Example 78.8: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_examples08.htm

Quotes

> ROC statement: "The specification can be either a list of effects that have previously been specified in the MODEL statement, or PRED=variable, where the variable does not have to be specified in the MODEL statement. The PRED= option enables you to input a criterion produced outside PROC LOGISTIC; for example, you can fit a random-intercept model by using PROC GLIMMIX or use survey weights in PROC SURVEYLOGISTIC, then use the predicted values from those models to produce an ROC curve for the comparisons." "The options are ignored for the PRED= specification." "This statement is available only for binary and binomial response models."

> NOFIT: "NOFIT performs the global score test without fitting the model. [...] If the NOFIT option is specified along with other MODEL statement options, NOFIT takes effect and all other options except FIRTH, LINK=, NOINT, OFFSET=, and TECHNIQUE= are ignored."

> ROC details: "By default for the reference contrast, the specified or selected model is used as the reference unless the NOFIT option is specified in the MODEL statement, in which case the first ROC model is the reference."

> Example 78.8: "the NOFIT option is specified in the MODEL statement to prevent PROC LOGISTIC from fitting the model with three covariates. [...] Note that the original data set contains six more records with missing values for one of the tests, but PROC LOGISTIC ignores all records with missing values; hence there is a common sample size for each of the three models."

> ROC details: "ROC curves can be created [...] from specified models in ROC statements, or from input variables which act as [pi-hat] in the preceding discussion. Association statistics are computed for these models, and the models are compared when the ROCCONTRAST statement is specified."

> ROC details: "Suppose that the n individuals undergo a test for predicting the event and that the test is based on the estimated probability of the event. Higher values of this estimated probability are assumed to be associated with the event."

> ROC Computations: "The trapezoidal area under an empirical ROC curve is equal to the Mann-Whitney two-sample rank measure of association statistic (a generalized U-statistic) applied to two samples, {X_i}, i = 1,...,n1, in C1 and {Y_i}, i = 1,...,n2, in C2. PROC LOGISTIC uses the predicted probabilities in place of X and Y; however, in general any criterion could be used. Denote the frequency of observation i in C_k as f_ki, and denote the total frequency in C_k as F_k. [...] The trapezoidal area under the curve is computed as [formula] c-hat = (1/(F1 F2)) * sum_{i=1..n1} sum_{j=1..n2} psi(X_i, Y_j) f_1i f_2j, with psi(X, Y) = 1 if Y < X; 1/2 if Y = X; 0 if Y > X, so that E(c-hat) = Pr(Y < X) + (1/2) Pr(Y = X)."

(C1 = events, Y = 1; C2 = nonevents.)

> Displayed Output: "ROC Association Statistic and Contrast Tables: Displayed if a ROC statement, a ROCCONTRAST statement, or the ROCCI option is specified. For more information, about the Mann-Whitney statistics and the test and estimation computations, see the section ROC Computations. For more information about the other statistics, see the section Rank Correlation of Observed Responses and Predicted Probabilities."

Example 78.8 output header: "ROC Association Statistics | ROC Model | Mann-Whitney: Area, Standard Error, 95% Wald Confidence Limits | Somers' D | Gamma | Tau-a".

> ROCEPS= (MODEL): "ROCEPS=number specifies a criterion for the ROC curve used for grouping estimated event probabilities that are close to each other. This option is available only for binary and binomial response models. In each group, the difference between the largest and the smallest estimated event probabilities does not exceed the given value. The value for number must be between 0 and 1; the default value is the square root of the machine epsilon, which is about 1E–8 (in releases prior to 9.2, the default was 1E–4). The smallest estimated probability in each group serves as a cutpoint for predicting an event response. The ROCEPS= option has no effect unless the OUTROC= option, the BINWIDTH=0 option, or a ROC statement is specified."

> ROCOPTIONS(EPS=): "EPS=value is an alias for the ROCEPS= option in the MODEL statement. This value is used to determine which predicted probabilities are equal. The default value is the square root of the machine epsilon, which is about 1E–8."

> OUTROC= data set: "Predicted probabilities that are close to each other are grouped together, with the maximum allowable difference between the largest and smallest values less than a constant that is specified by the ROCEPS= option. The smallest estimated probability is used to represent the group."

> ROC details: "The area under the ROC curve, as determined by the trapezoidal rule, is estimated by the concordance index, c, in the 'Association of Predicted Probabilities and Observed Responses' table."

Rule

- With `MODEL y(event=...) = ... / NOFIT; ROC 'label' PRED=p;` no model is fitted; p is used as the
  score in place of the predicted event probability, higher p meaning "more likely event".
- ROCAssociation Area = c-hat = [ #(event, nonevent) pairs with p_event > p_nonevent
  + 0.5 * #pairs with equal p ] / (F1 * F2), frequencies weighting pairs. This is exactly the
  trapezoidal area of the empirical ROC curve (documented as an identity).
- SomersD, Gamma, TauA in the same table are the D11 rank-correlation indices computed from the same
  concordant/discordant/tied pair counts: D = (nc - nd)/t (= 2*Area - 1), Gamma = (nc - nd)/(nc + nd),
  Tau-a = (nc - nd)/(0.5 N (N - 1)).
- "Equal" predicted values means equal after ROCEPS grouping: values are grouped so that within a
  group max - min does not exceed ROCEPS (default sqrt(machine epsilon), about 1E-8, i.e. about
  1.49E-8 for IEEE doubles); the group is represented by its smallest value.
- Observations with a missing response, missing MODEL covariates or (per the example) missing ROC
  variables are excluded.

NOT DOCUMENTED / caveats

- The exact grouping procedure for ROCEPS (where a group starts, whether grouping is a greedy scan
  from the smallest or the largest value, and whether "does not exceed" (MODEL page) or "less than"
  (OUTROC= page) is the test) is NOT DOCUMENTED; the two pages differ in wording at the boundary.
- That ROCEPS-grouped values are the ones treated as `Y = X` in psi is implied by "This value is
  used to determine which predicted probabilities are equal" and "has no effect unless ... a ROC
  statement is specified", but the psi formula itself is written with exact equality. PARTLY
  DOCUMENTED.
- "sqrt of machine epsilon ... about 1E-8": the exact constant is not printed.
- The docs do not state whether a PRED= variable must lie in [0, 1], nor what happens to
  observations with a missing PRED= value specifically. SECONDARY, UNVERIFIED (search summary of SAS
  Usage Note 39724, "ROC analysis using validation data and cross validation",
  https://support.sas.com/kb/39/724.html; page could not be opened): the note uses
  `model ... / nofit; roc pred=...;` and says the PRED= variable must not contain missing values.
- With NOFIT, the "Association of Predicted Probabilities and Observed Responses" table for the
  MODEL is not produced (no fit); the ROC table is. The NOFIT text "No further analyses are
  performed" predates the ROC statement and does not mention it; the ROC/NOFIT combination is
  documented in the ROC details and Example 78.8.

---

## D11. PROC LOGISTIC "Association of Predicted Probabilities and Observed Responses"; BINWIDTH=

URLs

- Rank Correlation of Observed Responses and Predicted Probabilities (in Model Fitting Information): https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details12.htm
- MODEL statement, BINWIDTH=: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_syntax22.htm
- ROC Computations: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details47.htm

Quotes

> "The predicted mean score of an observation is the sum of the Ordered Values (shown in the 'Response Profile' table) minus one, weighted by the corresponding predicted probabilities for that observation; that is, the predicted means score equals [formula] sum_{i=1..k+1} (i - 1) pi-hat_i, where k+1 is the number of response levels and pi-hat_i is the predicted probability of the ith (ordered) response."

> "A pair of observations with different observed responses is said to be concordant if the observation with the lower ordered response value has a lower predicted mean score than the observation with the higher ordered response value. If the observation with the lower ordered response value has a higher predicted mean score than the observation with the higher ordered response value, then the pair is discordant. If the pair is neither concordant nor discordant, it is a tie."

> "If you have more than two response levels, enumeration of the total numbers of concordant and discordant pairs is carried out by categorizing the predicted mean score into intervals of length k/500 and accumulating the corresponding frequencies of observations. You can change the length of these intervals by specifying the BINWIDTH= option in the MODEL statement."

> "Let N be the sum of observation frequencies in the data. Suppose there are a total of t pairs with different responses: n_c of them are concordant, n_d of them are discordant, and t - n_c - n_d of them are tied. PROC LOGISTIC computes the following four indices of rank correlation for assessing the predictive ability of a model: [formula] c = (n_c + 0.5 (t - n_c - n_d)) / t; Somers' D (Gini coefficient) = (n_c - n_d) / t; Goodman-Kruskal gamma = (n_c - n_d) / (n_c + n_d); Kendall's tau-a = (n_c - n_d) / (0.5 N (N - 1))"

> "If there are no ties, then Somers' D (Gini's coefficient) equals 2c - 1. Note that the concordance index, c, also gives an estimate of the area under the receiver operating characteristic (ROC) curve when the response is binary (Hanley and McNeil 1982)."

> "For binary responses, the predicted mean score is equal to the predicted probability for Ordered Value 2. As such, the preceding definition of concordance is consistent with the definition used in previous releases for the binary response model."

> BINWIDTH=: "BINWIDTH=width specifies the size of the bins used for estimating the association statistics. [...] Valid values are 0 <= width < 1 (for polytomous response models, 0 < width < 1). In releases before SAS/STAT 14.1, the default width is 0.002. Beginning in SAS/STAT 14.1, if you have a binary response and fewer than 5,000,000 observations, the default is BINWIDTH=0; this means that no binning is performed and the exact values of the statistics are computed using the trapezoidal area described in the section ROC Computations. This method is a bit slower and might require more memory than the binning approach. If a nonzero width does not evenly divide the unit interval, it is reduced to a valid value and a message is displayed in the SAS log. [...] The BINWIDTH= option is ignored and no binning is performed when a ROC statement is specified, when ROC graphics are produced, or when the SCORE statement computes an ROC area."

> ROC Computations: "Note that the concordance index, c, in the 'Association of Predicted Probabilities and Observed Responses' table does not use weights unless both the WEIGHTED and BINWIDTH=0 options are in effect."

> ROCOPTIONS(WEIGHTED): "The 'Association of Predicted Probabilities and Observed Responses' table uses frequency (unless the BINWIDTH=0 option is also specified on the MODEL statement), and is suppressed when ROC comparisons are performed."

Rule

- Pairs: all pairs of observations with different observed responses (t = F_event * F_nonevent for a
  binary response, frequency-weighted). Binary case: a pair is concordant when the observation that
  is the event has the higher predicted event probability, discordant when lower, tied otherwise.
  (The docs phrase it through the "predicted mean score" = predicted probability of Ordered Value 2;
  lower ordered response value <-> lower mean score.)
- c = (nc + 0.5*(t - nc - nd))/t; Somers' D = (nc - nd)/t; Gamma = (nc - nd)/(nc + nd);
  Tau-a = (nc - nd)/(0.5*N*(N-1)), N = total frequency.
- SAS/STAT 14.1 and later (so 15.x): for a binary response with fewer than 5,000,000 observations
  the default is BINWIDTH=0: exact computation, no binning. Before 14.1 the default width was
  0.002 (binned approximation; that pairs in the same bin count as tied is the natural reading of
  "categorizing ... into intervals", not a quoted sentence).

NOT DOCUMENTED / caveats

- With BINWIDTH=0 the tie test uses ROCEPS (D10: "The ROCEPS= option has no effect unless the
  OUTROC= option, the BINWIDTH=0 option, or a ROC statement is specified"), so "tied" means equal
  within ROCEPS grouping, not bitwise equal. The interaction is stated only through that sentence.
  PARTLY DOCUMENTED.
- "Percent Concordant/Discordant/Tied" and "Pairs" in the displayed table are 100*nc/t, 100*nd/t,
  100*(t-nc-nd)/t and t; these displayed columns are shown in examples but not defined by formula.
- Identity: by the quoted formulas 2c - 1 = (nc - nd)/t always, i.e. Somers' D = 2c - 1 regardless
  of ties; the docs' "If there are no ties" qualifier is weaker than the formulas.

---

## D12. PROC LOGISTIC LACKFIT (Hosmer-Lemeshow)

URLs

- SAS/STAT 15.2, Goodness-of-Fit Tests (The Hosmer-Lemeshow Goodness-of-Fit Test): https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details35.htm
- SAS/STAT 15.1 (same page id, same text): https://documentation.sas.com/doc/en/statug/15.1/statug_logistic_details35.htm
- SAS/STAT 14.1 (older wording): https://support.sas.com/documentation/cdl/en/statug/68162/HTML/default/statug_logistic_details32.htm

Quote, SAS/STAT 15.2 (algorithm in full; 15.1 has the same sentences)

> "The observations are sorted in increasing order of a scored value. For binary response variables, the scored value of an observation is its estimated event probability. The event is the response level specified in the response variable option EVENT=, the response level that is not specified in the REF= option, or, if neither of these options was specified, the response level identified in the 'Response Profiles' table as 'Ordered Value 1.'"

> "The observations (and frequencies) are then combined into G groups. By default G = 10, but you can specify G >= 5 with the NGROUPS= suboption of the LACKFIT option in the MODEL statement. For single-trial syntax, observations with identical scored values are combined and are placed in the same group. Let F be the total frequency. The target frequency for each group is [formula] T = floor(F/G + 0.5), which is the integer part of F/G + 0.5. Load the first group (g_j, j = 1) with the observation that has the smallest scored value and with frequency f_1, and let the next-smallest observation have a frequency of f. PROC LOGISTIC performs the following steps for each observation to create the groups:
> 1. If j = G, then add this observation to group g_j.
> 2. Otherwise, if f_j < T and f_j + floor(f/2) <= T, then add this observation to group g_j.
> 3. Otherwise, start loading the next group (g_{j+1}) with f_{j+1} = f, and set j = j + 1.
>
> If the final group g_j has frequency f_j < F/(2G), then add these observations to the preceding group. The total number of groups actually created, g, can be less than G. There must be at least three groups in order for the Hosmer-Lemeshow statistic to be computed."

> "For binary response variables, the Hosmer-Lemeshow goodness-of-fit statistic is obtained by calculating the Pearson chi-square statistic from the 2 x g table of observed and expected frequencies, where g is the number of groups. The statistic is written [formula] chi2_HL = sum_{j=1..g} (O_j - F_j pibar_j)^2 / (F_j pibar_j (1 - pibar_j)) where F_j is the total frequency of subjects in the jth group, O_j is the total frequency of event outcomes in the jth group, and pibar_j is the average estimated predicted probability of an event outcome for the jth group. (Note that the predicted probabilities are computed as shown in the section Linear Predictor, Predicted Probability, and Confidence Limits and are not the cross validated estimates discussed in the section Classification Table.) The Hosmer-Lemeshow statistic is then compared to a chi-square distribution with (g - r) degrees of freedom, where the value of r can be specified in the DFREDUCE= suboption of the LACKFIT option in the MODEL statement. The default is r = 2."

> "Large values of chi2_HL (and small p-values) indicate a lack of fit of the model."

Quote, SAS/STAT 14.1 (older wording of the same scheme, for comparison)

> "First, the observations are sorted in increasing order of their estimated event probability. [...] The observations are then divided into approximately 10 groups according to the following scheme. Let N be the total number of subjects. Let M be the target number of subjects for each group given by [formula] M = [0.1 x N + 0.5] where [x] represents the integral value of x. If the single-trial syntax is used, blocks of subjects are formed of observations with identical values of the explanatory variables. Blocks of subjects are not divided when being placed into groups. Suppose there are n_1 subjects in the first block and n_2 subjects in the second block. The first block of subjects is placed in the first group. Subjects in the second block are added to the first group if [formula] n_1 < M and n_1 + [0.5 x n_2] <= M. Otherwise, they are placed in the second group. In general, suppose subjects of the (j – 1) block have been placed in the kth group. Let c be the total number of subjects currently in the kth group. Subjects for the jth block (containing n_j subjects) are also placed in the kth group if [formula] c < M and c + [0.5 x n_j] <= M. Otherwise, the n_j subjects are put into the next group. In addition, if the number of subjects in the last group does not exceed [0.05 x N] (half the target group size), the last two groups are collapsed to form only one group. Note that the number of groups, g, can be smaller than 10 if there are fewer than 10 patterns of explanatory variables. There must be at least three groups in order for the Hosmer-Lemeshow statistic to be computed."

Rule (SAS/STAT 15.x)

1. Sort by estimated event probability ascending; merge observations with identical scored values
   into one block with frequency f (blocks are never split).
2. G = 10 by default; F = total frequency; T = floor(F/G + 0.5).
3. Group 1 starts with the first block. For each later block with frequency f, with f_j the current
   group's frequency: if j = G add it to group j; else if f_j < T and f_j + floor(f/2) <= T add it
   to group j; else start group j+1 with it.
4. If the final group's frequency is < F/(2G), merge it into the preceding group.
5. Expected events in group j = F_j * pibar_j (pibar_j = frequency-weighted mean predicted event
   probability in the group); chi2_HL = sum (O_j - F_j pibar_j)^2 / (F_j pibar_j (1 - pibar_j));
   df = g - 2 by default (g = number of groups actually formed, at least 3).

NOT DOCUMENTED / caveats

- Differences between 14.1 and 15.x wording that can change results at the margins, and which the
  docs do not reconcile: (i) blocks are "observations with identical values of the explanatory
  variables" (14.1) versus "observations with identical scored values" (15.x); (ii) the last-group
  test is "does not exceed [0.05 x N]" (<=, integer part; 14.1) versus "f_j < F/(2G)" (strict, no
  integer part; 15.x); (iii) 15.x adds the explicit "If j = G" cap, 14.1 has no cap sentence.
- Whether "identical scored values" means bitwise-equal doubles or equality within a tolerance is
  NOT DOCUMENTED.
- Order of observations within a block and the summation order for pibar_j are NOT DOCUMENTED
  (matters only at floating-point level).
- The "Partition for the Hosmer and Lemeshow Test" table columns (Observed/Expected for event and
  nonevent) are shown in examples; expected nonevent = F_j (1 - pibar_j) follows from the 2 x g
  Pearson form.

---

## D13. PROC LOGISTIC OUTPUT PREDICTED=; PROC PLM SCORE

URLs

- OUTPUT statement: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_syntax27.htm
- Missing Values: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details01.htm
- Response Level Ordering: https://documentation.sas.com/doc/en/statug/15.2/statug_logistic_details02.htm
- PLM SCORE statement: https://documentation.sas.com/doc/en/statug/15.2/statug_plm_syntax08.htm

Quotes

> OUTPUT: "PREDICTED=name | PRED=name | PROB=name | P=name names the variable containing the predicted probabilities. For the events/trials syntax or single-trial syntax with binary response, it is the predicted event probability."

> OUTPUT: "The OUTPUT statement creates a new SAS data set that contains all the variables in the input data set and, optionally, the estimated linear predictors and their standard error estimates, the estimates of the cumulative or individual response probabilities [...]"

> OUTPUT: "The estimated linear predictor, its standard error estimate, all predicted probabilities, and the confidence limits for the cumulative probabilities are computed for all observations in which the explanatory variables have no missing values, even if the response is missing. By adding observations with missing response values to the input data set, you can compute these statistics for new observations or for settings of the explanatory variables not present in the data without affecting the model fit."

> Missing Values: "Any observation with missing values for the response, offset, strata, or explanatory variables is excluded from the analysis [...] The estimated linear predictor and its standard error estimate, the fitted probabilities and confidence limits, and the regression diagnostic statistics are not computed for any observation with missing offset or explanatory variable values. However, if only the response value is missing, the linear predictor, its standard error, the fitted individual and cumulative probabilities, and confidence limits for the cumulative probabilities can be computed and output to a data set by using the OUTPUT statement."

> Response Level Ordering: "by default, PROC LOGISTIC models the probability of response levels with lower Ordered Value." "By default, PROC LOGISTIC assigns Ordered Value 1 to response level Y=0, and Ordered Value 2 to response level Y=1. As a result, PROC LOGISTIC models the probability of the nonevent (Ordered Value=1) category [...]" "Explicitly state which response level is to be modeled by using the response variable option EVENT= in the MODEL statement: `model Y(event='1') = Exposure;`" "Specify the response variable option DESCENDING in the MODEL statement to assign the lowest Ordered Value to Y=1: `model Y(descending)=Exposure;`"

> PLM SCORE, Table 9: "PREDICTED | Linear predictor | [formula] eta-hat = x beta-hat | Predicted"

> PLM SCORE: "ILINK requests that predicted values be inversely linked to produce predictions on the data scale. By default, predictions are produced on the linear scale where covariate effects are additive."

> PLM SCORE: "DATA=SAS-data-set specifies the input data set for scoring. This option is required, and the data set is examined for congruity with the previously fitted (and stored) model. For example, all necessary variables to form a row of the X matrix must be present in the input data set and must be of the correct type and format. The following variables do not have to be present in the input data set: the response variable [...]"

> PLM SCORE: "NOVAR requests that variables from the input data set not be added to the output data set."

Rule

- OUT= of the LOGISTIC OUTPUT statement has one row per input observation (all input variables
  kept). PREDICTED= is nonmissing for every observation whose explanatory variables are all
  nonmissing, including observations with a missing response (which do not affect the fit); it is
  missing when any explanatory (or offset) variable is missing.
- For a binary response the value is the predicted probability of the modelled ("event") level:
  the level named in EVENT=, or Ordered Value 1 (which DESCENDING makes the highest level, e.g.
  Y=1 for a 0/1 response).
- PROC PLM `SCORE DATA=... OUT=... PREDICTED=name;` writes the linear predictor x'beta-hat by
  default; with `/ ILINK` it writes the inverse-link value (the probability, for a logit link).
  The output keeps the input variables unless NOVAR.

NOT DOCUMENTED / caveats

- PROC PLM SCORE with a missing model covariate: NOT DOCUMENTED in the PLM chapter (the word
  "missing" does not occur in the SCORE statement section in this sense). SECONDARY, UNVERIFIED
  (search summaries only; pages could not be opened): SAS Usage Note 33307 on scoring
  (https://support.sas.com/kb/33/307.html) says several conditions make it impossible to score an
  observation, "resulting in a missing predicted value"; a SAS Communities answer
  (https://communities.sas.com/t5/Statistical-Procedures/Missing-predicted-values-using-proc-plm-after-proc-logistic/m-p/477726)
  says a missing value in any model independent variable gives a missing predicted result. Treat
  "row is kept, predicted value is missing" as expected behaviour that needs an empirical check.
- Which probability PLM's ILINK value is (event level as stored by the fitting procedure) is implied
  by the stored model, not stated in the PLM chapter.
- With `_LEVEL_`: for a binary single-trial model OUT= has one row per observation and `_LEVEL_`
  holds the event level; documented on the OUTPUT page ("the data set also contains a variable named
  _LEVEL_").

---

## D14. Numeric literals and run-time binary arithmetic

URLs

- Numerical Accuracy in SAS Software: https://documentation.sas.com/doc/en/lrcon/9.4/p0ji1unv6thm0dn1gp4t01a1u0g6.htm
- SAS Constants in Expressions: https://documentation.sas.com/doc/en/lrcon/9.4/p0cq7f0icfjr8vn19vyunwmmsl7m.htm
- ROUND function (binary vs decimal discussion): https://documentation.sas.com/doc/en/lefunctionsref/9.4/p0tj6cmga7p8qln1ejh6ebevm0c9.htm

Quotes

> Numerical Accuracy: "SAS stores numeric values in 8 bytes of data. Although there are various ways to store binary numbers internally, SAS uses floating-point representation to store numeric values." "All platforms on which SAS runs use 8-byte floating-point representation." "The IEEE standard is used by the Windows and UNIX operating systems."

> Numerical Accuracy: "although computers do allow the use of decimal numbers and decimal arithmetic via human-centric software interfaces, all numbers and data are eventually converted to binary format to be stored and processed by the computer internally. It is in the conversion between these 2 number systems – decimal to binary – that precision is affected and rounding errors are introduced."

> Numerical Accuracy: "Because the decimal values 0.1 and 0.3 do not have exact binary representations, this equality does not hold true in binary arithmetic."

> ROUND page: "In decimal arithmetic, 3*0.1 is exactly equal to 0.3, but this equality is not true in binary arithmetic." with the example `three=3; point_three=0.3; three_times_point_one=three*0.1; difference=point_three - three_times_point_one;` whose log shows `difference=-5.55112E-17`.

> ROUND page: "If the characters '0.3' appear as a constant in a SAS program, the value is computed by the standard informat as 3/10."

> Constants: "A numeric constant is a number that appears in a SAS statement." "Most numeric constants are written just as numeric data values are."

Rule

- Every numeric value, including a decimal literal such as `0.05`, is an IEEE 754 double on
  Windows/UNIX; a literal is converted as by the standard numeric informat (the double nearest the
  decimal, computed "as 3/10" for `0.3`).
- Arithmetic on such values is binary floating-point arithmetic: `base_rate + 0.02` is the double
  sum of the two doubles, which need not equal the double for the decimal literal `0.07`. The docs'
  own example (3*0.1 - 0.3 = -5.55112E-17) establishes that no decimal correction is applied.

NOT DOCUMENTED / caveats

- Whether a constant sub-expression (`0.05 + 0.02`) is folded at compile time or evaluated at run
  time is NOT DOCUMENTED; either way it is the binary double sum, so the value is the same.
- "computed by the standard informat as 3/10" describes the literal conversion; that the result is
  the correctly rounded nearest double for every literal is NOT explicitly guaranteed.
- Extended-precision intermediates: the docs note "you might occasionally see varying results
  between the platforms due to compiler differences, and math library differences"; bit-exact
  cross-platform equality is not promised.

---

## D15. `x = (cond);` and `IF numeric-expression THEN`

URL

- SAS Operators in Expressions: https://documentation.sas.com/doc/en/lrcon/9.4/p00iah2thp63bmn1lt20esag14lh.htm

Quotes

> "You can also use comparisons in expressions in assignment statements. For example, the preceding statements can be recoded as follows: `c=5*(x<y)+12*(x>=y);` Since SAS evaluates quantities inside parentheses before performing any operations, the expressions (x<y) and (x>=y) are evaluated first, and the result (1 or 0) is substituted for the expressions in parentheses."

> "If the comparison is true, the result is 1. If the comparison is false, the result is 0."

> "You can perform comparisons on character operands, but the comparison always yields a numeric result (1 or 0)."

> "In addition, a numeric expression without any logical operators can serve as a Boolean expression."

> "In SAS, any numeric value other than 0 or missing is true, and a value of 0 or missing is false. [...] `if cost then remarks='Ready to budget';` This statement is equivalent to: `if cost ne . and cost ne 0 then remarks='Ready to budget';`"

> "any nonzero, nonmissing constant is always evaluated as true."

> Sum statement page example (https://documentation.sas.com/doc/en/lestmtsref/9.4/n1dfiqj146yi2cn1maeju9wo7ijs.htm): `nx + (x ne .);`

Rule

- `x = (cond);` assigns the numeric 1 if the comparison/logical expression is true and 0 if false;
  it is never missing, even when operands are missing (missing compares as the smallest value, D2).
- `IF e THEN ...` with a numeric e executes the THEN branch iff e is neither 0 nor missing; otherwise
  the ELSE branch (if any).

NOT DOCUMENTED / caveats

- None material. (Compound conditions `a < b < c` are documented as `(a<b) and (b<c)`; AND/OR
  results are 1/0, see D2.)
