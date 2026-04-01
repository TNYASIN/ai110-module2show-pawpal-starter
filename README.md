# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
# CLI demo (see all features)
python main.py

# Streamlit web UI
streamlit run app.py
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## 🌟 Smarter Scheduling: Advanced Features

This implementation goes beyond basic scheduling with three algorithmic capabilities:

### 1. **Recurring Task Automation** ✨

When a recurring task (DAILY, TWICE_DAILY, WEEKLY) is marked complete, the system automatically creates a new instance for the next occurrence. This keeps the task pool fresh without manual re-adding.

**How it works:**
```python
scheduler.mark_task_complete("Morning Walk")  # Marks as complete
# → Auto-creates new "Morning Walk" for tomorrow
```

**Benefit:** Reduces data entry; ensures daily/weekly tasks always appear in future plans.

**Use case:** Owner checks off "Morning Walk" once at 7am; system resets it for tomorrow automatically.

---

### 2. **Lightweight Conflict Detection** ⚠️

Detects when a pet is scheduled for more tasks than reasonable in a single day (>120 min), and alerts the owner to avoid unrealistic schedules.

**How it works:**
```python
scheduler.print_conflicts()
# Output: "⚠️ HIGH LOAD: Luna has 150 min of tasks. Consider spreading or adjusting priorities."
```

**Strategy:** Lightweight, non-blocking approach—warns rather than crashes. Doesn't assign exact clock times; assumes sequential task execution. Owners manually resolve conflicts by adjusting priorities.

**Benefit:** Prevents over-scheduling before the day starts; highlights resource constraints early.

---

### 3. **Weighted Priority Scoring** 🧠 (Advanced)

An intelligent scheduler that scores tasks across multiple dimensions: **base priority + recency + frequency pattern**. This goes beyond simple priority sorting.

**Scoring formula:**
```
Score = (priority_weight × priority_score) 
       + (recency_weight × days_since_last_done)
       + (frequency_weight × frequency_multiplier)

Default weights: 50% priority, 30% recency, 20% frequency
```

**Example:** 
- Task A: priority 2, not done in 5 days, DAILY → score 2.65
- Task B: priority 1, never done, TWICE_DAILY → score 3.04
- Result: Task B ranked first (higher score = more urgent)

**How to use:**
```python
scheduler.view_smart_plan()  # Instead of scheduler.view_plan()
```

**Benefit:** Smarter task ordering for owners with complex schedules. Ensures high-frequency medical tasks stay top-of-mind and overdue tasks get priority boosts.

---

## 🤖 How Agent Mode Was Used

This project leveraged **Copilot Agent Mode** to iteratively develop and refine the scheduling algorithms:

### Phase 1: Initial Analysis
- **Agent Exploration:** Used Copilot to analyze the codebase and identify improvement opportunities
- **Suggested:** Implemented recurring task automation, conflict detection, and weighted prioritization
- **Agent benefit:** Rapid brainstorming of algorithmic enhancements without manual codebase review

### Phase 2: Weighted Priority Implementation
- **Challenge:** How to combine multiple scoring dimensions (priority + recency + frequency) without hardcoding?
- **Agent Mode:** Asked Copilot: *"How can I weight three factors (priority, recency, frequency) to create a composite urgency score?"*
- **Solution received:** Composite scoring with configurable weights (dict of multipliers)
- **Implementation:** `calculate_weighted_priority_score()` method with Dict[str, float] weights parameter
- **Agent benefit:** Got a mathematically clean, extensible design instead of trial-and-error

### Phase 3: Conflict Detection Strategy
- **Challenge:** Exact time-slot allocation is complex (requires owner availability windows, pet location, etc.)
- **Agent Mode:** Asked: *"What's a lightweight conflict detection strategy that warns rather than crashes?"*
- **Solution received:** Check total daily load per pet against reasonable threshold (120 min/day)
- **Implementation:** `detect_conflicts()` returns list of (task1, task2, warning) tuples
- **Agent benefit:** Avoided over-engineering; got a practical, maintainable approach

### Phase 4: Recurring Task Logic
- **Challenge:** How to use Python's `timedelta` to calculate next occurrence dates?
- **Agent Mode:** Asked: *"Show me how to calculate next_date = today + timedelta(days=1) for daily tasks"*
- **Solution received:** Used `deepcopy()` to clone task; reset completion dates; let scheduler handle slot generation
- **Implementation:** `create_next_occurrence()` method; `mark_task_complete()` integrates recurrence
- **Agent benefit:** Avoided reinventing task scheduling; reused existing frequency logic

### Key Takeaway
**Agent Mode accelerated algorithm design** by:
1. Explaining tradeoffs (exact scheduling vs. lightweight warnings)
2. Suggesting patterns (weighted scoring with Dict weights, deepcopy for task duplication)
3. Validating edge cases (e.g., TWICE_DAILY + WEEKLY combinations)

The result: clean, maintainable code that went beyond "make it work" to "make it smart."

---

## Architecture

```
Owner (single source of truth)
├── Pet 1
│   ├── name, type, age, special_needs[]
│   └── tasks[] (Task objects)
├── Pet 2
│   └── tasks[] (Task objects)
└── availability, preferences

Scheduler (reads from Owner)
├── generate_daily_plan() — Simple priority/duration sort
├── generate_smart_daily_plan() — Weighted priority scoring
├── detect_conflicts() — Warn on high daily load
└── mark_task_complete() — Mark complete + auto-create next occurrence
```

---

## Testing

Run the demo to see all three features in action:

```bash
python main.py
```

Output shows:
1. Basic daily plan (simple sorting)
2. Task filtering (by duration, by priority)
3. Conflict warnings (high load detection)
4. Smart plan (weighted priority scoring with scores)
5. Recurring task automation (mark complete → auto-create next)

---
