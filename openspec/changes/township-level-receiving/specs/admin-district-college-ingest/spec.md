## ADDED Requirements

### Requirement: Fetch administrative-district college statistics from SEGIS

The system SHALL retrieve the SEGIS dataset "行政區大專校院統計" at township
(鄉鎮市區) granularity through the administrative-district open-service endpoint
`GetAdminSTDataForOpenCode`, and SHALL cache each raw response on local disk
before any parsing occurs.

The oCode parameter SHALL be a constant declared in the fetch script, accompanied
by a comment recording the date it was obtained. The system SHALL NOT attempt to
discover the oCode at runtime.

#### Scenario: First fetch with no local cache

- **WHEN** the fetch script runs and no cached response exists
- **THEN** the system requests the endpoint, writes the raw response bytes to the
  local cache directory, and reports the number of records received

#### Scenario: Re-run with an existing cache and no network

- **WHEN** the fetch script runs, a cached response exists, and the network is unavailable
- **THEN** the system completes successfully using the cache and makes no network request

#### Scenario: The oCode is no longer valid

- **WHEN** the endpoint rejects the request or returns a payload containing no records
- **THEN** the system aborts with an error naming the oCode constant and the
  one-time manual step required to obtain a replacement
- **AND** the system MUST NOT write an empty or partial cache file that a later run
  would treat as valid

### Requirement: Verify the field mapping before use

The system SHALL declare the mapping from response field identifiers to their
statistical meanings as an explicit constant, and SHALL validate the response
against that mapping before producing any output. The system SHALL NOT rely on
the field order shown in platform metadata pages.

The mapping SHALL cover at minimum: number of institutions, total student count,
indigenous student count, male indigenous student count, and female indigenous
student count.

#### Scenario: Response field count does not match the declared mapping

- **WHEN** the parsed response contains a different set of field identifiers than
  the declared mapping
- **THEN** the system aborts, prints the field identifiers actually received, and
  writes no output file

#### Scenario: Sex components do not sum to the indigenous total

- **WHEN** any record has male indigenous students plus female indigenous students
  not equal to indigenous students
- **THEN** the system aborts and reports the year and township of the first
  offending record

##### Example: sex-component validation

| Indigenous total | Male | Female | Result                       |
| ---------------- | ---- | ------ | ---------------------------- |
| 120              | 70   | 50     | accepted                     |
| 120              | 70   | 49     | aborted, record identified   |
| 0                | 0    | 0      | accepted                     |

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

### Requirement: Record provenance and non-independence

The system SHALL record, in the fetch script documentation, that the originating
authority of this dataset is the Ministry of Education statistics office, the same
source as the publication tables already used by the project. Documentation
produced for this dataset SHALL NOT describe the comparison with those tables as
cross-validation by an independent source.

#### Scenario: Documentation review

- **WHEN** a reader consults the fetch script documentation or the generated report
  section for this dataset
- **THEN** the same-source relationship is stated explicitly, and the stated value
  of the dataset is its township granularity and multi-year coverage
