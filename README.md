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

## Testing PawPal+

### Run the tests

```bash
python -m pytest
```

### What the tests cover

| Area | What is tested |
|---|---|
| **Task completion** | `mark_complete()` flips `completed` to `True` and records today's date |
| **Pet task count** | `add_task()` increases `pet.tasks` length by 1 each time |
| **Schedule sorting** | Daily plan orders by priority first, then duration as a tiebreaker |
| **Frequency — twice daily** | Task appears twice as separate slots in the generated plan |
| **Frequency — weekly** | Task is hidden from the plan if completed within the last 7 days; reappears after 7 days |
| **Frequency — daily / as-needed** | Each appears exactly once in the plan |
| **Recurrence tracking** | `times_completed_today` resets on a new day; `last_completed_date` is stamped correctly |
| **Conflict detection** | Flags pets whose total daily task time exceeds 120 minutes; no false positives under the limit |
| **Edge cases** | Owner with no pets, pets with no tasks, and empty schedulers all return gracefully |
| **Smart prioritization** | Weighted score ranks never-completed tasks above recently-completed ones |

### Confidence level

★★★★☆ (4/5)

Core scheduling logic — sorting, frequency rules, conflict detection, and task completion — is well covered by 34 passing tests. The one gap is end-to-end UI behavior: session state persistence and form interactions in Streamlit are not tested at the unit level, so edge cases in the web interface would require manual verification or a separate UI testing tool.
