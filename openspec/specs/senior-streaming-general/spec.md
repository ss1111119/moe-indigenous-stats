# senior-streaming-general Specification

## Purpose

TBD - created by archiving change 'streaming-general-comparison'. Update Purpose after archive.

## Requirements

### Requirement: Fetch general-student senior-secondary programme data per academic year

The system SHALL retrieve, for each academic year from 105 through 114, the ministry's
senior-secondary school-level file broken down by programme, and SHALL cache each
year's raw response on local disk before parsing.

The system SHALL request the CSV form for every year that offers it and the XLSX form
only where CSV is unavailable.

#### Scenario: First fetch with no local cache

- **WHEN** the fetch script runs and no cache exists
- **THEN** the system retrieves one file per academic year and reports each year and
  its byte count

#### Scenario: Re-run with a complete cache and no network

- **WHEN** every year is cached and the network is unavailable
- **THEN** the system completes successfully and makes no network request

#### Scenario: A single year fails

- **WHEN** any academic year cannot be retrieved
- **THEN** the system aborts naming that academic year, and writes no partial cache
  file for it


<!-- @trace
source: streaming-general-comparison
updated: 2026-08-11
code:
  - fetch_senior.py
  - README.md
  - build_stream.py
  - docs/geography.html
  - geography_template.html
  - docs/data/geography.json
  - export_report.py
  - out/senior_stream_compare.csv
-->

---
### Requirement: Normalise the per-year format differences in one place

The source changes shape across years. The system SHALL declare the differences as an
explicit mapping and SHALL apply it in a single normalisation step.

The mapping SHALL cover at minimum: the programme column named 等級名稱, 學程名稱 or
學程(等級)名稱; and the category names 進修部(學校) versus 進修部, and
專業群(職業)科 versus 專業群科.

The system SHALL detect each CSV's character encoding by trying UTF-8 with BOM and
then Big5, and SHALL detect its delimiter from whether the first line contains a tab.
The system SHALL NOT hard-code which academic year uses which encoding or delimiter.
Where neither encoding decodes a file, the system SHALL abort naming that academic
year rather than attempting further guesses.

After normalisation the system SHALL verify that only the five expected programme
categories remain, and SHALL abort listing any unexpected category together with its
academic year.

#### Scenario: An older year uses the earlier column name

- **WHEN** a year's file names the programme column 等級名稱 or 學程名稱
- **THEN** normalisation maps it to the same field as 學程(等級)名稱

#### Scenario: A year differs in encoding and delimiter

- **WHEN** a year's CSV is encoded in Big5 and separated by tabs while other years are
  UTF-8 and comma-separated
- **THEN** detection resolves both correctly and that year parses to the same column
  set as the others

##### Example: observed per-year formats

| Academic year | Encoding | Delimiter |
| ------------- | -------- | --------- |
| 110           | UTF-8    | comma     |
| 111           | Big5     | tab       |
| 112           | UTF-8    | comma     |

#### Scenario: An unexpected category appears

- **WHEN** normalisation produces a category outside the five expected ones
- **THEN** the system aborts, naming the category and the academic year, and writes no
  output

##### Example: category normalisation

| Source value      | Normalised value |
| ----------------- | ---------------- |
| 進修部(學校)      | 進修部           |
| 專業群(職業)科    | 專業群(職業)科   |
| 專業群科          | 專業群(職業)科   |
| 附設國中部        | (excluded)       |


<!-- @trace
source: streaming-general-comparison
updated: 2026-08-11
code:
  - fetch_senior.py
  - README.md
  - build_stream.py
  - docs/geography.html
  - geography_template.html
  - docs/data/geography.json
  - export_report.py
  - out/senior_stream_compare.csv
-->

---
### Requirement: Derive student counts by summing grade columns

The system SHALL compute each row's student count by summing the per-grade male and
female columns together with the extended-study columns, for every academic year and
both file formats.

The system SHALL NOT read a student-count column supplied by the file, even where one
exists, so that all years share one definition.

Where a year offers both formats, the system SHALL verify that the two files yield the
same total and SHALL abort if they differ.

#### Scenario: Counts are derived consistently

- **WHEN** a year's rows are parsed
- **THEN** each row's student count equals the sum of its per-grade and extended-study
  columns

#### Scenario: The two formats disagree

- **WHEN** a year offers both CSV and XLSX and their totals differ
- **THEN** the system aborts and reports both totals


<!-- @trace
source: streaming-general-comparison
updated: 2026-08-11
code:
  - fetch_senior.py
  - README.md
  - build_stream.py
  - docs/geography.html
  - geography_template.html
  - docs/data/geography.json
  - export_report.py
  - out/senior_stream_compare.csv
-->

---
### Requirement: Exclude the affiliated junior-high programme

The affiliated junior-high programme (附設國中部) SHALL be excluded from all
senior-secondary totals and shares, because it is lower-secondary education and has no
counterpart on the indigenous side.

#### Scenario: Affiliated junior-high rows are dropped

- **WHEN** the general-student totals are computed
- **THEN** rows for the affiliated junior-high programme contribute nothing

##### Example: observed national total

- **GIVEN** academic year 114 after excluding the affiliated junior-high programme
- **WHEN** the five programme categories are summed
- **THEN** the total is 532,256


<!-- @trace
source: streaming-general-comparison
updated: 2026-08-11
code:
  - fetch_senior.py
  - README.md
  - build_stream.py
  - docs/geography.html
  - geography_template.html
  - docs/data/geography.json
  - export_report.py
  - out/senior_stream_compare.csv
-->

---
### Requirement: Produce the indigenous-versus-general comparison

The system SHALL produce a dataset in which each row represents one academic year and
one programme, carrying the academic year, the programme, the indigenous count and
share, the general count and share, and the gap in percentage points defined as the
indigenous share minus the general share.

Academic years with no general-student data SHALL appear with the indigenous figures
present and the general and gap fields empty.

The existing indigenous-only output SHALL remain unchanged in both columns and values.

#### Scenario: Comparison dataset is produced

- **WHEN** the build runs against the caches and the existing indigenous output
- **THEN** the dataset covers academic years 104 through 114 for all five programmes

##### Example: observed comparison

| Academic year | Programme | Indigenous share | General share | Gap   |
| ------------- | --------- | ---------------- | ------------- | ----- |
| 105           | 普通科    | 29.0%            | 40.5%         | -11.6 |
| 114           | 普通科    | 38.0%            | 51.7%         | -13.7 |

#### Scenario: A year lacks general data

- **WHEN** academic year 104 is written
- **THEN** its indigenous figures are present and its general and gap fields are empty

#### Scenario: Shares are internally consistent

- **WHEN** either side's five shares are summed for any academic year with data
- **THEN** the result is one hundred percent


<!-- @trace
source: streaming-general-comparison
updated: 2026-08-11
code:
  - fetch_senior.py
  - README.md
  - build_stream.py
  - docs/geography.html
  - geography_template.html
  - docs/data/geography.json
  - export_report.py
  - out/senior_stream_compare.csv
-->

---
### Requirement: Report the direction of the gap without explaining it

The system SHALL report whether the academic-track gap widened or narrowed between the
first and last comparable academic years.

Documentation and presentation SHALL state that no cause is offered for the direction
of the gap, because the project holds no data able to separate admissions policy,
school supply, household economics or reporting practice.

Documentation SHALL also state that both sides originate from the same authority, so
agreement between them is not independent cross-validation.

#### Scenario: Gap direction is reported

- **WHEN** the build completes
- **THEN** it reports the academic-track gap for the first and last comparable years
  and states which way it moved

##### Example: observed direction

- **GIVEN** academic years 105 and 114
- **WHEN** the academic-track gaps are compared
- **THEN** the gap moved from -11.6 to -13.7 percentage points, that is, it widened

<!-- @trace
source: streaming-general-comparison
updated: 2026-08-11
code:
  - fetch_senior.py
  - README.md
  - build_stream.py
  - docs/geography.html
  - geography_template.html
  - docs/data/geography.json
  - export_report.py
  - out/senior_stream_compare.csv
-->