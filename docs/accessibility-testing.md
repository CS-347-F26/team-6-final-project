# Accessibility manual assessment (I89)

**Status: in progress.** The manual Accessibility Insights for Web Assessment has
not yet been completed. Do not use this document as evidence that I89 is complete
until the assessment and final retest results below are filled in.

## Manual testing performed

- Tool: Accessibility Insights for Web, Assessment
- Browser and version: _pending_
- Date performed: _pending_
- Application URL / commit tested: _pending_
- Assessor: _pending_

Record every page and state actually assessed. Include the check or task from the
Accessibility Insights Assessment, what was done manually, and the observed
result. Include relevant flows such as the homepage map-search form, its
validation or search-results states, and other pages in the claim's scope.
Do not imply untested pages or checks were assessed.

| Page / state | Assessment check or task | Manual steps performed | Result / evidence |
|---|---|---|---|
| _pending_ | _pending_ | _pending_ | _pending_ |

## Findings, effort, and code changes

For every issue found, describe its location and impact, the work performed to
resolve it, and the GitHub issue, PR, or commit that contains the fix. If no
issues are reported, record that outcome from the completed Assessment.

| Finding and page | Resolution effort / change | GitHub issue / PR / commit | Status |
|---|---|---|---|
| Before manual testing, code inspection found no visible labels on the map-search inputs on `/`. This is not a finding from Accessibility Insights. | Added translated visible labels for place, year, latitude, and longitude, plus keyboard focus styling for the inputs. | _Add links after the change is committed or reviewed._ | _Manual retest pending._ |
| _Add findings from the completed Assessment, or record that none were reported._ | _Describe the work performed, or write "No fix required" if applicable._ | _Link related GitHub work, or write "N/A" if no change was needed._ | _Open / resolved_ |

## Final Accessibility Insights retest

- Date and application commit: _pending_
- Browser and version: _pending_
- Pages, states, and checks repeated: _pending_
- Results for each previously identified finding: _pending_
- New findings from the retest: _pending_
- Remaining issues or limitations: _pending_

## Automated regression check

On 2026-11-19, the following focused Django tests passed (2 tests):

```text
uv run python manage.py test \
  catalog.tests.HomePageTests.test_map_search_fields_have_visible_labels \
  catalog.tests.HomePageTests.test_map_search_field_labels_are_translated
```

They verify the search form has an accessible name and visible labels associated
with all four inputs in English and Spanish. This supports the code change but
does not replace the manual Accessibility Insights Assessment.
