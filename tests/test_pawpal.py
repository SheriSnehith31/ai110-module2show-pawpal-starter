"""
PawPal+ pytest test suite.
Run: python -m pytest tests/test_pawpal.py -v
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def today() -> date:
    return date(2026, 6, 24)


@pytest.fixture
def sample_task(today) -> Task:
    return Task(
        description="Morning Feed",
        time="07:30",
        frequency="Daily",
        pet_name="Luna",
        due_date=today,
    )


@pytest.fixture
def sample_pet() -> Pet:
    return Pet(name="Luna", species="Dog", age=3, breed="Golden Retriever")


@pytest.fixture
def populated_owner(today) -> Owner:
    owner = Owner(name="Snehith")
    luna = Pet(name="Luna", species="Dog", age=3, breed="Golden Retriever")
    mochi = Pet(name="Mochi", species="Cat", age=2, breed="Scottish Fold")
    owner.add_pet(luna)
    owner.add_pet(mochi)

    luna.add_task(Task("Evening Walk",   "18:00", "Daily",  "Luna",  today))
    luna.add_task(Task("Morning Feed",   "07:30", "Daily",  "Luna",  today))
    luna.add_task(Task("Vet Checkup",    "10:00", "Once",   "Luna",  today))

    mochi.add_task(Task("Breakfast",     "08:00", "Daily",  "Mochi", today))
    mochi.add_task(Task("Playtime",      "15:30", "Daily",  "Mochi", today))
    return owner


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

class TestTask:
    def test_initial_state(self, sample_task):
        assert sample_task.completed is False

    def test_mark_complete(self, sample_task):
        sample_task.mark_complete()
        assert sample_task.completed is True

    def test_id_auto_generated(self, today):
        t1 = Task("Feed", "08:00", "Once", "Luna", today)
        t2 = Task("Feed", "08:00", "Once", "Luna", today)
        assert t1.id != t2.id

    def test_mark_complete_idempotent(self, sample_task):
        sample_task.mark_complete()
        sample_task.mark_complete()
        assert sample_task.completed is True


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_task(self, sample_pet, sample_task):
        sample_pet.add_task(sample_task)
        assert sample_task in sample_pet.get_tasks()

    def test_get_tasks_returns_copy(self, sample_pet, sample_task):
        sample_pet.add_task(sample_task)
        result = sample_pet.get_tasks()
        result.clear()
        assert len(sample_pet.get_tasks()) == 1

    def test_get_pending(self, sample_pet, today):
        t1 = Task("Feed",  "08:00", "Once", "Luna", today)
        t2 = Task("Walk",  "09:00", "Once", "Luna", today)
        t2.mark_complete()
        sample_pet.add_task(t1)
        sample_pet.add_task(t2)
        pending = sample_pet.get_pending_tasks()
        assert t1 in pending
        assert t2 not in pending

    def test_get_completed(self, sample_pet, today):
        t1 = Task("Feed", "08:00", "Once", "Luna", today)
        t1.mark_complete()
        sample_pet.add_task(t1)
        assert t1 in sample_pet.get_completed_tasks()


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet(self, sample_pet):
        owner = Owner("Snehith")
        owner.add_pet(sample_pet)
        assert sample_pet in owner.get_all_pets()

    def test_duplicate_pet_raises(self, sample_pet):
        owner = Owner("Snehith")
        owner.add_pet(sample_pet)
        with pytest.raises(ValueError):
            owner.add_pet(Pet("Luna", "Dog", 1, "Poodle"))

    def test_get_pet_case_insensitive(self, sample_pet):
        owner = Owner("Snehith")
        owner.add_pet(sample_pet)
        assert owner.get_pet("luna") is sample_pet
        assert owner.get_pet("LUNA") is sample_pet

    def test_get_pet_not_found(self):
        owner = Owner("Snehith")
        assert owner.get_pet("Ghost") is None

    def test_get_all_tasks_aggregates(self, populated_owner):
        tasks = populated_owner.get_all_tasks()
        assert len(tasks) == 5


# ---------------------------------------------------------------------------
# Scheduler — sorting
# ---------------------------------------------------------------------------

class TestSchedulerSorting:
    def test_sorted_chronologically(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        tasks = scheduler.get_sorted_schedule()
        times = [t.time for t in tasks]
        assert times == sorted(times)

    def test_sorted_with_pet_filter(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        tasks = scheduler.get_sorted_schedule(pet_filter="Luna")
        times = [t.time for t in tasks]
        assert times == sorted(times)
        assert all(t.pet_name == "Luna" for t in tasks)


# ---------------------------------------------------------------------------
# Scheduler — filtering
# ---------------------------------------------------------------------------

class TestSchedulerFiltering:
    def test_filter_by_pet(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        tasks = scheduler.get_sorted_schedule(pet_filter="Mochi")
        assert all(t.pet_name == "Mochi" for t in tasks)
        assert len(tasks) == 2

    def test_filter_pending(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        # complete one task
        all_tasks = populated_owner.get_all_tasks()
        all_tasks[0].mark_complete()
        pending = scheduler.get_sorted_schedule(status_filter="Pending")
        assert all(not t.completed for t in pending)

    def test_filter_completed(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        all_tasks = populated_owner.get_all_tasks()
        all_tasks[0].mark_complete()
        completed = scheduler.get_sorted_schedule(status_filter="Completed")
        assert all(t.completed for t in completed)
        assert len(completed) == 1

    def test_all_pets_no_op(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        tasks = scheduler.get_sorted_schedule(pet_filter="All Pets")
        assert len(tasks) == 5


# ---------------------------------------------------------------------------
# Scheduler — recurrence
# ---------------------------------------------------------------------------

class TestRecurrence:
    def test_daily_recurrence(self, today):
        task = Task("Feed", "08:00", "Daily", "Luna", today)
        scheduler = Scheduler(Owner("Snehith"))
        next_task = scheduler.generate_recurrence(task)
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False

    def test_weekly_recurrence(self, today):
        task = Task("Bath", "10:00", "Weekly", "Luna", today)
        scheduler = Scheduler(Owner("Snehith"))
        next_task = scheduler.generate_recurrence(task)
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=7)

    def test_once_no_recurrence(self, today):
        task = Task("Vet", "09:00", "Once", "Luna", today)
        scheduler = Scheduler(Owner("Snehith"))
        assert scheduler.generate_recurrence(task) is None

    def test_complete_task_adds_recurrence(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        task = Task("Feed", "08:00", "Daily", "Luna", today)
        luna.add_task(task)
        owner.add_pet(luna)
        scheduler = Scheduler(owner)
        scheduler.complete_task(task.id)
        tasks = luna.get_tasks()
        assert len(tasks) == 2
        next_task = next(t for t in tasks if not t.completed)
        assert next_task.due_date == today + timedelta(days=1)

    def test_complete_once_no_recurrence(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        task = Task("Vet", "09:00", "Once", "Luna", today)
        luna.add_task(task)
        owner.add_pet(luna)
        scheduler = Scheduler(owner)
        scheduler.complete_task(task.id)
        assert len(luna.get_tasks()) == 1


# ---------------------------------------------------------------------------
# Scheduler — conflict detection
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def test_detects_conflict(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        luna.add_task(Task("Vet",       "10:00", "Once", "Luna", today))
        luna.add_task(Task("Nail Trim", "10:00", "Once", "Luna", today))
        owner.add_pet(luna)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1
        assert "Luna" in conflicts[0]

    def test_no_conflict_different_times(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        luna.add_task(Task("Vet",  "09:00", "Once", "Luna", today))
        luna.add_task(Task("Walk", "10:00", "Once", "Luna", today))
        owner.add_pet(luna)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []

    def test_no_conflict_different_pets(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        mochi = Pet("Mochi", "Cat", 2, "Scottish Fold")
        luna.add_task(Task("Feed",  "08:00", "Once", "Luna",  today))
        mochi.add_task(Task("Feed", "08:00", "Once", "Mochi", today))
        owner.add_pet(luna)
        owner.add_pet(mochi)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []

    def test_completed_tasks_not_flagged(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        t1 = Task("Vet",  "10:00", "Once", "Luna", today)
        t2 = Task("Trim", "10:00", "Once", "Luna", today)
        t1.mark_complete()
        luna.add_task(t1)
        luna.add_task(t2)
        owner.add_pet(luna)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []

    def test_conflict_does_not_raise(self, today):
        owner = Owner("Snehith")
        luna = Pet("Luna", "Dog", 3, "Golden Retriever")
        for i in range(5):
            luna.add_task(Task(f"Task {i}", "10:00", "Once", "Luna", today))
        owner.add_pet(luna)
        scheduler = Scheduler(owner)
        result = scheduler.detect_conflicts()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Scheduler — KPIs
# ---------------------------------------------------------------------------

class TestKPIs:
    def test_kpi_structure(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        kpis = scheduler.get_kpis()
        assert "total_active" in kpis
        assert "alerts" in kpis
        assert "completion_rate" in kpis

    def test_completion_rate_zero(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        assert scheduler.get_kpis()["completion_rate"] == 0.0

    def test_completion_rate_partial(self, populated_owner):
        scheduler = Scheduler(populated_owner)
        all_tasks = populated_owner.get_all_tasks()
        all_tasks[0].mark_complete()
        kpis = scheduler.get_kpis()
        assert kpis["completion_rate"] == 20.0
        assert kpis["total_active"] == 4

    def test_empty_owner_kpis(self):
        scheduler = Scheduler(Owner("Empty"))
        kpis = scheduler.get_kpis()
        assert kpis["total_active"] == 0
        assert kpis["completion_rate"] == 0.0
