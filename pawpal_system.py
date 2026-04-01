from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum
from datetime import date, timedelta
from copy import deepcopy


class Frequency(Enum):
    DAILY = "daily"
    TWICE_DAILY = "twice daily"
    WEEKLY = "weekly"
    AS_NEEDED = "as needed"


@dataclass
class Task:
    """A single pet care activity."""
    title: str
    type: str
    duration: int           # in minutes
    priority: int           # 1 = highest
    frequency: Frequency
    pet_name: str = ""      # name of the pet this task belongs to
    notes: str = ""
    completed: bool = False
    last_completed_date: Optional[date] = None
    times_completed_today: int = 0

    def update_task(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_duration(self, duration: int):
        self.duration = duration

    def set_priority(self, priority: int):
        self.priority = priority

    def set_frequency(self, frequency: Frequency):
        self.frequency = frequency

    def mark_complete(self):
        """Mark task as complete and set completion date.
        
        For recurring tasks (DAILY, TWICE_DAILY, WEEKLY), also returns
        a new task instance for the next occurrence.
        """
        today = date.today()
        if self.last_completed_date != today:
            self.times_completed_today = 0
        self.times_completed_today += 1
        self.last_completed_date = today
        self.completed = True
    
    def create_next_occurrence(self) -> Optional['Task']:
        """Create a new task instance for the next occurrence if frequency is recurring.
        
        Returns:
            A new Task with updated due date for daily/weekly tasks, or None for AS_NEEDED.
        """
        if self.frequency == Frequency.AS_NEEDED:
            return None
        
        # Create a deep copy of the current task
        next_task = deepcopy(self)
        next_task.completed = False
        next_task.times_completed_today = 0
        
        # Calculate next due date based on frequency
        if self.frequency == Frequency.DAILY:
            next_task.last_completed_date = None
        elif self.frequency == Frequency.TWICE_DAILY:
            next_task.last_completed_date = None
        elif self.frequency == Frequency.WEEKLY:
            # For weekly tasks, reset so they can appear in next week's plan
            next_task.last_completed_date = None
        
        return next_task

    def __str__(self):
        status = "✓" if self.completed else "○"
        pet_label = f" [{self.pet_name}]" if self.pet_name else ""
        return (f"{status} {self.title}{pet_label} | {self.type} | "
                f"{self.duration} min | priority {self.priority} | {self.frequency.value}")


@dataclass
class Pet:
    """Stores pet details and owns its list of care tasks."""
    name: str
    type: str
    age: int
    special_needs: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def update_basic_info(self, name: str = None, type: str = None, age: int = None):
        if name is not None:
            self.name = name
        if type is not None:
            self.type = type
        if age is not None:
            self.age = age

    def add_special_need(self, need: str):
        if need not in self.special_needs:
            self.special_needs.append(need)

    def add_task(self, task: Task):
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, title: str):
        self.tasks = [t for t in self.tasks if t.title != title]

    def __str__(self):
        needs = ", ".join(self.special_needs) if self.special_needs else "none"
        return f"{self.name} ({self.type}, age {self.age}) | special needs: {needs}"


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str, availability: str = "", preferences: str = ""):
        self.name = name
        self.availability = availability
        self.preferences = preferences
        self.pets: List[Pet] = []

    def update_info(self, name: str = None):
        if name is not None:
            self.name = name

    def set_availability(self, availability: str):
        self.availability = availability

    def set_preferences(self, preferences: str):
        self.preferences = preferences

    def add_pet(self, pet: Pet):
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> List[Task]:
        """Collect every task across all pets — Scheduler reads from here."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __str__(self):
        return (f"Owner: {self.name} | availability: {self.availability} | "
                f"preferences: {self.preferences} | pets: {len(self.pets)}")


class Scheduler:
    """Retrieves, organizes, and manages tasks across all pets via the Owner."""

    def __init__(self, owner: Owner):
        self.owner = owner  # single source of truth

    def generate_daily_plan(self) -> List[Task]:
        """Build today's schedule respecting frequency rules:
        - TWICE_DAILY  → task appears twice (two slots)
        - DAILY        → appears once
        - WEEKLY       → skipped if already completed this week
        - AS_NEEDED    → appears once
        """
        today = date.today()
        slots: List[Task] = []

        for task in self.owner.get_all_tasks():
            if task.frequency == Frequency.WEEKLY:
                # skip if completed within the last 7 days
                if task.last_completed_date and (today - task.last_completed_date).days < 7:
                    continue
                slots.append(task)
            elif task.frequency == Frequency.TWICE_DAILY:
                # add two slots; mark label with (1/2) and (2/2)
                slots.append(task)
                slots.append(task)
            else:
                # DAILY or AS_NEEDED
                slots.append(task)

        return sorted(slots, key=lambda t: (t.priority, t.duration))
    
    def detect_conflicts(self, assume_sequential: bool = False) -> List[Tuple[Task, Task, str]]:
        """Detect task conflicts where two tasks for the same pet would overlap in time.
        
        This uses a lightweight strategy:
        - By default, assumes all tasks are scheduled sequentially (no overlaps if they fit)
        - If assume_sequential=False, flags any two tasks on same pet for the same day
          (warns that they need time-slot assignment to avoid conflicts)
        
        Args:
            assume_sequential: If True, only warns if total duration exceeds a reasonable daily limit
            
        Returns:
            List of tuples (task1, task2, warning_message) for detected conflicts.
        """
        conflicts: List[Tuple[Task, Task, str]] = []
        all_tasks = self.owner.get_all_tasks()
        
        # Group tasks by pet to check same-pet scheduling
        tasks_by_pet = {}
        for task in all_tasks:
            if task.pet_name not in tasks_by_pet:
                tasks_by_pet[task.pet_name] = []
            tasks_by_pet[task.pet_name].append(task)
        
        # For each pet, check if total daily task time is reasonable
        plan = self.generate_daily_plan()
        for pet_name, pet_tasks in tasks_by_pet.items():
            # Get tasks for this pet in today's plan
            pet_plan_tasks = [t for t in plan if t.pet_name == pet_name]
            
            if pet_plan_tasks:
                total_duration = sum(t.duration for t in pet_plan_tasks)
                # Flag if total exceeds reasonable daily limit (e.g., 120 minutes per pet)
                if total_duration > 120:
                    for i, task1 in enumerate(pet_plan_tasks):
                        for task2 in pet_plan_tasks[i + 1:]:
                            warning = (
                                f"⚠️ HIGH LOAD: {pet_name} has {total_duration} min of tasks today. "
                                f"'{task1.title}' and '{task2.title}' may need scheduling. "
                                f"Consider spreading tasks or adjusting priorities."
                            )
                            # Only add once per pet, not per task pair
                            if not any(w[2] == warning for w in conflicts):
                                conflicts.append((task1, task2, warning))
                            return conflicts
        
        return conflicts
    
    def print_conflicts(self):
        """Print all detected conflicts in a user-friendly format."""
        conflicts = self.detect_conflicts()
        if not conflicts:
            print("✓ No scheduling conflicts detected.")
        else:
            print(f"\n{len(conflicts)} conflict(s) found:")
            for task1, task2, warning in conflicts:
                print(f"  {warning}")
    
    def calculate_weighted_priority_score(self, task: Task, weights: Dict[str, float] = None) -> float:
        """Calculate a weighted priority score for a task based on multiple factors.
        
        Factors considered:
        - Base priority (1-5): Lower is more urgent
        - Recency: How many days since last completed (more days = higher urgency)
        - Frequency multiplier: Weekly tasks get priority boost, as-needed tasks deprioritized
        
        Args:
            task: The task to score
            weights: Dict with keys 'priority', 'recency', 'frequency'. Defaults to balanced weights.
        
        Returns:
            A composite score (higher = more urgent). Can be negative.
        """
        if weights is None:
            weights = {
                'priority': 0.5,      # Base priority weight (lower number = more important)
                'recency': 0.3,       # Days since completion weight
                'frequency': 0.2      # Frequency multiplier weight
            }
        
        today = date.today()
        
        # Priority component (inverse: lower priority number = higher score)
        # Maps 1→5, 2→4, 3→3, 4→2, 5→1
        priority_score = (6 - task.priority) * weights['priority']
        
        # Recency component (days since last completion)
        recency_score = 0.0
        if task.last_completed_date:
            days_since = (today - task.last_completed_date).days
            # Score increases with days since completion (max 10 days = full score)
            recency_score = min(days_since / 10.0, 1.0) * weights['recency']
        else:
            # Never completed: maximum recency urgency
            recency_score = weights['recency']
        
        # Frequency component (recurring tasks get boosted)
        frequency_multipliers = {
            Frequency.DAILY: 1.0,
            Frequency.TWICE_DAILY: 1.2,  # Extra urgent due to high frequency
            Frequency.WEEKLY: 0.8,
            Frequency.AS_NEEDED: 0.5,    # Lowest priority
        }
        frequency_score = frequency_multipliers.get(task.frequency, 0.5) * weights['frequency']
        
        # Composite score
        return priority_score + recency_score + frequency_score
    
    def generate_smart_daily_plan(self) -> List[Task]:
        """Generate a daily plan using weighted prioritization instead of simple sorting.
        
        Uses calculate_weighted_priority_score to order tasks by urgency across
        multiple dimensions: importance, recency, and frequency patterns.
        
        Returns:
            Sorted list of tasks for the day, ordered by composite urgency score (descending).
        """
        today = date.today()
        slots: List[Task] = []

        # Collect slots respecting frequency rules (same as generate_daily_plan)
        for task in self.owner.get_all_tasks():
            if task.frequency == Frequency.WEEKLY:
                if task.last_completed_date and (today - task.last_completed_date).days < 7:
                    continue
                slots.append(task)
            elif task.frequency == Frequency.TWICE_DAILY:
                slots.append(task)
                slots.append(task)
            else:
                slots.append(task)

        # Sort by weighted priority score (descending = most urgent first)
        return sorted(slots, key=lambda t: self.calculate_weighted_priority_score(t), reverse=True)
    
    def view_smart_plan(self):
        """Display the daily plan generated by smart weighted prioritization."""
        plan = self.generate_smart_daily_plan()
        if not plan:
            print("No tasks scheduled.")
            return
        today = date.today()
        print(f"\n🧠 SMART Daily plan for {self.owner.name} — {today}:")
        print("(Ordered by weighted priority: importance + recency + frequency)")
        print("-" * 60)
        seen: dict = {}
        for task in plan:
            seen[task.title] = seen.get(task.title, 0) + 1
            slot_label = f" ({seen[task.title]}/2)" if task.frequency == Frequency.TWICE_DAILY else ""
            status = "✓" if task.completed else "○"
            pet_label = f" [{task.pet_name}]" if task.pet_name else ""
            score = self.calculate_weighted_priority_score(task)
            print(f"  {status} {task.title}{slot_label}{pet_label} | "
                  f"{task.duration} min | priority {task.priority} | "
                  f"score: {score:.2f}")
        print("-" * 60)

    def view_plan(self):
        plan = self.generate_daily_plan()
        if not plan:
            print("No tasks scheduled.")
            return
        today = date.today()
        print(f"\nDaily plan for {self.owner.name} — {today}:")
        print("-" * 50)
        seen: dict = {}
        for task in plan:
            seen[task.title] = seen.get(task.title, 0) + 1
            slot_label = f" ({seen[task.title]}/2)" if task.frequency == Frequency.TWICE_DAILY else ""
            status = "✓" if task.completed else "○"
            pet_label = f" [{task.pet_name}]" if task.pet_name else ""
            print(f"  {status} {task.title}{slot_label}{pet_label} | "
                  f"{task.duration} min | priority {task.priority} | {task.frequency.value}")
        print("-" * 50)

    def edit_plan(self, task_title: str, **kwargs):
        """Find a task by title across all pets and update its fields."""
        for task in self.owner.get_all_tasks():
            if task.title == task_title:
                task.update_task(**kwargs)
                return
        raise ValueError(f"Task '{task_title}' not found.")

    def filter_by_duration(self, max_duration: int) -> List[Task]:
        return [t for t in self.owner.get_all_tasks() if t.duration <= max_duration]

    def filter_by_priority(self, priority: int) -> List[Task]:
        return [t for t in self.owner.get_all_tasks() if t.priority == priority]

    def mark_task_complete(self, task_title: str) -> Optional[Task]:
        """Mark a task as complete by title across all pets.
        
        For recurring tasks, automatically creates a new instance for the next occurrence.
        
        Args:
            task_title: The title of the task to mark complete
            
        Returns:
            The newly created recurring task, or None if task is AS_NEEDED or not found
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.title == task_title:
                    task.mark_complete()
                    
                    # Create next occurrence for recurring tasks
                    next_task = task.create_next_occurrence()
                    if next_task:
                        pet.add_task(next_task)
                        return next_task
                    return None
        
        raise ValueError(f"Task '{task_title}' not found.")
