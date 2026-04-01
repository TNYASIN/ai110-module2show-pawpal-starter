import streamlit as st
import pawpal_system as ps

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ── Session state init (runs once; survives all reruns) ─────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = ps.Owner(name="")

if "scheduler" not in st.session_state:
    st.session_state.scheduler = ps.Scheduler(st.session_state.owner)

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
    availability = st.text_input("Availability", value=owner.availability, placeholder="e.g. 8am-6pm")

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
        st.success(f"Added '{task_title}' to {target_pet}.")

st.divider()

# ── Daily schedule ───────────────────────────────────────────────────────────
st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    plan = scheduler.generate_daily_plan()
    if not plan:
        st.info("No tasks scheduled. Add pets and tasks above.")
    else:
        seen: dict = {}
        for task in plan:
            seen[task.title] = seen.get(task.title, 0) + 1
            slot_label = f" ({seen[task.title]}/2)" if task.frequency == ps.Frequency.TWICE_DAILY else ""
            status = "✓" if task.completed else "○"
            st.markdown(
                f"{status} **{task.title}{slot_label}** `[{task.pet_name}]`  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;{task.type} · {task.duration} min · "
                f"priority {task.priority} · {task.frequency.value}"
            )
