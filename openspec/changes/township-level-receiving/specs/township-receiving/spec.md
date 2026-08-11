## ADDED Requirements

### Requirement: Produce township-level receiving detail

The system SHALL produce a detail dataset in which each row represents one
year and one township (鄉鎮市區), carrying: year, county code, county name,
township code, township name, institution count, total student count,
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

- **WHEN** the detail dataset is inspected for any single year
- **THEN** the number of distinct townships present is smaller than the national
  township count, because townships with no tertiary institution contribute no rows

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

The system SHALL produce a summary dataset for the latest available period, one row
per county, carrying: county code, county name, number of townships hosting
institutions, institution count, total student count, indigenous student count, and
indigenous share of total students.

#### Scenario: Summary aggregates the latest period only

- **WHEN** the build script runs over a detail dataset spanning multiple years
- **THEN** the summary contains rows for the latest period only, and its indigenous
  student totals equal the sum of that period's township rows per county

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

### Requirement: Retain multi-year data without presenting it

The system SHALL retain every year covered by the fetch in the detail dataset, even
though the report page presents only the latest period. A later change SHALL be able
to build a time series from the detail dataset without re-fetching.

#### Scenario: Detail dataset spans all fetched years

- **WHEN** the detail dataset is grouped by year
- **THEN** every year present in the cached source appears, not only the latest one

### Requirement: Fail rather than emit partial output

The system SHALL abort without writing output when the cache is absent or when
validation fails. The system SHALL NOT fall back to fetching data during the build
step.

#### Scenario: Build runs with no cache present

- **WHEN** the build script runs and no cached response exists
- **THEN** the system aborts with a message directing the operator to run the fetch
  step first, and writes no output file
