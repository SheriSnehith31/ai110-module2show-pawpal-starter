"""
PawPal+ — Smart Pet Care Management System
Backend module: all business logic lives here; no Streamlit imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single scheduled pet-care event."""

    description: str
    time: str          # "HH:MM" 24-hour
    frequency: str     # "Once" | "Daily" | "Weekly"
    pet_name: str
    due_date: date
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.time} | {self.description} "
            f"({self.pet_name}, {self.frequency}) — {self.due_date}"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Stores a pet profile and owns its task list."""

    name: str
    species: str
    age: int
    breed: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's schedule."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        """Return only incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        """Return only completed tasks."""
        return [t for t in self.tasks if t.completed]

    def __repr__(self) -> str:
        return f"Pet({self.name}, {self.species}, age={self.age}, breed={self.breed})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Registry that manages all pets in the household."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self._pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet; raises ValueError on duplicate name."""
        if any(p.name.lower() == pet.name.lower() for p in self._pets):
            raise ValueError(f"A pet named '{pet.name}' is already registered.")
        self._pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Look up a pet by name (case-insensitive)."""
        for pet in self._pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_pets(self) -> List[Pet]:
        """Return the full list of registered pets."""
        return list(self._pets)

    def get_all_tasks(self) -> List[Task]:
        """Aggregate every task across all pets."""
        tasks: List[Task] = []
        for pet in self._pets:
            tasks.extend(pet.tasks)
        return tasks

    @property
    def pets(self) -> List[Pet]:
        return self._pets

    def __repr__(self) -> str:
        return f"Owner({self.name}, pets={len(self._pets)})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Algorithmic engine: sorting, filtering, recurrence, conflict detection,
    and KPI calculation.  The only surface that app.py should call.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner: Owner = owner

    # --- Core schedule retrieval ---

    def get_sorted_schedule(
        self,
        pet_filter: str = "All Pets",
        status_filter: str = "All",
    ) -> List[Task]:
        """
        Return tasks sorted chronologically by "HH:MM" time string.
        Lexicographic order on zero-padded time strings equals chronological order.
        """
        tasks = self.owner.get_all_tasks()
        tasks = self.filter_tasks(tasks, pet_filter, status_filter)
        return sorted(tasks, key=lambda t: t.time)

    # --- Filtering ---

    def filter_tasks(
        self,
        tasks: List[Task],
        pet_filter: str = "All Pets",
        status_filter: str = "All",
    ) -> List[Task]:
        """
        Filter by pet name and completion status.
        'All Pets' / 'All' are no-op sentinel values.
        """
        if pet_filter != "All Pets":
            tasks = [t for t in tasks if t.pet_name == pet_filter]
        if status_filter == "Pending":
            tasks = [t for t in tasks if not t.completed]
        elif status_filter == "Completed":
            tasks = [t for t in tasks if t.completed]
        return tasks

    # --- Task completion ---

    def complete_task(self, task_id: str) -> Optional[Task]:
        """
        Mark the matching task complete and, if recurring, add the next
        occurrence to the owning pet.  Returns the task or None if not found.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.id == task_id:
                    task.mark_complete()
                    next_task = self.generate_recurrence(task)
                    if next_task:
                        pet.add_task(next_task)
                    return task
        return None

    # --- Recurrence ---

    def generate_recurrence(self, task: Task) -> Optional[Task]:
        """
        Create the next Task occurrence:
          Daily  → due_date + 1 day
          Weekly → due_date + 7 days
          Once   → None
        """
        delta_map: Dict[str, Optional[timedelta]] = {
            "Daily": timedelta(days=1),
            "Weekly": timedelta(days=7),
            "Once": None,
        }
        delta = delta_map.get(task.frequency)
        if delta is None:
            return None
        return Task(
            description=task.description,
            time=task.time,
            frequency=task.frequency,
            pet_name=task.pet_name,
            due_date=task.due_date + delta,
        )

    # --- Conflict detection ---

    def detect_conflicts(self) -> List[str]:
        """
        Detect pending tasks for the same pet at the same time on the same date.
        Returns warning strings; never raises.
        """
        warnings: List[str] = []
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        seen: Dict[Tuple, Task] = {}
        for task in pending:
            key = (task.pet_name, task.due_date, task.time)
            if key in seen:
                other = seen[key]
                warnings.append(
                    f"⚠ Conflict for {task.pet_name} at {task.time} on {task.due_date}: "
                    f"'{other.description}' vs '{task.description}'"
                )
            else:
                seen[key] = task
        return warnings

    # --- KPIs ---

    def get_kpis(self) -> dict:
        """
        Compute dashboard KPIs.
        Returns:
            total_active   — pending task count
            alerts         — number of scheduling conflicts
            completion_rate — percentage 0.0–100.0
        """
        all_tasks = self.owner.get_all_tasks()
        total = len(all_tasks)
        completed_count = sum(1 for t in all_tasks if t.completed)
        active = total - completed_count
        alerts = len(self.detect_conflicts())
        rate = round(completed_count / total * 100, 1) if total > 0 else 0.0
        return {
            "total_active": active,
            "alerts": alerts,
            "completion_rate": rate,
        }
