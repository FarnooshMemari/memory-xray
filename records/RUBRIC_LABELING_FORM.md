# Rubric labeling form (blind)

> **Amendment 4:** in this study, the two labelers were AI models (GPT-6 and Gemini), not people. See `rubric_validation_record.md`.

Two different people each fill in **their own file**:
- labeler 1: `records/labels/labeler_1.json`;
- labeler 2: `records/labels/labeler_2.json`.

Do not look at the other person's file, or at the scores in `scenarios/macro_*.json`.

For each of the three scenarios:
1. **Each record (E1–E4):** pick the rubric `component` (`P`, `I`, `G`, `E` or `F`) and a `score` of `-1`, `0` or `1`. Write the score as a number, not text.
2. **`signal`:** add up your four scores and apply the decision rule: `Positive` if the total is +2 or more, `Negative` if −2 or less, otherwise `Neutral`.
3. **`flip_target_score`:** score the flipped record's new text (shown under "Flip variant").
4. **`flip_signal`:** recompute the total with that one record replaced by your flip score, and apply the same rule.

Also fill in your `name` and today's `date`. Then run `python check_labels.py` to see whether anything is missing or inconsistent.

## Rubric (`rubric_macro_v1`)

- **P (policy rate)**: +1 = rate cut, or explicit easing bias; -1 = rate hike, or explicit tightening bias; 0 = unchanged with no stated bias
- **I (inflation)**: +1 = falling and at, near or below target; -1 = rising, or well above target; 0 = stable at target
- **G (growth and labor)**: +1 = PMI at or above 50 and rising, or labor market improving; -1 = PMI below 50, or unemployment rising / employment falling; 0 = mixed or flat
- **E (earnings expectations)**: +1 = consensus 12-month earnings forecasts revised up by 1% or more; -1 = revised down by 1% or more; 0 = revisions smaller than 1%
- **F (financial conditions)**: +1 = credit spreads narrowing or credit standards easing; -1 = credit spreads widening or credit standards tightening; 0 = little change

Decision: Positive if S >= +2; Negative if S <= -2; otherwise Neutral.

## macro_a

Question: What is the 12-month signal for Economy A's broad equity market?

- **E1**: Economy A's central bank lowered its policy rate by 50 basis points to 4.25% at its latest meeting and said further cuts are possible if inflation keeps easing.
- **E2**: Core consumer-price inflation in Economy A slowed to 2.4% a year from 3.9% a year earlier, close to the central bank's 2% target.
- **E3**: Economy A's manufacturing purchasing managers' index fell to 47.6, its fourth straight month below the 50 level that separates expansion from contraction.
- **E4**: Analysts raised their consensus forecast for Economy A's listed-company earnings over the next 12 months by 4% during the past quarter.

**Flip variant:** same as above, except E1 reads:

- **E1′**: Economy A's central bank raised its policy rate by 50 basis points to 5.25% at its latest meeting and said further increases are possible if inflation does not keep easing.

## macro_b

Question: What is the 12-month signal for Economy B's broad equity market?

- **E1**: Economy B's central bank raised its policy rate by 75 basis points to 6.50% at its latest meeting, its third increase in a row.
- **E2**: Consumer-price inflation in Economy B rose to 6.8% a year from 5.1% three months earlier, well above the central bank's 3% target.
- **E3**: Economy B's services purchasing managers' index rose to 55.2, its strongest reading in two years.
- **E4**: Analysts cut their consensus forecast for Economy B's listed-company earnings over the next 12 months by 6% during the past quarter.

**Flip variant:** same as above, except E2 reads:

- **E2′**: Consumer-price inflation in Economy B fell to 2.1% a year from 3.8% three months earlier, below the central bank's 3% target.

## macro_c

Question: What is the 12-month signal for Economy C's broad equity market?

- **E1**: Economy C's central bank cut its policy rate by 25 basis points to 3.00% at its latest meeting.
- **E2**: Economy C's unemployment rate rose to 6.1% from 4.8% a year earlier, and payroll employment fell for a third straight quarter.
- **E3**: Spreads on Economy C's corporate bonds widened by 180 basis points over the past six months, and large lenders tightened their credit standards.
- **E4**: Analysts cut their consensus forecast for Economy C's listed-company earnings over the next 12 months by 9% during the past quarter.

**Flip variant:** same as above, except E4 reads:

- **E4′**: Analysts raised their consensus forecast for Economy C's listed-company earnings over the next 12 months by 9% during the past quarter.

