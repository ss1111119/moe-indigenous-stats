# senior-secondary-streaming Specification

## Purpose

TBD - created by archiving change 'senior-secondary-streaming'. Update Purpose after archive.

## Requirements

### Requirement: Produce senior-secondary streaming shares across academic years

The system SHALL produce a dataset in which each row represents one academic year
and one stream, carrying the academic year, the stream name, the student count, and
that stream's share of the year's total.

The streams SHALL be 普通科, 綜合高中, 專業群(職業)科, 實用技能學程 and 進修部.
The source SHALL be the existing indigenous-students-by-establishment output already
fetched by the project. The system SHALL NOT fetch any new data.

#### Scenario: Dataset is produced

- **WHEN** the build runs against the existing source
- **THEN** the dataset covers academic years 104 through 114 for all five streams

##### Example: expected shape

- **GIVEN** 11 academic years and 5 streams
- **WHEN** the dataset is built
- **THEN** it contains 55 rows

#### Scenario: Source is absent

- **WHEN** the source file does not exist
- **THEN** the system aborts, directs the operator to run the fetch step, and writes
  no output file

#### Scenario: Expected columns are missing

- **WHEN** any of the five senior-secondary columns is absent from the source
- **THEN** the system aborts and lists the column names actually present


<!-- @trace
source: senior-secondary-streaming
updated: 2026-08-11
code:
  - out/senior_stream.csv
  - README.md
  - docs/geography.html
  - docs/data/geography.json
  - export_report.py
  - build_stream.py
  - geography_template.html
-->

---
### Requirement: Select one breakdown and cross-check against the others

The source expresses the same population three ways: by establishment type, by sex,
and by ethnic group. The system SHALL compute totals from the establishment-type rows
only, and SHALL verify that the sex and ethnic-group breakdowns yield the same
senior-secondary total for every academic year.

The system SHALL NOT sum rows from more than one breakdown together, which would
triple-count the population.

#### Scenario: Breakdowns agree

- **WHEN** the three breakdowns are totalled for each academic year
- **THEN** the three totals are equal, and the build proceeds

##### Example: observed totals

| Academic year | By establishment | By sex | By ethnic group |
| ------------- | ---------------- | ------ | --------------- |
| 104           | 24,195           | 24,195 | 24,195          |
| 114           | 20,398           | 20,398 | 20,398          |

#### Scenario: Breakdowns disagree

- **WHEN** the three totals differ for any academic year
- **THEN** the system aborts and reports all three figures for that year, because a
  mismatch means a column was misread or the source changed shape


<!-- @trace
source: senior-secondary-streaming
updated: 2026-08-11
code:
  - out/senior_stream.csv
  - README.md
  - docs/geography.html
  - docs/data/geography.json
  - export_report.py
  - build_stream.py
  - geography_template.html
-->

---
### Requirement: Report shares that sum to one hundred percent

For each academic year the five stream shares SHALL be computed against the sum of
those five streams, and SHALL sum to one hundred percent.

#### Scenario: Shares are internally consistent

- **WHEN** the shares for any academic year are summed
- **THEN** the result is one hundred percent

##### Example: observed shares

| Academic year | 普通科 | 綜合高中 | 專業群(職業)科 | 實用技能學程 | 進修部 |
| ------------- | ------ | -------- | -------------- | ------------ | ------ |
| 104           | 27.6%  | 13.2%    | 41.8%          | 5.1%         | 12.4%  |
| 114           | 38.0%  | 8.9%     | 41.9%          | 5.0%         | 6.2%   |


<!-- @trace
source: senior-secondary-streaming
updated: 2026-08-11
code:
  - out/senior_stream.csv
  - README.md
  - docs/geography.html
  - docs/data/geography.json
  - export_report.py
  - build_stream.py
  - geography_template.html
-->

---
### Requirement: Cross-check the latest year against the education ladder

The system SHALL compare the latest academic year's total against the senior-secondary
row of the education-ladder summary, and SHALL report the comparison.

Documentation SHALL state that both figures originate from the same authority, so
agreement confirms only that no column was misread and does not constitute
independent cross-validation.

#### Scenario: Latest total matches the ladder

- **WHEN** the latest academic year's total is compared with the ladder's
  senior-secondary indigenous student count
- **THEN** the two figures are equal

##### Example: observed value

- **GIVEN** academic year 114
- **WHEN** the streaming total and the ladder figure are compared
- **THEN** both are 20,398


<!-- @trace
source: senior-secondary-streaming
updated: 2026-08-11
code:
  - out/senior_stream.csv
  - README.md
  - docs/geography.html
  - docs/data/geography.json
  - export_report.py
  - build_stream.py
  - geography_template.html
-->

---
### Requirement: Present streams as shares and disclose the absence of a comparison

The report page SHALL present the streaming section after the education-ladder section
and before the township receiving section, and SHALL use shares rather than counts as
the principal figure.

The page SHALL present the indigenous share alongside the corresponding share for
students generally, and SHALL make the gap between them the principal figure of the
section.

The page SHALL NOT present the indigenous series alone in a way that implies
improvement, because the indigenous academic-track share rose while the general share
rose faster, so the gap widened. Any statement about the indigenous trend SHALL be
accompanied by the general trend for the same period.

For any academic year without a general-student figure, the page SHALL show the
indigenous figure and mark the comparison as unavailable for that year.

The page SHALL state that the change in total student numbers is not interpreted, and
SHALL state that no cause is offered for the widening gap.

#### Scenario: Reader opens the streaming section

- **WHEN** the county report page is opened
- **THEN** the streaming section appears between the ladder and receiving sections,
  showing for each academic year the indigenous share, the general share, and the gap

#### Scenario: Improvement is not implied from the indigenous series alone

- **WHEN** the streaming section is inspected
- **THEN** every statement about the indigenous trend is accompanied by the general
  trend for the same period, and no wording describes the indigenous change as an
  improvement without that context

#### Scenario: A year has no general-student figure

- **WHEN** an academic year has indigenous data but no general-student data
- **THEN** the indigenous figure is shown and the comparison is marked unavailable for
  that year

#### Scenario: No cause is attributed

- **WHEN** the streaming section is inspected
- **THEN** it states that the change in total student numbers is not interpreted, and
  offers no cause for the widening gap

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