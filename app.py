import streamlit as st
import pawpal_system as ps

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ── Session state init (runs once; survives all reruns) ─────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = ps.Owner(name="")

if "scheduler" not in st.session_state:
    st.session_state.scheduler = ps.Scheduler(st.session_state.owner)

if "plan" not in st.session_state:
    st.session_state.plan = None

if "use_smart" not in st.session_state:
    st.session_state.use_smart = False

if "conflicts" not in st.session_state:
    st.session_state.conflicts = []

owner = st.session_state.owner
scheduler = st.session_state.scheduler

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("A daily pet care planner")
st.divider()

# ── Owner setup ──────────────────────────────────────────────────────────────
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value=owner.name)
with col2:
    def parse_hours_from_availability(avail: str) -> float:
        try:
            if avail.endswith("h") or "hour" in avail:
                return float(re.match(r"([0-9]+(?:\.[0-9]+)?)", avail).group(1))
            if "-" in avail:
                parts = avail.split("-")
                if len(parts) == 2:
                    start, end = parts
                    start = start.strip().lower()
                    end = end.strip().lower()
                    if start.endswith("am") or start.endswith("pm") or ":" in start:
                        # fallback: assume 8 hours if parsing fails
                        return owner.get_available_minutes() / 60.0
        except Exception:
            return owner.get_available_minutes() / 60.0
        return owner.get_available_minutes() / 60.0

    import re
    default_hours = parse_hours_from_availability(owner.availability) if owner.availability else 8.0
    availability_hours = st.number_input(
        "Available hours per day",
        min_value=1.0,
        max_value=24.0,
        value=float(default_hours),
        step=0.25,
        format="%.2f",
    )
    availability = f"{availability_hours}h"
    owner.set_availability(availability)

if st.button("Save owner info"):
    owner.update_info(name=owner_name)
    owner.set_availability(availability)
    st.success(f"Saved! Welcome, {owner.name}.")

st.divider()

# ── Add a pet ────────────────────────────────────────────────────────────────
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        pet_type = st.selectbox("Type", ["Dog", "Cat", "Bird", "Other"])
    with col3:
        pet_age = st.number_input("Age", min_value=0, max_value=30, value=1)
    special_need = st.text_input("Special need (optional)")
    submitted = st.form_submit_button("Add pet")

if submitted and pet_name:
    pet = ps.Pet(name=pet_name, type=pet_type, age=pet_age)
    if special_need:
        pet.add_special_need(special_need)
    owner.add_pet(pet)
    st.success(f"Added {pet_name}!")

if owner.pets:
    for pet in owner.pets:
        st.markdown(f"**{pet.name}** — {pet.type}, age {pet.age}"
                    + (f" | needs: {', '.join(pet.special_needs)}" if pet.special_needs else ""))
        
        # Display tasks for this pet
        if pet.tasks:
            st.caption("Tasks:")
            for task in pet.tasks:
                status = "✓" if task.completed else "○"
                st.markdown(
                    f"&nbsp;&nbsp;{status} **{task.title}** — {task.type} · {task.duration} min · "
                    f"priority {task.priority} · {task.frequency.value}"
                )
        else:
            st.caption("_(no tasks)_")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Add a task ───────────────────────────────────────────────────────────────
st.subheader("Tasks")

if not owner.pets:
    st.warning("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title", placeholder="e.g. Morning walk")
            task_type = st.text_input("Type", placeholder="e.g. Exercise")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            priority = st.number_input("Priority (1=highest)", min_value=1, max_value=5, value=2)

        frequency = st.selectbox("Frequency", [f.value for f in ps.Frequency])
        target_pet = st.selectbox("Assign to pet", [p.name for p in owner.pets])
        notes = st.text_input("Notes (optional)")
        task_submitted = st.form_submit_button("Add task")

    if task_submitted and task_title:
        freq_enum = ps.Frequency(frequency)
        task = ps.Task(
            title=task_title,
            type=task_type,
            duration=int(duration),
            priority=int(priority),
            frequency=freq_enum,
            notes=notes,
        )
        pet = next(p for p in owner.pets if p.name == target_pet)
        pet.add_task(task)
        # Regenerate plan immediately if one already exists
        if st.session_state.get("plan") is not None:
            use_smart = st.session_state.get("use_smart", False)
            plan = (scheduler.generate_smart_daily_plan() if use_smart
                    else scheduler.generate_daily_plan())
            st.session_state.plan = plan
            st.session_state.conflicts = scheduler.detect_conflicts(plan=plan)
        st.success(f"Added '{task_title}' to {target_pet}.")

plan_mode = st.radio(
    "Scheduling mode",
    ["Standard (priority + duration)", "Smart (weighted: priority + recency + frequency)"],
    horizontal=True,
)

if st.button("Generate schedule", use_container_width=True):
    use_smart = "Smart" in plan_mode
    st.session_state.use_smart = use_smart

    plan = scheduler.generate_smart_daily_plan() if use_smart else scheduler.generate_daily_plan()
    st.session_state.plan = plan
    st.session_state.conflicts = scheduler.detect_conflicts(plan=plan)

# ── Conflict warnings (persisted across reruns) ───────────────────────────
if st.session_state.get("conflicts"):
    for _, _, message in st.session_state.conflicts:
        st.warning(
            f"**Schedule overload detected**  \n{message}  \n"
            "_Tip: reduce task count, lower duration estimates, or spread tasks across days._"
        )
elif st.session_state.plan is None:
    st.info("No schedule generated yet. Click \"Generate schedule\" to build today’s plan.")
elif st.session_state.plan:
    st.success("No scheduling conflicts — your plan looks manageable!")

# ── Filters + table ───────────────────────────────────────────────────────
if st.session_state.plan:
    use_smart = st.session_state.use_smart

    with st.expander("Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            all_pet_names = sorted({t.pet_name for t in st.session_state.plan})
            selected_pets = st.multiselect("Pet", all_pet_names, default=all_pet_names)
        with col2:
            plan_max_dur = max((t.duration for t in st.session_state.plan), default=60)
            max_dur = st.slider("Max duration (min)", min_value=1, max_value=plan_max_dur, value=plan_max_dur)
        with col3:
            priority_options = ["All"] + sorted({t.priority for t in st.session_state.plan})
            selected_priority = st.selectbox("Priority", priority_options)

    # Apply filters
    view = [
        t for t in st.session_state.plan
        if t.pet_name in selected_pets
        and t.duration <= max_dur
        and (selected_priority == "All" or t.priority == selected_priority)
    ]

    # Build rows for data_editor
    seen: dict = {}
    rows = []
    row_titles = []   # parallel list: maps row index → task title for mark_complete
    row_slots = []    # parallel list: maps row index → slot number (for twice-daily)

    for task in view:
        seen[task.title] = seen.get(task.title, 0) + 1
        slot_num = seen[task.title]
        slot_label = f" ({slot_num}/2)" if task.frequency == ps.Frequency.TWICE_DAILY else ""
        row = {
            "Done": task.is_done(slot_num),
            "Task": f"{task.title}{slot_label}",
            "Pet": task.pet_name,
            "Type": task.type,
            "Duration (min)": task.duration,
            "Priority": task.priority,
            "Frequency": task.frequency.value,
        }
        if use_smart:
            row["Score"] = round(scheduler.calculate_weighted_priority_score(task), 2)
        rows.append(row)
        row_titles.append(task.title)
        row_slots.append(slot_num)

    disabled_cols = ["Task", "Pet", "Type", "Duration (min)", "Priority", "Frequency"]
    if use_smart:
        disabled_cols.append("Score")

    edited = st.data_editor(
        rows,
        hide_index=True,
        use_container_width=True,
        disabled=disabled_cols,
        column_config={"Done": st.column_config.CheckboxColumn("Done")},
        key="plan_editor",
    )

    # Normalize to list of dicts (data_editor returns DataFrame when given list of dicts)
    edited_list = edited.to_dict("records") if hasattr(edited, "to_dict") else list(edited)

    # Detect a newly checked box → mark that task complete and refresh
    for i, (orig, edit) in enumerate(zip(rows, edited_list)):
        if not orig["Done"] and edit.get("Done", False):
            scheduler.mark_task_complete(row_titles[i])
            st.session_state.plan = (scheduler.generate_smart_daily_plan() if use_smart
                                     else scheduler.generate_daily_plan())
            st.session_state.conflicts = scheduler.detect_conflicts(plan=st.session_state.plan)
            st.rerun()

    total_min = sum(t.duration for t in view)
    all_done = all(r["Done"] for r in rows)
    st.caption(f"{len(rows)} slot(s) · **{total_min} min** total · click a column header to sort")
    if all_done and rows:
        st.success("All tasks for today are done!")
