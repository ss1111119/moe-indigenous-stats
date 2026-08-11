## MODIFIED Requirements

### Requirement: Present township receiving alongside county-level flow

The county report page SHALL present a township-level receiving section for the
latest period, alongside the existing county-level flow presentation.

The page SHALL present the education-ladder section before the township receiving
section, so that the count of townships hosting tertiary institutions is read
against the counts for the lower levels rather than in isolation.

Where the township section and the existing county-level figures differ because
their source scopes differ, the page SHALL state that the scopes differ.

The presentation SHALL mark the indigenous share as unstable for any township whose
total student count is below 1,000, so that extreme ratios from small denominators
do not dominate the display.

#### Scenario: Reader opens the county report page

- **WHEN** the report is regenerated and the county page is opened
- **THEN** the township-level receiving section is visible and shows, per township,
  the indigenous student count and the indigenous share

#### Scenario: Ladder precedes receiving

- **WHEN** the county page is opened
- **THEN** the education-ladder section appears above the township receiving section
  in document order

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
