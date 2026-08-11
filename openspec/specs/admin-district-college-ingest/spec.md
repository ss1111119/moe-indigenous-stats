# admin-district-college-ingest Specification

## Purpose

TBD - created by archiving change 'township-level-receiving'. Update Purpose after archive.

## Requirements

### Requirement: Fetch administrative-district college statistics from SEGIS

The system SHALL retrieve, for each of four education levels — primary school
(國小), junior high school (國中), senior secondary school (高中職) and tertiary
institutions (大專) — the corresponding SEGIS administrative-district dataset at
township (鄉鎮市區) granularity through the open-service endpoint
`GetAdminSTDataForOpenCode`, and SHALL cache each raw response on local disk
before any parsing occurs.

A single request per level SHALL cover the whole country. The system SHALL NOT
issue one request per county.

Each level's oCode SHALL be a constant declared in the fetch script alongside the
level identifier, accompanied by a comment recording the date it was obtained.
The system SHALL NOT attempt to discover any oCode at runtime.

The levels SHALL be driven from a single declared list. The system SHALL NOT
duplicate the fetch, validation or abort logic per level.

#### Scenario: First fetch with no local cache

- **WHEN** the fetch script runs and no cached response exists for a level
- **THEN** the system requests that level's endpoint, writes the raw response bytes
  to the local cache directory under a filename identifying the level, and reports
  the level and the number of records received

#### Scenario: Re-run with an existing cache and no network

- **WHEN** the fetch script runs, cached responses exist for every level, and the
  network is unavailable
- **THEN** the system completes successfully using the caches and makes no network request

#### Scenario: The oCode is no longer valid

- **WHEN** the endpoint rejects the request for a level, or returns a payload
  containing no records
- **THEN** the system aborts with an error naming the affected level, its oCode
  constant, and the one-time manual step required to obtain a replacement
- **AND** the system MUST NOT write an empty or partial cache file that a later run
  would treat as valid

#### Scenario: One level fails while others succeed

- **WHEN** any single level fails to fetch or validate
- **THEN** the system reports which level failed
- **AND** the system MUST NOT produce ladder output built from the remaining levels,
  because a ladder missing a rung misstates the progression


<!-- @trace
source: education-ladder-township
updated: 2026-08-11
code:
  - out/ladder_township.csv
  - geography_template.html
  - README.md
  - build_ladder.py
  - fetch_segis_college.py
  - build_receiving.py
  - out/ladder_summary.csv
  - docs/data/geography.json
  - docs/geography.html
  - export_report.py
-->

---
### Requirement: Verify the field mapping before use

The system SHALL declare the required response field names as an explicit constant
and SHALL read every value by field name. The system SHALL NOT read values by their
position within the response.

The required names SHALL be: `INFO_TIME`, `COUNTY_ID`, `COUNTY`, `TOWN_ID`, `TOWN`,
`SCH_CNT`, `STU_CNT`, `NA_STU_CNT`, `NA_STU_M_CNT`, `NA_STU_F_CNT`.

The same required names SHALL apply to all four education levels, and the
validation SHALL be implemented once and shared across levels.

#### Scenario: A required field is absent from the response

- **WHEN** a level's response column list does not contain every required field name
- **THEN** the system aborts, names the affected level, prints which required names
  are missing and which names were actually received, and writes no output file

#### Scenario: The response gains additional fields

- **WHEN** a level's response contains fields beyond the required names
- **THEN** the system proceeds normally, because values are read by name and extra
  fields cannot shift the position of required ones

#### Scenario: Sex components do not sum to the indigenous total

- **WHEN** any record in any level has male indigenous students plus female
  indigenous students not equal to indigenous students
- **THEN** the system aborts and reports the education level, academic year and
  township of the first offending record


<!-- @trace
source: education-ladder-township
updated: 2026-08-11
code:
  - out/ladder_township.csv
  - geography_template.html
  - README.md
  - build_ladder.py
  - fetch_segis_college.py
  - build_receiving.py
  - out/ladder_summary.csv
  - docs/data/geography.json
  - docs/geography.html
  - export_report.py
-->

---
### Requirement: Reconcile county totals against the published statistics

The system SHALL aggregate township records to county level and compare the
indigenous student totals against the ministry publication table whose scope
excludes religious research colleges and open-university affiliated continuing
schools. The system SHALL report per-county differences rather than passing
silently.

#### Scenario: County totals reconcile within the explainable range

- **WHEN** aggregated county totals differ from the publication table only by
  amounts attributable to the documented scope difference
- **THEN** the system reports the comparison as reconciled and records the observed
  difference magnitude in the output

#### Scenario: County totals differ beyond the explainable range

- **WHEN** aggregated county totals differ from the publication table by amounts
  that the documented scope difference does not account for
- **THEN** the system prints the per-county differences and SHALL NOT report the
  comparison as reconciled


<!-- @trace
source: township-level-receiving
updated: 2026-08-11
code:
  - README.md
  - out/receiving_township.csv
  - out/receiving_township_summary.csv
  - geography_template.html
  - site_style.css
  - docs/style.css
  - fetch_segis_college.py
  - .spectra.yaml
  - build_receiving.py
  - build_education.py
  - CLAUDE.md
  - STATCatalog.pdf
  - docs/geography.html
  - docs/data/geography.json
  - export_report.py
-->

---
### Requirement: Record provenance and non-independence

The system SHALL record, in the fetch script documentation, that the originating
authority of every one of these datasets is the Ministry of Education statistics
office, the same source as the publication tables already used by the project.
Documentation produced for these datasets SHALL NOT describe comparisons with those
tables, or agreement between the four levels, as cross-validation by an independent
source.

#### Scenario: Documentation review

- **WHEN** a reader consults the fetch script documentation or the generated report
  section for these datasets
- **THEN** the same-source relationship is stated explicitly, and the stated value
  of the datasets is their township granularity

<!-- @trace
source: education-ladder-township
updated: 2026-08-11
code:
  - out/ladder_township.csv
  - geography_template.html
  - README.md
  - build_ladder.py
  - fetch_segis_college.py
  - build_receiving.py
  - out/ladder_summary.csv
  - docs/data/geography.json
  - docs/geography.html
  - export_report.py
-->