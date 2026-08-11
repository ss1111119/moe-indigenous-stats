## ADDED Requirements

### Requirement: Decompose indigenous attainment by age band

The system SHALL produce a dataset in which each row represents one county and one
age band, carrying the reference date, county code, county name, age band,
population aged 15 and over in that band, the count holding a junior-college
qualification or higher, the corresponding share, and a flag marking bands whose
population is too small for the share to be stable.

The source SHALL be the existing adult-education output. The system SHALL NOT fetch
any new data.

#### Scenario: Decomposition is produced

- **WHEN** the build runs against the existing adult-education output
- **THEN** the dataset contains one row per county and age band, and the population
  figures sum to the national total of the source

##### Example: expected shape

- **GIVEN** 22 counties and 6 age bands
- **WHEN** the decomposition is built
- **THEN** it contains 132 rows summing to 490,336 people

#### Scenario: Source output is absent

- **WHEN** the adult-education output does not exist
- **THEN** the system aborts, directs the operator to run the upstream build first,
  and writes no output file

#### Scenario: Age bands differ from those expected

- **WHEN** the source contains age bands other than the six expected bands
- **THEN** the system aborts and lists the bands actually found, because the
  standard-population weights would not align

### Requirement: Mark small cells as unstable and exclude them from range statistics

The system SHALL mark any county-and-age-band cell whose population is below 500 as
unstable. Cells so marked SHALL be excluded when computing the spread of shares
across counties for an age band.

#### Scenario: A cell falls below the threshold

- **WHEN** a county's population in an age band is below 500
- **THEN** that cell is flagged as unstable and does not contribute to that age
  band's reported spread across counties

##### Example: threshold behaviour

| Band population | Flagged unstable | Counted in spread |
| --------------- | ---------------- | ----------------- |
| 499             | yes              | no                |
| 500             | no               | yes               |
| 4200            | no               | yes               |

### Requirement: Produce age-standardised attainment by direct standardisation

The system SHALL compute an age-standardised share for each county by weighting that
county's within-band shares by the national age structure of the indigenous
population aged 15 and over, taken from the same source and reference date.

The system SHALL produce a dataset with one row per county carrying: reference date,
county code, county name, population aged 15 and over, crude share, age-standardised
share, the difference between them, the share of population aged 65 and over, the
crude rank, the standardised rank, and the change in rank.

#### Scenario: Standardisation is identity at the national level

- **WHEN** the national crude share and the national age-standardised share are compared
- **THEN** they are equal, because standardising the standard population by its own
  age structure changes nothing

#### Scenario: An older county's rank rises after standardisation

- **WHEN** a county has an older indigenous age structure than the national average
- **THEN** its standardised share exceeds its crude share and its rank improves

##### Example: observed values at the 113-year-end reference date

| County | Crude share | Standardised share | Aged 65+ | Crude rank |
| ------ | ----------- | ------------------ | -------- | ---------- |
| 臺東縣 | 29.3%       | 33.0%              | 18.9%    | 22         |
| 花蓮縣 | 32.4%       | 34.8%              | 17.5%    | 17         |
| 臺北市 | 53.9%       | 52.3%              | 10.4%    | 1          |

### Requirement: Mark counties whose standardised share rests on unstable cells

A county's standardised share is a weighted average of its own within-band shares.
Where most of that county's population sits in cells already flagged as unstable,
the standardised share inherits that instability even though it is a single large
number.

The system SHALL flag any county for which cells flagged as unstable account for at
least half of its population aged 15 and over, and the presentation SHALL mark that
county's standardised share.

The reported spread of standardised shares across counties SHALL be verified not to
depend on flagged counties; if a flagged county holds the maximum or minimum, the
spread SHALL be reported excluding flagged counties.

#### Scenario: A county sits mostly in unstable cells

- **WHEN** unstable cells account for at least half of a county's population aged 15 and over
- **THEN** that county is flagged, and its standardised share is marked in the presentation

##### Example: flagged counties at the 113-year-end reference date

| County | Share of population in unstable cells | Flagged |
| ------ | ------------------------------------- | ------- |
| 嘉義市 | 100%                                  | yes     |
| 雲林縣 | 53%                                   | yes     |
| 新竹市 | 19%                                   | no      |

#### Scenario: Spread does not depend on flagged counties

- **WHEN** the crude and standardised spreads are computed over all counties and
  again excluding flagged counties
- **THEN** the two results agree, and the reported figures are therefore safe to state

### Requirement: Present crude and standardised shares together

The report page SHALL display both the crude share and the age-standardised share
for each county, and SHALL state which question each answers: the crude share
describes the population actually resident in the county, and the standardised share
compares counties with the effect of differing age structures removed.

The page SHALL NOT present the standardised share as a correction to the crude share,
and SHALL NOT remove or replace the existing crude figures.

#### Scenario: Reader opens the stock section

- **WHEN** the county report page is opened
- **THEN** both shares are visible for each county, each labelled with the question
  it answers

#### Scenario: Existing conclusions are preserved

- **WHEN** the stock section and the correlation scatter are inspected after this change
- **THEN** the previously published crude figures and the correlation conclusion
  remain present and unaltered

### Requirement: State the limits of standardisation

The page and the project documentation SHALL state that age structure explains only
part of the gap, giving the spread before and after standardisation, and SHALL state
that age structure is itself shaped by migration so that standardisation is a
decomposition rather than a correction and supports no causal claim.

#### Scenario: Limits are stated

- **WHEN** the age-decomposition presentation is read
- **THEN** it reports both the crude spread and the standardised spread across
  counties, and states that standardisation does not license a causal reading
