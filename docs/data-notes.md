# Data notes — what the schema cannot tell you

Injected verbatim into the agent's prompt, alongside the live schema. Everything here
is a thing that will produce a confidently wrong answer if ignored.

## Join-key contract

- **`unit_id` is the universal key.** It links content, delivered, designed, and feedback. Prefer it over anything else.
- **`session_id` is stored dash-less** (32-hex) in `sessions`, `delivered_sessions`, and `session_feedback`. Never join on a dashed UUID.
- **Course titles do NOT join across layers.** Delivered has ~148 titles, the catalogue has 63, and the names differ. Use `course_crosswalk` (`raw_title` → `catalogue_course_title`, via normalized `course_key`). Only ~50% of delivered session volume maps; the rest have `match_status='unmapped'`. A course-level count taken without the crosswalk is wrong.
- **There is no Subject entity.** `courses.stack` (11 stacks) is the closest roll-up.
- **`delivered_niat` cannot be joined to `delivered_sessions`.** It carries no `unit_id` and no `session_id`. Use it standalone for instructor / course-title / session-status questions. Do not invent a join on title+timestamp.

## Table meanings and grain

| Table | Grain | Notes |
|---|---|---|
| `delivered_sessions` | one row per session×unit scheduled | What actually ran. `start_ts`/`end_ts` are real timestamps. Sem 1 **and** Sem 2. |
| `delivered_sections` | `delivered_sessions` exploded by section | `batch_section_name` is a **comma-separated list** ("TU Batch-1-S-002, TU Batch-1-S-003"); one row can cover several sections. Use this view for per-section questions — counting `batch_section_name` counts section *groupings*, not sections. |
| `delivered_niat` | one row per planned session | Has course/instructor/status. **34% (53,643 rows) were never scheduled** — `is_scheduled = false`, `start_ts` null. Filter on `is_scheduled` or you will count sessions that never happened. |
| `designed_sequence` | one row per unit per sheet | The plan (HLID/Prod). **Semester 1 only.** May contain the same `unit_id` more than once (MRV has a "NEW BATCH" re-plan alongside the original) — dedupe by `unit_id` when counting. |
| `designed_course_plan` | one row per university×course | HLID "Student Journey": planned session counts, hours, start/end timelines. Sem 1 block only. |
| `deviation` | one row per university×unit | Pre-solved designed↔delivered join. Use this rather than re-deriving it. |
| `session_feedback_safe` | one row per institute×session×unit | Ratings and counts. **Use this, not `session_feedback`.** |
| `content_units` | one row per content item | Union of objective/coding/reading. `unit_id` repeats (many questions per unit). |
| `sessions` | distinct session→unit catalogue | Same unit set as `delivered_sessions`; largely redundant with it. |
| `universities` | 4 rows | Maps university code (MRV/Yenepoya/SGU/CDU) ↔ `institute_name`. Only these 4 have designed data. |

## The `deviation` view

`status` is one of:
- `delivered` — planned and ran. `drift_days` = actual − planned (positive = late).
- `dropped` — planned, never ran.
- `added` — ran, not found in the plan.

**`added` is unreliable, and the reason matters.** The Prod-Sequence exports have sparsely-filled Unit ID columns. Coverage of delivered units: **MRV ~82%, SGU ~65%, CDU ~42%, Yenepoya ~40%** (see `universities.prod_unit_id_coverage`). A low number means an **incomplete export**, not that staff improvised content. Never report Yenepoya/CDU `added` counts as if they were real curriculum additions.

`planned_start` is explicit only for MRV. For the other three it is **derived** as HLID semester start + (week−1)×7 — see `designed_sequence.planned_start_derived`. Derived dates are week-accurate at best, so treat small drifts (±7 days) as noise for those universities.

The view covers **Semester 1 only** and **only the 4 universities with designed data**. There is no design on file for the other 14 institutes — that is absence of data, not absence of a plan.

## Coverage caveats

- **Content covers only ~15 of 63 catalogue course titles, reaching ~19% of delivered units.** "No content found" almost always means *not ingested yet*, not *does not exist*. Say so.
- **Fine unit types are not recorded.** Delivered data has only coarse `session_type` (LECTURE/PRACTICE/EXAM) × `resource_type` (LP_RESOURCE/LP_QUIZ). Classroom quiz vs MCQ vs coding practice vs module quiz vs reading material **cannot** be distinguished from delivery data — only inferred from the content tables, for the ~19% covered.
- **~30% of content units are never scheduled** in any delivery.
- Semester windows derived from min/max session dates have a stray Jun–Jul 2026 tail (a data artifact); prefer explicit semester filters.

## How to answer

- When a caveat above materially affects the answer, **state it alongside the number**. A confident number built on a known-broken join is worse than a caveated one.
- If a question cannot be answered from this data, say so plainly. Do not substitute a near-miss and present it as the answer.
- Never invent a number that did not come from a query.
