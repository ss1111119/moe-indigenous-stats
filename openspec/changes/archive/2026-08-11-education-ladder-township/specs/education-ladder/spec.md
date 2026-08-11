## ADDED Requirements

### Requirement: Produce the education-ladder detail across four levels

The system SHALL produce a detail dataset in which each row represents one
education level and one township, carrying: academic year, education level, number
of school years in that level, county code, county name, township code, township
name, institution count, total student count, indigenous student count, male
indigenous student count and female indigenous student count.

The education level values SHALL be 國小, 國中, 高中職 and 大專.

#### Scenario: Detail covers every level

- **WHEN** the ladder build runs against validated caches for all four levels
- **THEN** the detail dataset contains rows for all four education levels, and the
  row count for the tertiary level equals the row count of the existing township
  receiving detail

### Requirement: Carry the number of school years to block invalid comparison

Each row SHALL carry the number of school years covered by its education level:
6 for 國小, 3 for 國中, 3 for 高中職. For 大專 the value SHALL be empty, because
the level spans two-year, four-year and five-year programmes together with
postgraduate study and therefore has no single figure.

This column exists so that a reader who obtains only the CSV, without the report
page, still sees why student counts are not comparable across levels.

#### Scenario: School-year column is populated

- **WHEN** the detail dataset is inspected
- **THEN** rows carry 6, 3, 3 and an empty value for 國小, 國中, 高中職 and 大專
  respectively

##### Example: school years by level

| Education level | School years |
| --------------- | ------------ |
| 國小            | 6            |
| 國中            | 3            |
| 高中職          | 3            |
| 大專            | (empty)      |

### Requirement: Produce the ladder summary as a descending township count

The system SHALL produce a summary dataset with one row per education level,
ordered from the lowest level upward, carrying: academic year, education level,
number of school years, count of townships hosting that level, count of townships
having at least one indigenous student at that level, count of counties covered,
and total indigenous students.

The count of townships hosting each level SHALL be the primary ladder measure,
because each township is counted once per level regardless of how many school
years that level spans.

#### Scenario: Township counts descend with level

- **WHEN** the summary dataset is read in level order
- **THEN** the count of townships hosting each level decreases from 國小 through 大專

##### Example: observed ladder for academic year 114

| Education level | Townships hosting | Townships with indigenous students | Indigenous students |
| --------------- | ----------------- | ---------------------------------- | ------------------- |
| 國小            | 367               | 363                                | 52,051              |
| 國中            | 357               | 339                                | 24,513              |
| 高中職          | 206               | 197                                | 20,398              |
| 大專            | 87                | 86                                 | 25,613              |

### Requirement: Require a single shared academic year across levels

The system SHALL verify that all four levels report the same academic year before
producing any output. Levels drawn from different academic years SHALL NOT be
placed on the same ladder.

#### Scenario: Levels disagree on academic year

- **WHEN** the cached responses do not all carry the same academic year
- **THEN** the system aborts, lists the academic year found for each level, and
  writes no output file

### Requirement: Present the ladder without inviting cross-level division

The report page SHALL present the ladder using the count of townships hosting each
level as the principal figure, and SHALL state that the four levels are a
cross-section at one point in time rather than one cohort followed over time.

The page SHALL state that student counts are not comparable across levels because
the levels span different numbers of school years. The page SHALL NOT display any
figure derived by dividing one level's student count by another's.

#### Scenario: Reader opens the ladder section

- **WHEN** the county report page is opened
- **THEN** the ladder section shows the township counts for the four levels and
  states both the cross-section caveat and the differing-school-years caveat

#### Scenario: No progression rate is shown

- **WHEN** the ladder section is inspected
- **THEN** no percentage or ratio computed between two education levels appears
