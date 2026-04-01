from pawpal_system import Owner, Pet, Task, Scheduler, Frequency

# --- Create Owner ---
owner = Owner(name="Tanya", availability="8am-6pm", preferences="mornings first")

# --- Create Pets ---
luna = Pet(name="Luna", type="Dog", age=3)
luna.add_special_need("joint supplement with meals")

mochi = Pet(name="Mochi", type="Cat", age=5)

owner.add_pet(luna)
owner.add_pet(mochi)

# --- Add Tasks to Luna ---
luna.add_task(Task(
    title="Morning Walk",
    type="Exercise",
    duration=30,
    priority=1,
    frequency=Frequency.DAILY,
))

luna.add_task(Task(
    title="Joint Supplement",
    type="Medication",
    duration=5,
    priority=1,
    frequency=Frequency.TWICE_DAILY,
    notes="Mix into food",
))

# --- Add Tasks to Mochi ---
mochi.add_task(Task(
    title="Brush Coat",
    type="Grooming",
    duration=10,
    priority=3,
    frequency=Frequency.WEEKLY,
))

mochi.add_task(Task(
    title="Feeding",
    type="Nutrition",
    duration=5,
    priority=2,
    frequency=Frequency.TWICE_DAILY,
))

# --- Create a conflict scenario: Luna has too many tasks ---
# Add several tasks that will exceed the 120-minute reasonable daily limit
luna.add_task(Task(
    title="Afternoon Walk",
    type="Exercise",
    duration=35,
    priority=1,
    frequency=Frequency.DAILY,
))

luna.add_task(Task(
    title="Training Session",
    type="Behavior",
    duration=45,
    priority=2,
    frequency=Frequency.DAILY,
))

luna.add_task(Task(
    title="Playtime",
    type="Enrichment",
    duration=30,
    priority=3,
    frequency=Frequency.DAILY,
))

# --- Run Scheduler ---
scheduler = Scheduler(owner)
scheduler.view_plan()

# --- Demo filters ---
print("\nTasks under 10 minutes:")
for task in scheduler.filter_by_duration(10):
    print(f"  - {task}")

print("\nPriority 1 tasks:")
for task in scheduler.filter_by_priority(1):
    print(f"  - {task}")

# --- Conflict Detection ---
print("\n" + "=" * 50)
scheduler.print_conflicts()

# --- ADVANCED FEATURE: Smart Prioritization ---
print("\n" + "=" * 50)
print("ADVANCED FEATURE: WEIGHTED PRIORITY SCORING")
print("=" * 50)
scheduler.view_smart_plan()

print("\n💡 How it works:")
print("   The smart planner weighs tasks by:")
print("   • Base priority (importance): 50%")
print("   • Recency (days since completion): 30%")
print("   • Frequency pattern (recurring vs one-off): 20%")
print("   This creates a composite urgency score for smarter ordering.")

# --- Recurring Task Automation Demo ---
print("\n" + "=" * 50)
print("RECURRING TASK AUTOMATION DEMO")
print("=" * 50)
print(f"\nLuna's tasks BEFORE marking 'Morning Walk' complete: {len(luna.tasks)}")
for i, task in enumerate(luna.tasks, 1):
    print(f"  {i}. {task.title}")

new_task = scheduler.mark_task_complete("Morning Walk")
print(f"\n✓ Marked 'Morning Walk' as complete!")
if new_task:
    print(f"→ Auto-created new task for next occurrence: '{new_task.title}'")
    print(f"  (Reset for next daily cycle)")

print(f"\nLuna's tasks AFTER: {len(luna.tasks)}")
for i, task in enumerate(luna.tasks, 1):
    status = "✓" if task.completed else "○"
    print(f"  {status} {i}. {task.title}")



