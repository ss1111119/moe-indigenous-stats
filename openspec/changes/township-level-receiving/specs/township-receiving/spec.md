## ADDED Requirements

### Requirement: Produce township-level receiving detail

The system SHALL produce a detail dataset in which each row represents one
academic year and one township (鄉鎮市區), carrying: academic year, county code,
county name, township code, township name, institution count, total student count,
indigenous student count, male indigenous student count, female indigenous
student count, and indigenous share of total students.

Township identifiers SHALL be the official administrative-district codes carried
by the source data. The system SHALL NOT derive township identifiers by inferring
them from statistical-area release codes.

#### Scenario: Detail output is generated

- **WHEN** the build script runs against a validated cache
- **THEN** the detail dataset is written with one row per year and township, and
  the row count equals the number of source records

#### Scenario: Only townships hosting institutions appear

- **WHEN** the detail dataset is inspected
- **THEN** the number of distinct townships present is far smaller than the national
  count of 368, because townships with no tertiary institution contribute no rows

##### Example: observed coverage

- **GIVEN** the source response for academic year 114
- **WHEN** the detail dataset is built
- **THEN** it contains 87 distinct townships across 21 distinct counties

### Requirement: Compute indigenous share from the same row

The system SHALL compute the indigenous share of total students as indigenous
student count divided by total student count, taking both values from the same
source row. When total student count is zero, the system SHALL emit an empty value
rather than zero.

#### Scenario: Share is computed for a township with students

- **WHEN** a township row has a non-zero total student count
- **THEN** the indigenous share is the quotient of indigenous students over total students

#### Scenario: Share is undefined for a township with no students

- **WHEN** a township row has a total student count of zero
- **THEN** the indigenous share field is empty

##### Example: share computation

| Total students | Indigenous students | Indigenous share |
| -------------- | ------------------- | ---------------- |
| 10000          | 250                 | 0.025            |
| 800            | 0                   | 0.0              |
| 0              | 0                   | (empty)          |

### Requirement: Produce a county-level summary for the latest period

The system SHALL produce a summary dataset for the latest academic year present in
the detail dataset, one row per county, carrying: county code, county name, number of
townships hosting institutions, institution count, total student count, indigenous
student count, and indigenous share of total students.

#### Scenario: Summary aggregates the latest period

- **WHEN** the build script runs over the detail dataset
- **THEN** the summary contains one row per county for the latest academic year, and
  its indigenous student totals equal the sum of that year's township rows per county

### Requirement: Present township receiving alongside county-level flow

The county report page SHALL present a township-level receiving section for the
latest period, alongside the existing county-level flow presentation.

Where the township section and the existing county-level figures differ because
their source scopes differ, the page SHALL state that the scopes differ.

The presentation SHALL mark the indigenous share as unstable for any township whose
total student count is below 1,000, so that extreme ratios from small denominators
do not dominate the display.

#### Scenario: Reader opens the county report page

- **WHEN** the report is regenerated and the county page is opened
- **THEN** the township-level receiving section is visible and shows, per township,
  the indigenous student count and the indigenous share

#### Scenario: A township has a very small denominator

- **WHEN** a township's total student count is below 1,000
- **THEN** that township's share is marked as unstable in the presentation

##### Example: stability marking at the threshold

| Total students | Indigenous students | Share | Marked unstable |
| -------------- | ------------------- | ----- | --------------- |
| 999            | 40                  | 0.040 | yes             |
| 1000           | 40                  | 0.040 | no              |
| 12000          | 300                 | 0.025 | no              |

#### Scenario: Township and county figures come from different scopes

- **WHEN** the township section's county aggregate differs from the existing
  county-level figure on the same page
- **THEN** the page states that the two figures cover different scopes

### Requirement: Carry the academic year from the source

The detail dataset SHALL carry an academic-year column whose value is taken from the
source response rather than hard-coded, so that a later change adding earlier years
does not alter the data shape, and so that a shift in the source's latest period is
reflected rather than mislabelled.

The report page SHALL state the academic year it is showing, and SHALL take that
label from the data rather than from a fixed string.

#### Scenario: Source period changes

- **WHEN** the source begins returning a later academic year than before
- **THEN** the detail dataset and the report page both report the new academic year,
  and no output states the previous year

#### Scenario: Detail dataset covers a single academic year

- **WHEN** the detail dataset is grouped by academic year
- **THEN** exactly one academic year is present, matching the source response

### Requirement: Fail rather than emit partial output

The system SHALL abort without writing output when the cache is absent or when
validation fails. The system SHALL NOT fall back to fetching data during the build
step.

#### Scenario: Build runs with no cache present

- **WHEN** the build script runs and no cached response exists
- **THEN** the system aborts with a message directing the operator to run the fetch
  step first, and writes no output file
