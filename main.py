"""
PawPal+ CLI Demo
Run: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


DIVIDER = "-" * 60


def print_schedule(scheduler: Scheduler, pet_filter: str = "All Pets", status_filter: str = "All") -> None:
    tasks = scheduler.get_sorted_schedule(pet_filter=pet_filter, status_filter=status_filter)
    label_parts = []
    if pet_filter != "All Pets":
        label_parts.append(pet_filter)
    if status_filter != "All":
        label_parts.append(status_filter)
    label = " | ".join(label_parts) if label_parts else "All Tasks"
    print(f"\n  Schedule [{label}]")
    print(f"  {DIVIDER}")
    if not tasks:
        print("  (no tasks)")
    for task in tasks:
        print(f"  {task}")


def main() -> None:
    print(f"\n{'=' * 60}")
    print("  PawPal+ Smart Pet Care — CLI Demo")
    print(f"{'=' * 60}")

    # --- Setup ---
    owner = Owner(name="Snehith")
    scheduler = Scheduler(owner=owner)

    luna = Pet(name="Luna", species="Dog", age=3, breed="Golden Retriever")
    mochi = Pet(name="Mochi", species="Cat", age=2, breed="Scottish Fold")
    owner.add_pet(luna)
    owner.add_pet(mochi)

    today = date.today()

    # Tasks added intentionally OUT of chronological order to test sorting
    luna.add_task(Task("Evening Walk",      "18:00", "Daily",  "Luna",  today))
    luna.add_task(Task("Morning Feed",      "07:30", "Daily",  "Luna",  today))
    luna.add_task(Task("Vet Checkup",       "10:00", "Once",   "Luna",  today))
    luna.add_task(Task("Flea Treatment",    "09:00", "Weekly", "Luna",  today))

    mochi.add_task(Task("Breakfast",        "08:00", "Daily",  "Mochi", today))
    mochi.add_task(Task("Playtime",         "15:30", "Daily",  "Mochi", today))
    mochi.add_task(Task("Hairball Remedy",  "09:00", "Weekly", "Mochi", today))

    # Intentional conflict: same pet, same time, same date
    luna.add_task(Task("Nail Trim",         "10:00", "Once",   "Luna",  today))

    print(f"\n  Owner : {owner.name}")
    print(f"  Pets  : {', '.join(p.name for p in owner.get_all_pets())}")

    # --- Full sorted schedule ---
    print_schedule(scheduler)

    # --- Filtering demos ---
    print_schedule(scheduler, pet_filter="Luna")
    print_schedule(scheduler, pet_filter="Mochi")
    print_schedule(scheduler, status_filter="Pending")

    # --- Conflict detection ---
    print(f"\n  Conflict Detection")
    print(f"  {DIVIDER}")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts detected.")

    # --- Complete a recurring task & show recurrence ---
    print(f"\n  Completing 'Morning Feed' (Daily → recurrence expected)")
    print(f"  {DIVIDER}")
    morning_feed = next(t for t in luna.get_tasks() if t.description == "Morning Feed")
    scheduler.complete_task(morning_feed.id)
    print(f"  Marked complete: {morning_feed}")
    next_feed = next(
        (t for t in luna.get_tasks() if t.description == "Morning Feed" and not t.completed),
        None,
    )
    if next_feed:
        print(f"  Next occurrence : {next_feed}")

    # --- KPIs ---
    kpis = scheduler.get_kpis()
    print(f"\n  KPI Summary")
    print(f"  {DIVIDER}")
    print(f"  Total Active Tasks : {kpis['total_active']}")
    print(f"  System Alerts      : {kpis['alerts']}")
    print(f"  Completion Rate    : {kpis['completion_rate']}%")

    # --- Pending after completion ---
    print_schedule(scheduler, status_filter="Completed")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
