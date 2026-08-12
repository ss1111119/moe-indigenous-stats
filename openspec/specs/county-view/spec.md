# county-view Specification

## Purpose

TBD - created by archiving change 'county-view'. Update Purpose after archive.

## Requirements

### Requirement: Assemble one row per county from existing outputs

The system SHALL produce a dataset with one row per county, assembled from the
existing flow, ladder, receiving and standardised-attainment outputs. It SHALL NOT
fetch any new data and SHALL NOT read the unversioned raw data directory.

Each row SHALL carry: county code, county name, students by birth registration,
students by school location, net flow, the enrolment-to-registration ratio, the count
of townships in that county hosting each of the four education levels, the count of
townships receiving indigenous tertiary students, the number of such students, the
crude and age-standardised tertiary-attainment shares, and a small-denominator flag.

#### Scenario: Dataset is assembled

- **WHEN** the build runs against the existing outputs
- **THEN** it produces one row for each of the 22 counties

#### Scenario: An upstream output is missing

- **WHEN** any of the four upstream outputs does not exist
- **THEN** the system aborts naming the missing file and the build script that
  produces it, and writes no output

#### Scenario: A county has no tertiary institution

- **WHEN** a county appears in the flow data but has no rows in the receiving output
- **THEN** its receiving township count and receiving student count are zero rather
  than absent

##### Example: observed counties

| County | Townships per level | Enrolment ratio | Receiving townships | Crude → standardised |
| ------ | ------------------- | --------------- | ------------------- | -------------------- |
| 臺東縣 | 16 / 14 / 4 / 1     | 20.3%           | 1 (792 students)    | 29.3% → 33.0%        |
| 新北市 | 29 / 29 / 22 / 13   | 142.8%          | 13                  | 39.1% → 37.0%        |
| 連江縣 | —                   | —               | 0 (0 students)      | —                    |


<!-- @trace
source: county-view
updated: 2026-08-12
code:
  - docs/geography.html
  - docs/data/geography.json
  - geography_template.html
  - export_report.py
  - out/county_view.csv
  - README.md
  - build_county.py
tests:
  - tests/test_page_description.py
  - tests/test_invariants.py
-->

---
### Requirement: Flag counties whose ratios rest on a tiny denominator

The system SHALL flag any county whose students-by-birth-registration count is below
200. The flag SHALL apply to the ratios — the enrolment-to-registration ratio and the
attainment shares — while the underlying counts remain displayed unflagged.

Flagged counties SHALL NOT be removed from the dataset or from the page's county
chooser, because their counts are real even where their ratios are not informative.

#### Scenario: A county has very few students

- **WHEN** a county's students-by-birth-registration count is below 200
- **THEN** that county is flagged, and the presentation marks its ratios

##### Example: flagged counties at academic year 114

| County | Students by birth registration | Flagged |
| ------ | ------------------------------ | ------- |
| 連江縣 | 4                              | yes     |
| 雲林縣 | 166                            | yes     |
| 新竹市 | 215                            | no      |

#### Scenario: Exactly five counties are flagged

- **WHEN** the flag is applied across all counties
- **THEN** 連江縣, 金門縣, 澎湖縣, 嘉義市 and 雲林縣 are flagged and no others are


<!-- @trace
source: county-view
updated: 2026-08-12
code:
  - docs/geography.html
  - docs/data/geography.json
  - geography_template.html
  - export_report.py
  - out/county_view.csv
  - README.md
  - build_county.py
tests:
  - tests/test_page_description.py
  - tests/test_invariants.py
-->

---
### Requirement: Township counts per level do not increase with level

Within a county, the count of townships hosting each education level SHALL not
increase as the level rises, because a township hosting a higher level is counted at
every level it hosts.

#### Scenario: Counts are checked per county

- **WHEN** each county's four counts are read in level order
- **THEN** each count is less than or equal to the one before it


<!-- @trace
source: county-view
updated: 2026-08-12
code:
  - docs/geography.html
  - docs/data/geography.json
  - geography_template.html
  - export_report.py
  - out/county_view.csv
  - README.md
  - build_county.py
tests:
  - tests/test_page_description.py
  - tests/test_invariants.py
-->

---
### Requirement: Receiving figures agree with the township receiving output

For every county, the receiving township count SHALL equal the number of that county's
rows in the township receiving output, and the receiving student count SHALL equal the
sum of that county's indigenous student counts in the same output.

#### Scenario: Receiving figures reconcile

- **WHEN** the assembled dataset is compared against the township receiving output
- **THEN** both figures agree for every county


<!-- @trace
source: county-view
updated: 2026-08-12
code:
  - docs/geography.html
  - docs/data/geography.json
  - geography_template.html
  - export_report.py
  - out/county_view.csv
  - README.md
  - build_county.py
tests:
  - tests/test_page_description.py
  - tests/test_invariants.py
-->

---
### Requirement: Present a county chooser as an entry point, not an appendix

The report page SHALL present a county section positioned before the per-county
trend section, allowing the reader to select one county and see that county's flow,
ladder, receiving and attainment figures together.

The section SHALL NOT reproduce the detailed charts that already exist in later
sections; it SHALL present summary figures and a compact per-level township chart.

The section SHALL state that senior-secondary streaming has no county breakdown, so
that its absence reads as a documented limit rather than an omission.

The section's explanatory note SHALL be at most 150 characters, because the page's
explanatory text already totals far more than the sibling page's and further growth
makes readers skip the caveats that prevent misreading.

#### Scenario: Reader selects a county

- **WHEN** the reader chooses a county
- **THEN** that county's flow, per-level township counts, receiving figures and
  attainment shares are shown together

#### Scenario: Section placement

- **WHEN** the page's sections are read in document order
- **THEN** the county section appears before the per-county trend section

#### Scenario: Streaming absence is explained

- **WHEN** the county section is inspected
- **THEN** it states that streaming has no county breakdown

#### Scenario: A flagged county is selected

- **WHEN** the reader selects a county flagged for a tiny denominator
- **THEN** its ratios are marked and its underlying count is visible alongside them

<!-- @trace
source: county-view
updated: 2026-08-12
code:
  - docs/geography.html
  - docs/data/geography.json
  - geography_template.html
  - export_report.py
  - out/county_view.csv
  - README.md
  - build_county.py
tests:
  - tests/test_page_description.py
  - tests/test_invariants.py
-->