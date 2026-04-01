from pawpal_system import Owner, Pet, Task, Scheduler, Frequency


def make_task(title="Morning Walk", priority=1, duration=30, frequency=Frequency.DAILY):
    return Task(title=title, type="Exercise", duration=duration, priority=priority, frequency=frequency)


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
