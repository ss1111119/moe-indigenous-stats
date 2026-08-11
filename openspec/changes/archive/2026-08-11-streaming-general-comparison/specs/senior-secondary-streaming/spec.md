## MODIFIED Requirements

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
