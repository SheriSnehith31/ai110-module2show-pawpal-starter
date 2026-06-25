"""
PawPal+ Streamlit Dashboard
Presentation layer only — all business logic lives in pawpal_system.py.
"""

from datetime import date
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session-state bootstrap — backend objects created exactly once
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Snehith")
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Sidebar — global filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Smart Pet Care Management")
    st.divider()

    pet_names = ["All Pets"] + [p.name for p in owner.get_all_pets()]
    pet_filter = st.selectbox("🐶 Pet Filter", pet_names)
    status_filter = st.selectbox("📋 Task Status", ["All", "Pending", "Completed"])

    st.divider()
    st.caption(f"Owner: **{owner.name}**")
    st.caption(f"Registered pets: **{len(owner.get_all_pets())}**")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    "<h1 style='margin-bottom:0'>🐾 PawPal+ Dashboard</h1>"
    "<p style='color:#94A3B8;margin-top:4px'>Smart pet care scheduling & management</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

kpis = scheduler.get_kpis()
conflicts = scheduler.detect_conflicts()

k1, k2, k3 = st.columns(3)
k1.metric("📅 Total Active Tasks",  kpis["total_active"])
k2.metric("🚨 System Alerts",       kpis["alerts"],
          delta=f"{kpis['alerts']} conflict(s)" if kpis["alerts"] else None,
          delta_color="inverse")
k3.metric("✅ Completion Rate",      f"{kpis['completion_rate']}%")

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_schedule, tab_pets, tab_admin = st.tabs(
    ["📅 Daily Schedule", "🐾 Manage Pets", "➕ Administrative Panel"]
)

# ── Tab 1: Daily Schedule ────────────────────────────────────────────────────

with tab_schedule:
    if conflicts:
        for warning in conflicts:
            st.warning(warning)

    tasks = scheduler.get_sorted_schedule(
        pet_filter=pet_filter,
        status_filter=status_filter,
    )

    if not tasks:
        st.info("No tasks match the current filters.")
    else:
        task_conflicts = {w for w in conflicts}

        for task in tasks:
            # Determine card border color
            is_conflict = any(task.description in w for w in conflicts)
            if is_conflict:
                border = "#EF4444"
            elif task.completed:
                border = "#10B981"
            else:
                border = "#4F46E5"

            status_badge = (
                "<span style='background:#10B981;color:#fff;padding:2px 8px;"
                "border-radius:12px;font-size:12px'>✓ Done</span>"
                if task.completed
                else "<span style='background:#4F46E5;color:#fff;padding:2px 8px;"
                "border-radius:12px;font-size:12px'>Pending</span>"
            )
            conflict_badge = (
                "<span style='background:#EF4444;color:#fff;padding:2px 8px;"
                "border-radius:12px;font-size:12px;margin-left:6px'>⚠ Conflict</span>"
                if is_conflict else ""
            )

            card_html = f"""
            <div style="
                border-left: 4px solid {border};
                background: #1E293B;
                border-radius: 8px;
                padding: 14px 18px;
                margin-bottom: 4px;
            ">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="font-size:18px;font-weight:600;color:#F8FAFC">
                            {task.time} — {task.description}
                        </span>
                        {status_badge}{conflict_badge}
                    </div>
                    <div style="color:#94A3B8;font-size:13px;text-align:right">
                        🐾 {task.pet_name}<br>
                        🔁 {task.frequency}<br>
                        📆 {task.due_date}
                    </div>
                </div>
            </div>
            """

            col_card, col_btn = st.columns([6, 1])
            with col_card:
                st.markdown(card_html, unsafe_allow_html=True)
            with col_btn:
                btn_label = "↩ Undo" if task.completed else "✓ Done"
                if not task.completed:
                    if st.button(btn_label, key=f"complete_{task.id}"):
                        scheduler.complete_task(task.id)
                        st.toast("🔄 Task updated!", icon="📅")
                        st.rerun()
                else:
                    st.button(btn_label, key=f"done_{task.id}", disabled=True)

# ── Tab 2: Manage Pets ───────────────────────────────────────────────────────

with tab_pets:
    st.subheader("Registered Pets")

    pets = owner.get_all_pets()
    if not pets:
        st.info("No pets registered yet. Use the Administrative Panel to add one.")
    else:
        cols = st.columns(min(len(pets), 3))
        for i, pet in enumerate(pets):
            with cols[i % 3]:
                pending = len(pet.get_pending_tasks())
                done = len(pet.get_completed_tasks())
                st.markdown(
                    f"""
                    <div style="background:#1E293B;border-radius:10px;padding:16px;margin-bottom:12px">
                        <h3 style="margin:0;color:#F8FAFC">🐾 {pet.name}</h3>
                        <p style="color:#94A3B8;margin:4px 0">{pet.species} · {pet.breed}</p>
                        <p style="color:#94A3B8;margin:4px 0">Age: {pet.age} yr</p>
                        <hr style="border-color:#334155;margin:8px 0">
                        <span style="color:#4F46E5">⏳ {pending} pending</span> &nbsp;
                        <span style="color:#10B981">✓ {done} done</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ── Tab 3: Administrative Panel ──────────────────────────────────────────────

with tab_admin:
    col_add_pet, col_add_task = st.columns(2)

    # --- Add Pet form ---
    with col_add_pet:
        st.subheader("Add a New Pet")
        with st.form("add_pet_form", clear_on_submit=True):
            pet_name_input  = st.text_input("Pet Name")
            pet_species     = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
            pet_age         = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            pet_breed       = st.text_input("Breed")
            submitted_pet   = st.form_submit_button("Register Pet 🐾")

        if submitted_pet:
            if not pet_name_input.strip():
                st.error("Pet name cannot be empty.")
            elif not pet_breed.strip():
                st.error("Breed cannot be empty.")
            else:
                try:
                    new_pet = Pet(
                        name=pet_name_input.strip(),
                        species=pet_species,
                        age=int(pet_age),
                        breed=pet_breed.strip(),
                    )
                    owner.add_pet(new_pet)
                    st.success(f"✅ {new_pet.name} registered!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # --- Add Task form ---
    with col_add_task:
        st.subheader("Schedule a Task")
        pet_options = [p.name for p in owner.get_all_pets()]

        if not pet_options:
            st.info("Register a pet first before scheduling tasks.")
        else:
            with st.form("add_task_form", clear_on_submit=True):
                task_pet    = st.selectbox("Pet", pet_options)
                task_desc   = st.text_input("Task Description")
                task_time   = st.text_input("Time (HH:MM)", value="08:00")
                task_freq   = st.selectbox("Frequency", ["Once", "Daily", "Weekly"])
                task_date   = st.date_input("Due Date", value=date.today())
                submitted_task = st.form_submit_button("Schedule Task 📅")

            if submitted_task:
                if not task_desc.strip():
                    st.error("Task description cannot be empty.")
                else:
                    try:
                        # Validate HH:MM format
                        h, m = task_time.strip().split(":")
                        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
                        new_task = Task(
                            description=task_desc.strip(),
                            time=task_time.strip(),
                            frequency=task_freq,
                            pet_name=task_pet,
                            due_date=task_date,
                        )
                        pet_obj = owner.get_pet(task_pet)
                        pet_obj.add_task(new_task)
                        st.success(f"✅ Task '{new_task.description}' added for {task_pet}!")
                        st.rerun()
                    except (ValueError, AssertionError):
                        st.error("Invalid time format. Use HH:MM (e.g. 08:30).")
