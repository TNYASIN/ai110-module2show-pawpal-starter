# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?


Three core actions the user needs to perform:

Add and manage pet and owner information
Create and manage care tasks
Generate and view a daily care plan

My initial UML design has the following classes:

Owner class: stores basic user information (name, availability, preferences). had methods to update info and set availability and preferences.

Pet class: stores pet details (name, type, age, special needs). has methods update basic info and add special needs.

Task class: represents a care task (walk, feeding, medication, etc.) with attributes like duration, priority, and frequency. has methods to update task, set a duration and set a priority.

Scheduler class: responsible for generating a daily plan based on tasks, priorities, and time constraints. had methods to allow viewing or editing or filtering by duration or priority.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design changed in several ways during implementation.

The most significant structural change was making `Owner` the single source of truth for pets and tasks. In the original skeleton, `Scheduler` kept its own `self.tasks` and `self.pets` lists alongside the owner's, which created two separate copies of the same data. If a task was added to the owner's pet, the scheduler's list would never know about it. Removing those duplicate lists from `Scheduler` and routing everything through `self.owner.get_all_tasks()` fixed this.

A second change was replacing the plain `frequency` string on `Task` with a `Frequency` enum. The original design used freeform strings like `"daily"` or `"twice daily"`, which made comparisons error-prone — a typo like `"Twice Daily"` would silently break scheduling logic. Switching to an enum (`Frequency.TWICE_DAILY`) made comparisons safe and also enabled the scheduler to apply real frequency rules, such as showing a twice-daily task twice in the plan and hiding a weekly task after it's been completed.

A third change was linking each `Task` to the pet it belongs to via a `pet_name` field, and moving task ownership to `Pet` instead of `Owner`. The initial design had `Owner` holding a flat `tasks` list, but that made it impossible to know which pet a task was for. Having `Pet` own its tasks and stamping each task with its `pet_name` when added made the schedule output meaningful.

I made the personal choice, to remove `contact` from `Owner`. Since contact information wasn't part of the scheduling logic, removing it kept the class focused.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers:
1. **Task frequency** (DAILY, TWICE_DAILY, WEEKLY, AS_NEEDED) — ensures recurring tasks appear at correct intervals
2. **Priority level** (1-5) — user-defined importance; lower number = higher urgency
3. **Task duration** — secondary sort within same priority
4. **Recency** (in smart mode) — tasks not completed in a while get boosted
5. **Reasonable daily load** (120 min per pet) — warns if overloaded

Constraints were prioritized by impact on pet welfare: frequency > priority > duration. We decided that recurring medical tasks (TWICE_DAILY) must always appear, followed by user-assigned priority, and finally optimizing for time efficiency.

**b. Tradeoffs**

**Tradeoff 1: Simple vs. Smart Scheduling**

The scheduler offers two modes:
- **Simple mode** (`generate_daily_plan`): Sort by priority then duration. Fast, predictable, easy to debug.
- **Smart mode** (`generate_smart_daily_plan`): Weighted scoring across priority + recency + frequency. More intelligent but adds complexity.

Why: Simple mode works well when owner manually manages task frequency. Smart mode helps when tasks have varied recency (e.g., "Vet checkup" hasn't been done in 3 months, needs boost). Owners can choose based on their workflow.

**Tradeoff 2: Exact Time-Slot Blocking vs. Sequential Assumption**

The conflict detector uses a lightweight strategy: it checks if total daily time exceeds 120 min per pet, rather than assigning exact clock times (9:00am walk, 10:00am feed, etc.).

Why: Exact time-slot allocation requires additional data (pet location, owner availability windows) we don't have. The sequential assumption (tasks happen back-to-back) is reasonable for a planning tool; the app warns owners when overloaded, and humans adjust priorities accordingly. A future enhancement could add time-slot optimization using bin-packing algorithms.

**Tradeoff 3: Automatic Recurrence vs. One-off Tasks**

When a recurring task is marked complete, we auto-create a new instance with reset dates.

Why: This keeps the task pool fresh without UI clutter. However, it means the task object ID changes, which could confuse persistence layers. Future versions might use task templates + completion records instead of duplication.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
