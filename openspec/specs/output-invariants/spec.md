# output-invariants Specification

## Purpose

TBD - created by archiving change 'outputs-invariants-and-page-honesty'. Update Purpose after archive.

## Requirements

### Requirement: Assert cross-file invariants on the committed outputs

The project SHALL carry an executable test suite that asserts the relationships
between committed output files. The suite SHALL read only the committed outputs and
the report templates, and SHALL NOT read the unversioned raw data directory, so that
it runs immediately after a clone without network access.

#### Scenario: Suite runs on a fresh clone

- **WHEN** the test suite is run with no network and without executing the build pipeline
- **THEN** every check completes using only the committed outputs and templates

#### Scenario: A cross-file relationship breaks

- **WHEN** one output file's figures change so that it no longer agrees with the file
  it is constrained against
- **THEN** the corresponding test fails

##### Example: constrained relationships

| Relationship                                                     | Expected |
| ---------------------------------------------------------------- | -------- |
| Township receiving total equals the A1-6a county total            | 25,613   |
| Senior-secondary stream total equals the ladder's senior row      | 20,398   |
| Adult education total equals the age-decomposition total          | 490,336  |


<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->

---
### Requirement: Pin the headline figures as explicit constants

Expected values SHALL be written as constants in the test suite, each accompanied by a
note recording where the figure comes from. The suite SHALL NOT derive an expected
value from another output file in a way that would pass when both files are wrong
together.

#### Scenario: Both sides of a comparison change together

- **WHEN** two outputs are both regenerated with the same underlying error
- **THEN** the pinned constant still fails, because it does not depend on either file

#### Scenario: A new academic year arrives

- **WHEN** the sources are updated to a later academic year and the figures legitimately change
- **THEN** the tests fail, and each failure message instructs the operator to confirm
  the new figures before updating the constant


<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->

---
### Requirement: Assert the ladder counts descend

The suite SHALL assert that the count of townships hosting each education level is
367, 357, 206 and 87 for primary, junior, senior and tertiary respectively, and that
the sequence strictly decreases.

#### Scenario: Ladder counts are checked

- **WHEN** the ladder summary is read
- **THEN** the four counts match the pinned values and each is smaller than the one before


<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->

---
### Requirement: Assert standardisation is identity at the national level

The suite SHALL assert that the national crude share and the national age-standardised
share agree to two decimal places, because standardising the standard population by its
own age structure changes nothing. A discrepancy indicates the weights are wrong.

#### Scenario: Weights are correct

- **WHEN** the standardised output is read and the national figures compared
- **THEN** the two shares are equal to two decimal places


<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->

---
### Requirement: Assert row counts and share totals

The suite SHALL assert the row count of each output whose shape is determined by the
data, and SHALL assert that shares within each grouping sum to one hundred percent
within a rounding tolerance of 0.05.

#### Scenario: Row counts are checked

- **WHEN** the outputs are read
- **THEN** their row counts match the pinned values

##### Example: pinned row counts

| Output                      | Rows |
| --------------------------- | ---- |
| receiving_township.csv      | 87   |
| ladder_township.csv         | 1017 |
| attainment_by_age.csv       | 132  |
| senior_stream.csv           | 55   |
| senior_stream_compare.csv   | 55   |

#### Scenario: Shares within a grouping do not sum to one hundred

- **WHEN** any grouping's shares sum to a value outside one hundred plus or minus 0.05
- **THEN** the corresponding test fails naming the grouping


<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->

---
### Requirement: Assert the streaming gap widened

The suite SHALL assert that the academic-track gap between indigenous and general
students is -11.56 percentage points in academic year 105 and -13.69 in 114, and that
the later figure is larger in absolute value.

#### Scenario: Gap direction is checked

- **WHEN** the comparison output is read
- **THEN** both pinned gaps match and the later one is the larger in absolute value

<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->