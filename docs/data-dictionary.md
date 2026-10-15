# Data dictionary

## household_visit

| Column | Type | Source (CommCare form JSON) | Notes |
|---|---|---|---|
| form_id | TEXT, PK | `id` | Unique submission ID. Upsert key. |
| case_id | TEXT | `form.case.@case_id` | Household case the visit belongs to. |
| user_id | TEXT | `metadata.userID` | Mobile worker who submitted. |
| site | TEXT | `form.site` | Visit location. Required. |
| household_size | INTEGER | `form.household_size` | Valid range 1 to 30. |
| children_under_5 | INTEGER | `form.children_under_5` | Must not exceed household_size. |
| visit_date | TEXT (ISO date) | `form.visit_date` | Must not be after received_on. |
| received_on | TEXT (ISO datetime) | `received_on` | Server receipt time. Drives incremental sync. |

## dq_issue

| Column | Description |
|---|---|
| id | Auto ID |
| form_id | Offending record |
| rule | Rule name: `missing_site`, `invalid_household_size`, `children_exceed_household`, `visit_after_received` |
| detail | Human-readable reason |

## sync_state

Key/value store. `last_received_on` is the high-water mark for incremental sync.
