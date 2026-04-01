from pawpal_system import Owner, Pet, Task, Scheduler, Frequency
from datetime import date, timedelta


def make_task(title="Morning Walk", priority=1, duration=30, frequency=Frequency.DAILY):
    return Task(title=title, type="Exercise", duration=duration, priority=priority, frequency=frequency)


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================

# --- Test 1: mark_complete() changes task status ---
def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


# --- Test 2: adding a task to a Pet increases its task count ---
def test_add_task_increases_pet_task_count():
    pet = Pet(name="Luna", type="Dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task("Walk"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task("Feed"))
    assert len(pet.tasks) == 2


# ============================================================================
# SORTING CORRECTNESS TESTS
# ============================================================================

def test_sorting_by_priority_only():
    """Tasks sorted first by priority (lower number = higher urgency)."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Add tasks in reverse priority order
    pet.add_task(Task("Low priority", "Grooming", 30, 5, Frequency.DAILY))
    pet.add_task(Task("High priority", "Exercise", 30, 1, Frequency.DAILY))
    pet.add_task(Task("Medium priority", "Feeding", 30, 3, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # Verify priority order: 1, 3, 5
    assert plan[0].priority == 1
    assert plan[1].priority == 3
    assert plan[2].priority == 5


def test_sorting_by_duration_when_priority_equal():
    """When priority is equal, tasks sorted by duration (shorter first)."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Same priority, different durations
    pet.add_task(Task("Long task", "Grooming", 120, 2, Frequency.DAILY))
    pet.add_task(Task("Quick task", "Check", 5, 2, Frequency.DAILY))
    pet.add_task(Task("Medium task", "Exercise", 30, 2, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # Verify duration order: 5, 30, 120
    assert plan[0].duration == 5
    assert plan[1].duration == 30
    assert plan[2].duration == 120


def test_sorting_priority_then_duration():
    """Complex sort: priority first, then duration as tiebreaker."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Mix of priorities and durations
    pet.add_task(Task("P2-60min", "Task", 60, 2, Frequency.DAILY))
    pet.add_task(Task("P1-30min", "Task", 30, 1, Frequency.DAILY))
    pet.add_task(Task("P1-120min", "Task", 120, 1, Frequency.DAILY))
    pet.add_task(Task("P2-5min", "Task", 5, 2, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # Expected order: P1-30min, P1-120min, P2-5min, P2-60min
    assert (plan[0].priority, plan[0].duration) == (1, 30)
    assert (plan[1].priority, plan[1].duration) == (1, 120)
    assert (plan[2].priority, plan[2].duration) == (2, 5)
    assert (plan[3].priority, plan[3].duration) == (2, 60)


def test_sorting_multiple_pets_mixed_tasks():
    """Sorting works across all pets aggregated into single plan."""
    owner = Owner("Alice")
    
    dog = Pet(name="Max", type="Dog", age=5)
    dog.add_task(Task("Dog-P2", "Exercise", 30, 2, Frequency.DAILY))
    dog.add_task(Task("Dog-P1", "Feed", 5, 1, Frequency.DAILY))
    owner.add_pet(dog)
    
    cat = Pet(name="Whiskers", type="Cat", age=3)
    cat.add_task(Task("Cat-P3", "Groom", 40, 3, Frequency.DAILY))
    cat.add_task(Task("Cat-P2", "Play", 20, 2, Frequency.DAILY))
    owner.add_pet(cat)
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # All 4 tasks in priority order
    assert len(plan) == 4
    assert plan[0].priority == 1
    assert plan[1].priority == 2
    assert plan[2].priority == 2
    assert plan[3].priority == 3
    # P2 tasks should be sorted by duration
    assert plan[1].duration < plan[2].duration


# ============================================================================
# RECURRENCE LOGIC TESTS
# ============================================================================

def test_daily_task_hidden_from_plan_after_completion():
    """DAILY task disappears from today's plan after being marked done."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    pet.add_task(Task("Morning Walk", "Exercise", 30, 1, Frequency.DAILY))

    scheduler = Scheduler(owner)
    assert len(scheduler.generate_daily_plan()) == 1  # shows before completion

    scheduler.mark_task_complete("Morning Walk")
    assert len(scheduler.generate_daily_plan()) == 0  # hidden for rest of today
    assert len(pet.tasks) == 1  # no clone created


def test_daily_task_resets_for_new_day():
    """DAILY task shows up again when last_completed_date is a previous day."""
    from datetime import timedelta
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)

    task = Task("Morning Walk", "Exercise", 30, 1, Frequency.DAILY)
    task.last_completed_date = date.today() - timedelta(days=1)  # completed yesterday
    task.completed = True
    pet.add_task(task)

    scheduler = Scheduler(owner)
    assert len(scheduler.generate_daily_plan()) == 1  # back in today's plan


def test_twice_daily_shows_one_slot_after_first_completion():
    """After completing a TWICE_DAILY task once, only 1 slot remains."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    pet.add_task(Task("Feed", "Meal", 5, 2, Frequency.TWICE_DAILY))

    scheduler = Scheduler(owner)
    assert len(scheduler.generate_daily_plan()) == 2  # starts with 2 slots

    scheduler.mark_task_complete("Feed")
    assert len(scheduler.generate_daily_plan()) == 1  # 1 slot remaining
    assert len(pet.tasks) == 1  # no clone created


def test_weekly_task_hidden_after_completion_no_clone():
    """WEEKLY task is hidden after completion; no clone is created."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    pet.add_task(Task("Groom", "Grooming", 60, 1, Frequency.WEEKLY))

    scheduler = Scheduler(owner)
    assert len(scheduler.generate_daily_plan()) == 1

    scheduler.mark_task_complete("Groom")
    assert len(scheduler.generate_daily_plan()) == 0
    assert len(pet.tasks) == 1  # no clone created


def test_as_needed_task_no_next_occurrence():
    """Marking AS_NEEDED task complete does NOT create next occurrence."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    task = Task("Medication", "Health", 5, 1, Frequency.AS_NEEDED)
    pet.add_task(task)
    
    assert len(pet.tasks) == 1
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Medication")

    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_recurrence_updates_last_completed_date():
    """Task completion updates last_completed_date to today."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    task = Task("Walk", "Exercise", 30, 1, Frequency.DAILY)
    pet.add_task(task)
    
    assert task.last_completed_date is None
    
    task.mark_complete()
    
    assert task.last_completed_date == date.today()


def test_recurrence_tracks_times_completed_today():
    """Marking task complete twice in one day increments times_completed_today."""
    task = Task("Feed", "Meal", 5, 2, Frequency.TWICE_DAILY)
    
    assert task.times_completed_today == 0
    task.mark_complete()
    assert task.times_completed_today == 1
    task.mark_complete()
    assert task.times_completed_today == 2


def test_recurrence_resets_times_completed_next_day():
    """times_completed_today resets on next day."""
    task = Task("Feed", "Meal", 5, 2, Frequency.TWICE_DAILY)
    
    task.mark_complete()
    assert task.times_completed_today == 1
    assert task.last_completed_date == date.today()
    
    # Simulate next day by manually setting last_completed_date
    task.last_completed_date = date.today() - timedelta(days=1)
    task.mark_complete()
    
    # Should reset and increment
    assert task.times_completed_today == 1


def test_twice_daily_appears_twice_in_plan():
    """TWICE_DAILY task appears exactly twice in daily plan."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    pet.add_task(Task("Feed", "Meal", 5, 1, Frequency.TWICE_DAILY))
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # Same task instance appears twice
    feed_count = sum(1 for t in plan if t.title == "Feed")
    assert feed_count == 2


def test_daily_appears_once_in_plan():
    """DAILY task appears exactly once in plan."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    pet.add_task(Task("Walk", "Exercise", 30, 1, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    walk_count = sum(1 for t in plan if t.title == "Walk")
    assert walk_count == 1


def test_as_needed_appears_once_in_plan():
    """AS_NEEDED task appears exactly once in plan."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    pet.add_task(Task("Medication", "Health", 5, 1, Frequency.AS_NEEDED))
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    med_count = sum(1 for t in plan if t.title == "Medication")
    assert med_count == 1


# ============================================================================
# CONFLICT DETECTION TESTS
# ============================================================================

def test_no_conflict_when_within_daily_limit():
    """No conflict flagged when total pet task duration ≤ 120 minutes."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # 3 tasks × 30 min = 90 min total (under 120)
    pet.add_task(Task("Walk1", "Exercise", 30, 1, Frequency.DAILY))
    pet.add_task(Task("Walk2", "Exercise", 30, 2, Frequency.DAILY))
    pet.add_task(Task("Feed", "Meal", 30, 3, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert len(conflicts) == 0


def test_conflict_when_exceeds_daily_limit():
    """Conflict flagged when total pet task duration > owner's available minutes."""
    owner = Owner("Alice", availability="9am-11am")  # 120 min window
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)

    # 3 tasks × 50 min = 150 min total (over 120 min window)
    pet.add_task(Task("Walk1", "Exercise", 50, 1, Frequency.DAILY))
    pet.add_task(Task("Walk2", "Exercise", 50, 2, Frequency.DAILY))
    pet.add_task(Task("Feed", "Meal", 50, 3, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert len(conflicts) > 0
    assert "HIGH LOAD" in conflicts[0][2]


def test_conflict_exactly_at_120_minute_boundary():
    """Exactly at the available window does NOT trigger conflict."""
    owner = Owner("Alice", availability="9am-11am")  # 120 min window
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)

    # Exactly 120 min (equal to window — no conflict)
    pet.add_task(Task("Task1", "Exercise", 60, 1, Frequency.DAILY))
    pet.add_task(Task("Task2", "Exercise", 60, 2, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert len(conflicts) == 0


def test_conflict_just_over_120_minute_boundary():
    """One minute over the available window triggers a conflict."""
    owner = Owner("Alice", availability="9am-11am")  # 120 min window
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)

    # 121 min total (1 min over the window)
    pet.add_task(Task("Task1", "Exercise", 60, 1, Frequency.DAILY))
    pet.add_task(Task("Task2", "Exercise", 61, 2, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert len(conflicts) > 0


def test_conflict_detection_multiple_pets():
    """Conflict detection uses the combined task duration across all pets."""
    owner = Owner("Alice", availability="9am-11am")  # 120 min window

    dog = Pet(name="Max", type="Dog", age=5)
    dog.add_task(Task("Walk", "Exercise", 80, 1, Frequency.DAILY))
    owner.add_pet(dog)

    cat = Pet(name="Whiskers", type="Cat", age=3)
    cat.add_task(Task("Feed", "Meal", 50, 1, Frequency.DAILY))
    owner.add_pet(cat)
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert len(conflicts) == 1
    assert "HIGH LOAD" in conflicts[0][2]
    assert "Alice" in conflicts[0][2]


def test_conflict_message_format():
    """Conflict warning contains pet name and task titles."""
    owner = Owner("Alice", availability="9am-11am")  # 120 min window
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)

    # 130 min total (over 120 min window)
    pet.add_task(Task("Walk", "Exercise", 80, 1, Frequency.DAILY))
    pet.add_task(Task("Play", "Exercise", 50, 2, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert len(conflicts) > 0
    warning = conflicts[0][2]
    assert "Alice" in warning
    """Weekly tasks skipped don't count toward conflict load."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # WEEKLY task completed 2 days ago (will be skipped)
    weekly_task = Task("Groom", "Grooming", 100, 1, Frequency.WEEKLY)
    weekly_task.last_completed_date = date.today() - timedelta(days=2)
    pet.add_task(weekly_task)
    
    # DAILY task
    pet.add_task(Task("Walk", "Exercise", 50, 2, Frequency.DAILY))
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    # Only walk counts (50 min), no conflict
    assert len(conflicts) == 0


def test_conflict_detection_empty_pet_no_error():
    """Pet with no tasks doesn't cause error in conflict detection."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    # No tasks added
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    # Should complete without error
    assert len(conflicts) == 0


def test_conflict_detection_no_pets_empty_list():
    """Scheduler with no pets returns empty conflict list."""
    owner = Owner("Alice")
    # No pets
    
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    
    assert conflicts == []


# ============================================================================
# EDGE CASE: WEEKLY TASK 7-DAY BOUNDARY
# ============================================================================

def test_weekly_task_completed_within_7_days_is_skipped():
    """Weekly task completed less than 7 days ago is SKIPPED."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Task completed 6 days ago
    task = Task("Groom", "Grooming", 30, 1, Frequency.WEEKLY)
    task.last_completed_date = date.today() - timedelta(days=6)
    pet.add_task(task)
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # Should be skipped
    assert len(plan) == 0


def test_weekly_task_completed_exactly_7_days_ago_included():
    """Weekly task completed exactly 7 days ago is INCLUDED."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Task completed exactly 7 days ago
    task = Task("Groom", "Grooming", 30, 1, Frequency.WEEKLY)
    task.last_completed_date = date.today() - timedelta(days=7)
    pet.add_task(task)
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    # Should be included (7 < 7 is False)
    assert len(plan) == 1
    assert plan[0].title == "Groom"


def test_weekly_task_never_completed_included():
    """Weekly task never completed is INCLUDED in plan."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Task never completed
    task = Task("Groom", "Grooming", 30, 1, Frequency.WEEKLY)
    pet.add_task(task)
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    assert len(plan) == 1
    assert plan[0].title == "Groom"


# ============================================================================
# EDGE CASE: EMPTY STATES
# ============================================================================

def test_empty_owner_no_pets():
    """Owner with no pets generates empty plan."""
    owner = Owner("Alice")
    # No pets
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    assert plan == []


def test_pet_with_no_tasks():
    """Pet with no tasks doesn't appear in plan."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    # No tasks added
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    assert plan == []


def test_multiple_pets_no_tasks():
    """Multiple pets with no tasks generates empty plan."""
    owner = Owner("Alice")
    owner.add_pet(Pet(name="Max", type="Dog", age=5))
    owner.add_pet(Pet(name="Whiskers", type="Cat", age=3))
    # No tasks
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    
    assert plan == []


# ============================================================================
# SMART PRIORITIZATION TESTS
# ============================================================================

def test_smart_plan_orders_by_weighted_score():
    """Smart plan orders tasks by weighted priority score (descending)."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Mix of priorities, frequencies, and recency
    pet.add_task(Task("Walk", "Exercise", 30, 2, Frequency.DAILY))  # P2 normal
    pet.add_task(Task("Feed", "Meal", 5, 3, Frequency.TWICE_DAILY))  # P3 high freq
    pet.add_task(Task("Groom", "Grooming", 60, 1, Frequency.WEEKLY))  # P1 low freq
    
    scheduler = Scheduler(owner)
    plan = scheduler.generate_smart_daily_plan()
    
    # Verify plan is sorted by score (descending)
    scores = [scheduler.calculate_weighted_priority_score(t) for t in plan]
    assert scores == sorted(scores, reverse=True)


def test_smart_plan_never_completed_highest_recency():
    """Never-completed task gets maximum recency boost."""
    owner = Owner("Alice")
    pet = Pet(name="Max", type="Dog", age=5)
    owner.add_pet(pet)
    
    # Never completed task (no last_completed_date)
    task1 = Task("Walk", "Exercise", 30, 3, Frequency.DAILY)
    
    # Completed today
    task2 = Task("Feed", "Meal", 5, 3, Frequency.DAILY)
    task2.last_completed_date = date.today()
    
    pet.add_task(task1)
    pet.add_task(task2)
    
    scheduler = Scheduler(owner)
    score1 = scheduler.calculate_weighted_priority_score(task1)
    score2 = scheduler.calculate_weighted_priority_score(task2)
    
    # Never-completed should have higher score
    assert score1 > score2
