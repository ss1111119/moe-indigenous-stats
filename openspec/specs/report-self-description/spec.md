# report-self-description Specification

## Purpose

TBD - created by archiving change 'outputs-invariants-and-page-honesty'. Update Purpose after archive.

## Requirements

### Requirement: The page deck SHALL describe the page as it currently is

The report page's opening deck SHALL NOT state a count of topics that disagrees with
the number of sections the page actually contains.

When a section is added to or removed from a report page, the deck SHALL be updated in
the same change.

#### Scenario: Deck and sections disagree

- **WHEN** the deck states a number of topics that differs from the page's section count
- **THEN** the self-description test fails, naming both numbers

#### Scenario: A section is added without updating the deck

- **WHEN** a new section is added to the template and the deck is left unchanged
- **THEN** the self-description test fails

##### Example: the state this requirement was written to correct

- **GIVEN** a deck reading 這一頁把三件事放在一起看
- **WHEN** the page contains ten sections
- **THEN** the description is stale and the test fails


<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->

---
### Requirement: The byline SHALL list every data source the page uses

The report page's byline SHALL name every data source feeding the page. When a section
introduces a new source, the byline SHALL be extended in the same change.

The check SHALL match on source keywords rather than comparing the byline verbatim, so
that rewording the byline does not fail the test.

#### Scenario: A source is missing from the byline

- **WHEN** the page draws on a source whose keyword does not appear in the byline
- **THEN** the self-description test fails naming the missing source

#### Scenario: The byline is reworded but still complete

- **WHEN** the byline text is rewritten while still naming every source
- **THEN** the test passes, because matching is by keyword and not by exact text

<!-- @trace
source: outputs-invariants-and-page-honesty
updated: 2026-08-11
code:
  - geography_template.html
  - docs/geography.html
  - README.md
  - requirements.txt
tests:
  - tests/test_invariants.py
  - tests/test_page_description.py
-->