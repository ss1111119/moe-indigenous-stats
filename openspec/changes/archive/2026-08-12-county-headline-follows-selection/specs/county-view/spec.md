## MODIFIED Requirements

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

The section's heading SHALL name the selected county and state that county's own
count of townships hosting primary schools and tertiary institutions, so that the
heading describes what is on screen rather than a county the reader did not choose.
The heading SHALL be derived from the same assembled figures the section already
displays, and SHALL NOT require any additional data.

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

#### Scenario: The heading follows the selection

- **WHEN** the reader selects a county
- **THEN** the heading names that county and states its own two township counts

##### Example: headings at academic year 114

| County | Townships with primary → tertiary | Heading                                              |
| ------ | --------------------------------- | ---------------------------------------------------- |
| 臺東縣 | 16 → 1                            | 臺東縣 16 個鄉鎮有國小，只有 1 個有大專校院          |
| 臺北市 | 12 → 9                            | 臺北市 12 個鄉鎮有國小，只有 9 個有大專校院          |
| 連江縣 | 4 → 0                             | 連江縣 4 個鄉鎮有國小，沒有一個有大專校院            |

#### Scenario: A county hosts no tertiary institution

- **WHEN** the selected county's tertiary township count is zero
- **THEN** the heading states that none of its townships host a tertiary institution,
  rather than stating that only zero of them do

#### Scenario: The default selection is unchanged

- **WHEN** the page is first loaded and no county has been chosen
- **THEN** the heading reads exactly as it did before this change, because the
  default selection is the same county
