from dataclasses import dataclass, field
from typing import List


@dataclass
class Pet:
    name: str
    type: str
    age: int
    special_needs: List[str] = field(default_factory=list)

    def update_basic_info(self, name: str = None, type: str = None, age: int = None):
        pass

    def add_special_need(self, need: str):
        pass


@dataclass
class Task:
    title: str
    type: str
    duration: int       # in minutes
    priority: int       # 1 = highest
    frequency: str      # e.g. "daily", "twice daily"
    notes: str = ""

    def update_task(self, **kwargs):
        pass

    def set_duration(self, duration: int):
        pass

    def set_priority(self, priority: int):
        pass

    def set_frequency(self, frequency: str):
        pass


class Owner:
    def __init__(self, name: str, availability: str = "", preferences: str = ""):
        self.name = name
        self.availability = availability
        self.preferences = preferences
        self.pets: List[Pet] = []
        self.tasks: List[Task] = []

    def update_info(self, name: str = None, contact: str = None):
        pass

    def set_availability(self, availability: str):
        pass

    def set_preferences(self, preferences: str):
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: List[Task] = []
        self.pets: List[Pet] = []

    def generate_daily_plan(self) -> List[Task]:
        pass

    def view_plan(self):
        pass

    def edit_plan(self, task_title: str, **kwargs):
        pass

    def filter_by_duration(self, max_duration: int) -> List[Task]:
        pass

    def filter_by_priority(self, priority: int) -> List[Task]:
        pass
