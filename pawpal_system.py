from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum
from datetime import date, timedelta


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
        today = date.today()
        if self.last_completed_date != today:
            self.times_completed_today = 0  # new day — reset counter
        self.times_completed_today += 1
        self.last_completed_date = today
        self.completed = True

    def is_done(self, slot: int = 1) -> bool:
        """Whether this task's nth slot has been completed today.
        Accounts for day boundaries so previous-day completions don't show as done.
        slot is only meaningful for TWICE_DAILY (1 or 2).
        """
        today = date.today()
        if self.frequency == Frequency.TWICE_DAILY:
            completed_today = (self.last_completed_date == today)
            done_count = self.times_completed_today if completed_today else 0
            return done_count >= slot
        elif self.frequency == Frequency.WEEKLY:
            return bool(self.last_completed_date and
                        (today - self.last_completed_date).days < 7)
        elif self.frequency == Frequency.DAILY:
            return self.last_completed_date == today
        else:  # AS_NEEDED
            return self.completed
    

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

    def get_available_minutes(self) -> int:
        """Parse availability string into total available minutes.

        Handles formats like '8am-6pm', '9:00-17:00', '8h', '8 hours', and '480 min'.
        Returns 480 (8 hours) as a safe default if the string can't be parsed.
        """
        import re
        if not self.availability:
            return 480

        text = self.availability.strip().lower()

        # Handle explicit hour-based values like '8h' or '8 hours'
        hour_match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(h|hr|hrs|hour|hours)$", text)
        if hour_match:
            hours = float(hour_match.group(1))
            return max(int(hours * 60), 60)

        # Handle explicit minute-based values like '480 min' or '480 minutes'
        minute_match = re.match(r"^([0-9]+)\s*(m|min|mins|minute|minutes)$", text)
        if minute_match:
            minutes = int(minute_match.group(1))
            return max(minutes, 60)

        # Match patterns like "8am-6pm", "8:30am-5:30pm", "9:00-17:00"
        pattern = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*[-–]\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
        match = re.search(pattern, text)
        if match:
            start_h, start_m, start_period, end_h, end_m, end_period = match.groups()
            start_h, end_h = int(start_h), int(end_h)
            start_m = int(start_m) if start_m else 0
            end_m = int(end_m) if end_m else 0

            # Convert to 24h
            if start_period == "pm" and start_h != 12:
                start_h += 12
            if start_period == "am" and start_h == 12:
                start_h = 0
            if end_period == "pm" and end_h != 12:
                end_h += 12
            if end_period == "am" and end_h == 12:
                end_h = 0

            total = (end_h * 60 + end_m) - (start_h * 60 + start_m)
            return max(total, 60)

        return 480

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
                if task.is_done():
                    continue
                slots.append(task)
            elif task.frequency == Frequency.TWICE_DAILY:
                # Only include remaining (uncompleted) slots for today
                completed_today = (task.last_completed_date == today)
                done_count = task.times_completed_today if completed_today else 0
                for _ in range(2 - done_count):
                    slots.append(task)
            elif task.frequency == Frequency.DAILY:
                if task.is_done():
                    continue  # done today; reappears tomorrow
                slots.append(task)
            else:  # AS_NEEDED
                slots.append(task)

        return sorted(slots, key=lambda t: (t.priority, t.duration))
    
    def detect_conflicts(self, plan: List[Task] = None) -> List[Tuple[Task, Task, str]]:
        """Detect schedule conflicts based on the owner's total available minutes.

        If a plan is supplied, conflict detection evaluates that exact schedule.
        Otherwise it falls back to the standard daily plan.
        """
        if plan is None:
            plan = self.generate_daily_plan()

        daily_limit = self.owner.get_available_minutes()
        total_duration = sum(t.duration for t in plan)

        if total_duration <= daily_limit:
            return []

        task1 = plan[0] if plan else None
        task2 = plan[1] if len(plan) > 1 else (plan[0] if plan else None)
        warning = (
            f"⚠️ HIGH LOAD: the schedule has {total_duration} min of tasks today "
            f"but {self.owner.name} is available for {daily_limit} min "
            f"({self.owner.availability or 'no availability set'}). "
            f"'{task1.title if task1 else 'Task'}' and '{task2.title if task2 else 'Task'}' may not both fit. "
            "Consider spreading tasks or adjusting priorities."
        )

        return [(task1, task2, warning)] if task1 and task2 else []
    
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
                if task.is_done():
                    continue
                slots.append(task)
            elif task.frequency == Frequency.TWICE_DAILY:
                completed_today = (task.last_completed_date == today)
                done_count = task.times_completed_today if completed_today else 0
                for _ in range(2 - done_count):
                    slots.append(task)
            elif task.frequency == Frequency.DAILY:
                if task.is_done():
                    continue
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

    def mark_task_complete(self, task_title: str) -> None:
        """Mark a task complete. Recurrence is handled automatically by date tracking —
        daily tasks reappear tomorrow, twice-daily after the second slot, weekly after 7 days.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.title == task_title:
                    task.mark_complete()
                    return
        raise ValueError(f"Task '{task_title}' not found.")
