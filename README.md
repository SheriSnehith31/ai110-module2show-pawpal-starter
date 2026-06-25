# PawPal+ (Module 2 Project)

> CodePath AI110 · Project 2 · Snehith Sheri

A smart pet care management system that helps owners keep their pets' daily routines on track — feedings, walks, medications, and appointments — organized through algorithmic scheduling logic and a polished Streamlit dashboard.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time, priority, scheduling conflicts)
- Produce a daily plan sorted chronologically and explain conflicts
- Support recurring tasks that auto-schedule the next occurrence on completion

---

## What You Will Build

Your final app:

- Lets a user enter owner + pet info
- Lets a user add/edit tasks with time, frequency, and due date
- Generates a daily schedule sorted chronologically
- Displays conflict warnings when two tasks clash for the same pet
- Tracks completion and auto-generates next recurrences for Daily/Weekly tasks
- Includes a full pytest suite verifying all scheduling behaviors

---

## Getting Started

### Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install streamlit pytest
```

### How to Run the CLI Demo

```bash
python -X utf8 main.py
```

### How to Run the Streamlit Dashboard

```bash
streamlit run app.py
```

### How to Run Tests

```bash
python -m pytest tests/test_pawpal.py -v
```

---

## Project Structure

```
pawpal_system.py        # All backend logic — Owner, Pet, Task, Scheduler
app.py                  # Streamlit UI (presentation only)
main.py                 # CLI demo
tests/
  test_pawpal.py        # 33 pytest tests
diagrams/
  uml_draft.mmd         # Phase 1 Mermaid diagram
  uml_final.mmd         # Phase 6 final Mermaid diagram
.streamlit/
  config.toml           # Dark SaaS theme
```

---

## Features

| Feature | Method | Notes |
|---|---|---|
| Chronological sorting | `Scheduler.get_sorted_schedule()` | Lambda key on `"HH:MM"` string — lexicographic = chronological |
| Pet / status filtering | `Scheduler.filter_tasks()` | Sidebar filters: All Pets, Pending, Completed |
| Conflict detection | `Scheduler.detect_conflicts()` | Same pet + same time + same date = warning, never a crash |
| Recurring tasks | `Scheduler.generate_recurrence()` | Daily → +1 day, Weekly → +7 days via `timedelta` |
| KPI dashboard | `Scheduler.get_kpis()` | Active tasks, alert count, completion rate |
| Task completion | `Scheduler.complete_task()` | Marks done, triggers recurrence if applicable |

---

## Sample Output

```
============================================================
  PawPal+ Smart Pet Care - CLI Demo
============================================================

  Owner : Snehith
  Pets  : Luna, Mochi

  Schedule [All Tasks]
  ------------------------------------------------------------
  [o] 07:30 | Morning Feed (Luna, Daily) -- 2026-06-24
  [o] 08:00 | Breakfast (Mochi, Daily) -- 2026-06-24
  [o] 09:00 | Flea Treatment (Luna, Weekly) -- 2026-06-24
  [o] 09:00 | Hairball Remedy (Mochi, Weekly) -- 2026-06-24
  [o] 10:00 | Vet Checkup (Luna, Once) -- 2026-06-24
  [o] 10:00 | Nail Trim (Luna, Once) -- 2026-06-24
  [o] 15:30 | Playtime (Mochi, Daily) -- 2026-06-24
  [o] 18:00 | Evening Walk (Luna, Daily) -- 2026-06-24

  Conflict Detection
  ------------------------------------------------------------
  Conflict for Luna at 10:00 on 2026-06-24: 'Vet Checkup' vs 'Nail Trim'

  Completing 'Morning Feed' (Daily -> recurrence expected)
  ------------------------------------------------------------
  Marked complete: [x] 07:30 | Morning Feed (Luna, Daily) -- 2026-06-24
  Next occurrence : [o] 07:30 | Morning Feed (Luna, Daily) -- 2026-06-25

  KPI Summary
  ------------------------------------------------------------
  Total Active Tasks : 8
  System Alerts      : 1
  Completion Rate    : 11.1%
```

---

## Testing PawPal+

```bash
python -m pytest tests/test_pawpal.py -v
```

Tests cover: task completion, adding tasks to pets, adding pets to owner, sorting correctness, filtering by pet and status, recurrence generation (Daily and Weekly), conflict detection, and KPI calculations.

```
============================= test session starts =============================
collected 33 items

tests/test_pawpal.py::TestTask::test_initial_state PASSED
tests/test_pawpal.py::TestTask::test_mark_complete PASSED
tests/test_pawpal.py::TestTask::test_id_auto_generated PASSED
tests/test_pawpal.py::TestTask::test_mark_complete_idempotent PASSED
tests/test_pawpal.py::TestPet::test_add_task PASSED
tests/test_pawpal.py::TestPet::test_get_tasks_returns_copy PASSED
tests/test_pawpal.py::TestPet::test_get_pending PASSED
tests/test_pawpal.py::TestPet::test_get_completed PASSED
tests/test_pawpal.py::TestOwner::test_add_pet PASSED
tests/test_pawpal.py::TestOwner::test_duplicate_pet_raises PASSED
tests/test_pawpal.py::TestOwner::test_get_pet_case_insensitive PASSED
tests/test_pawpal.py::TestOwner::test_get_pet_not_found PASSED
tests/test_pawpal.py::TestOwner::test_get_all_tasks_aggregates PASSED
tests/test_pawpal.py::TestSchedulerSorting::test_sorted_chronologically PASSED
tests/test_pawpal.py::TestSchedulerSorting::test_sorted_with_pet_filter PASSED
tests/test_pawpal.py::TestSchedulerFiltering::test_filter_by_pet PASSED
tests/test_pawpal.py::TestSchedulerFiltering::test_filter_pending PASSED
tests/test_pawpal.py::TestSchedulerFiltering::test_filter_completed PASSED
tests/test_pawpal.py::TestSchedulerFiltering::test_all_pets_no_op PASSED
tests/test_pawpal.py::TestRecurrence::test_daily_recurrence PASSED
tests/test_pawpal.py::TestRecurrence::test_weekly_recurrence PASSED
tests/test_pawpal.py::TestRecurrence::test_once_no_recurrence PASSED
tests/test_pawpal.py::TestRecurrence::test_complete_task_adds_recurrence PASSED
tests/test_pawpal.py::TestRecurrence::test_complete_once_no_recurrence PASSED
tests/test_pawpal.py::TestConflictDetection::test_detects_conflict PASSED
tests/test_pawpal.py::TestConflictDetection::test_no_conflict_different_times PASSED
tests/test_pawpal.py::TestConflictDetection::test_no_conflict_different_pets PASSED
tests/test_pawpal.py::TestConflictDetection::test_completed_tasks_not_flagged PASSED
tests/test_pawpal.py::TestConflictDetection::test_conflict_does_not_raise PASSED
tests/test_pawpal.py::TestKPIs::test_kpi_structure PASSED
tests/test_pawpal.py::TestKPIs::test_completion_rate_zero PASSED
tests/test_pawpal.py::TestKPIs::test_completion_rate_partial PASSED
tests/test_pawpal.py::TestKPIs::test_empty_owner_kpis PASSED

============================= 33 passed in 0.06s ==============================
```

**Confidence Level: 5/5** — All 33 tests pass covering happy paths and edge cases.

---

## Smarter Scheduling

| Feature | Method | Notes |
|---|---|---|
| Sorting by time | `Scheduler.get_sorted_schedule()` | `lambda t: t.time` on zero-padded `"HH:MM"` strings |
| Filtering | `Scheduler.filter_tasks()` | By pet name and completion status |
| Conflict detection | `Scheduler.detect_conflicts()` | Single-pass O(n) dict keyed on `(pet, date, time)` |
| Recurring tasks | `Scheduler.generate_recurrence()` | Daily +1 day, Weekly +7 days, Once returns None |

---

## Demo Walkthrough

1. Launch `streamlit run app.py` and open the browser.
2. Go to the **Administrative Panel** tab and register a pet (name, species, age, breed).
3. Use the task form to schedule tasks — add them out of order and watch the Daily Schedule tab sort them automatically by time.
4. Schedule two tasks for the same pet at the same time — a red conflict warning appears at the top of the Daily Schedule.
5. Click the **Done** button next to any task — a toast notification appears, the task turns green, and a new recurrence is auto-generated for Daily/Weekly tasks.
6. Use the **Pet Filter** and **Task Status** sidebar dropdowns to narrow the view.
7. Watch the three KPI cards (Active Tasks, System Alerts, Completion Rate) update in real time.
