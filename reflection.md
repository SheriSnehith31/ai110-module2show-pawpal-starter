# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started with four classes: `Task`, `Pet`, `Owner`, and `Scheduler`. `Task` is a dataclass that holds a description, time string, frequency, completion status, pet name, and due date — it is a pure data carrier with one behavior (`mark_complete`). `Pet` is also a dataclass that stores profile attributes and owns a list of tasks, with methods to add and query them. `Owner` is a plain class that acts as a registry for all pets in the household and aggregates tasks across them. `Scheduler` is a plain class that takes an `Owner` as a dependency and contains all the algorithmic logic — sorting, filtering, recurrence, conflict detection, and KPI calculation.

The key responsibility assignment was keeping `Scheduler` separate from `Owner`. `Owner` only knows how to store and retrieve pets; `Scheduler` knows how to think about them. This made testing and Streamlit integration much cleaner.

**b. Design changes**

During implementation I made two meaningful changes from the initial skeleton:

1. `Owner._pets` became a private attribute with a public `pets` property. The skeleton had it as a plain public list, but Streamlit reruns the script on every interaction — making the list private prevents accidental replacement from outside the class.

2. The conflict detection algorithm changed from a nested loop (O(n²)) to a single-pass dictionary keyed on `(pet_name, due_date, time)` (O(n)). The first approach was easier to read initially but would slow down noticeably with large task lists. The dict approach is equally readable once you understand the key tuple.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: time (tasks are sorted chronologically by their `"HH:MM"` string), pet ownership (tasks are scoped to a specific pet, so conflicts are per-pet not across pets), and due date (recurrences are generated relative to the original due date, not today's date). Priority was not implemented as a numeric field — frequency (`Once`, `Daily`, `Weekly`) acts as the implicit priority signal since recurring tasks are more important to surface.

I decided that time ordering mattered most for a daily care workflow: a pet owner scans their morning-to-evening schedule linearly, so chronological order is the most natural view.

**b. Tradeoffs**

The conflict detection only flags exact time matches — it does not consider task duration or overlapping intervals. For example, a 30-minute walk starting at 09:00 and a feeding at 09:15 would not trigger a warning. This is a reasonable tradeoff for the current scope because tasks do not yet have duration fields, and adding overlap detection without durations would require arbitrary assumptions. If duration were added, the conflict check would need to compare `[start, start+duration)` intervals instead of exact equality.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI across every phase: brainstorming class responsibilities, generating the Mermaid UML, scaffolding method stubs, implementing the algorithmic layer, drafting the pytest suite, and generating Streamlit HTML card markup. The most effective prompts were specific and architectural — for example, "the Scheduler should depend on Owner, not the other way around; generate the constructor and retrieval methods accordingly" produced cleaner output than a generic "build a pet scheduler."

Separate chat sessions for each phase were genuinely useful. The Phase 4 algorithmic session had no clutter from Phase 2 implementation details, so AI suggestions stayed focused on algorithm design rather than mixing in unrelated code edits.

**b. Judgment and verification**

The initial conflict detection draft used a nested loop comparing every task pair. I rejected it and asked for a single-pass dictionary approach instead. I evaluated the suggestion by tracing through both algorithms manually with a small example (three tasks, one conflict) and confirmed the dict version produced the same warnings with fewer iterations. I also checked that the dict correctly handles three-way conflicts — the first task wins the slot, and each subsequent task produces its own warning, which is the right user-facing behavior.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers: task completion (mark_complete sets the flag), task addition (pet task count increases), adding pets to owner (duplicate name raises ValueError), chronological sort correctness, filtering by pet name and by status, Daily recurrence (next due date is +1 day), Weekly recurrence (+7 days), Once tasks produce no recurrence, completing a task triggers recurrence generation, conflict detection fires on same-pet/same-time/same-date, completed tasks are excluded from conflict checks, and all three KPI values are computed correctly.

These tests matter because the Scheduler is the only surface the UI calls — if any of these behaviors are wrong, the entire dashboard shows incorrect data silently.

**b. Confidence**

Confidence level: **5/5**. All 33 tests pass. The edge cases I would test next with more time are: tasks added while a filter is active (verify filter still applies correctly after a rerun), recurrence across month boundaries (e.g., June 30 + 1 day = July 1), and concurrent completion of the same task ID from two browser tabs.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was the most valuable discipline in this project. By verifying `pawpal_system.py` through `main.py` and the pytest suite before touching `app.py`, I never had to debug business logic through the Streamlit interface. Every bug I found was caught at the terminal level where it was easy to isolate.

**b. What you would improve**

I would add a `duration_minutes` field to `Task` and upgrade conflict detection to check overlapping time intervals rather than exact matches. I would also add a date picker to the Daily Schedule tab so users can view past or future dates rather than only today's tasks.

**c. Key takeaway**

The most important thing I learned is that AI is most useful when you give it architectural constraints, not open-ended requests. Telling AI "the Scheduler must depend on Owner, not inherit from it, and must return a list of warning strings rather than raising exceptions" produced usable code on the first pass. Open-ended requests like "build a scheduler" produce generic code that requires significant rework. The human role is to define the constraints; AI executes within them.
