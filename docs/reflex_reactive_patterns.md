# Reflex Reactive Patterns Guide

## Overview
This guide documents best practices for working with Reflex's reactive system, based on real-world issues encountered and resolved during development.

## Table of Contents
1. [Understanding Reactive Vars](#understanding-reactive-vars)
2. [Common Pitfalls](#common-pitfalls)
3. [Safe Patterns](#safe-patterns)
4. [String Rendering](#string-rendering)
5. [Collections and Iteration](#collections-and-iteration)
6. [Comparisons and Conditionals](#comparisons-and-conditionals)
7. [Type Safety](#type-safety)

---

## Understanding Reactive Vars

### What are Reactive Vars?
In Reflex, state variables become "reactive Vars" when accessed in component render functions. These are proxy objects that enable:
- Client-side reactivity
- Automatic UI updates when state changes
- Type-safe data binding

### The Key Rule
**Never perform Python operations on reactive Vars at compile/render time.**

Python operations (like `>`, `<`, `len()`, list comprehensions) execute during component compilation, not at runtime. Reactive Vars are not regular Python values at this point.

---

## Common Pitfalls

### ❌ Pitfall 1: Direct Comparisons
```python
# WRONG - Python comparison on reactive Var
rx.cond(
    topic["due_today"] > 0,  # TypeError: '>' not supported
    rx.text("Due today"),
)
```

**Error:** `TypeError: '>' not supported between instances of 'ObjectItemOperation' and 'int'`

### ❌ Pitfall 2: List Comprehensions on State
```python
# WRONG - Iterating over reactive list
rx.select(
    [t["name"] for t in CardState.topics],  # VarTypeError
    placeholder="Select topic"
)
```

**Error:** `VarTypeError: Cannot iterate over Var 'CardState.topics'. Instead use rx.foreach.`

### ❌ Pitfall 3: f-strings with Vars
```python
# WRONG - f-string with reactive Var
rx.text(f"You have {ReviewState.count} cards")  # Evaluates at compile time
```

### ❌ Pitfall 4: Python len() on Reactive Lists
```python
# WRONG - Python len() on reactive list
rx.cond(
    len(DashboardState.topics) > 0,  # Evaluates at compile time
    rx.text("Has topics")
)
```

### ❌ Pitfall 5: Wrong Type Annotations
```python
# WRONG - float when component expects int
@rx.var
def progress_percentage(self) -> float:
    return ((self.current_index + 1) / len(self.cards)) * 100

# WRONG - Using in rx.progress which expects int
rx.progress(value=ReviewState.progress_percentage)  # TypeError
```

---

## Safe Patterns

### ✅ Pattern 1: Precompute Booleans in State
```python
class DashboardState(rx.State):
    topics: list[dict] = []
    has_topics: bool = False  # ← Precomputed boolean
    
    def load_topics(self):
        with rx.session() as session:
            topics_data = session.exec(select(Topic)).all()
            self.topics = [{"id": t.id, "name": t.name} for t in topics_data]
            self.has_topics = len(topics_data) > 0  # ← Python comparison in state method

# CORRECT - Use precomputed boolean
def dashboard_page():
    return rx.cond(
        DashboardState.has_topics,  # ← Simple boolean check
        rx.text("You have topics!"),
        rx.text("No topics yet")
    )
```

**Why it works:** The comparison happens in Python during `load_topics()`, not at render time.

### ✅ Pattern 2: Precompute Flags for Each Item
```python
class DashboardState(rx.State):
    topics: list[dict] = []
    
    def load_topics(self):
        topics_list = []
        for t in topics_data:
            due_today_val = int(progress.get("due_today", 0) or 0)
            topics_list.append({
                "id": t.id,
                "name": t.name,
                "due_today": due_today_val,
                "due_positive": due_today_val > 0,  # ← Precomputed flag
            })
        self.topics = topics_list

# CORRECT - Use precomputed flag
def topic_card(topic: dict):
    return rx.cond(
        topic["due_positive"],  # ← Boolean flag from data
        rx.button("Review Now", variant="solid"),
        rx.button("View Cards", variant="soft"),
    )
```

### ✅ Pattern 3: Simple Lists for Rendering
```python
class CardState(rx.State):
    topics: list[dict] = []        # ← For lookups (id, name pairs)
    topic_names: list[str] = []    # ← Simple list for rendering
    
    def load_topics(self):
        with rx.session() as session:
            topics_data = session.exec(select(Topic)).all()
            self.topics = [{"id": t.id, "name": t.name} for t in topics_data]
            self.topic_names = [t.name for t in topics_data]  # ← Simple list
    
    def select_topic_by_name(self, topic_name: str):
        """Convert name to ID using topics list."""
        for topic in self.topics:
            if topic["name"] == topic_name:
                self.new_topic_id = topic["id"]
                return

# CORRECT - Use simple list in select
def create_form():
    return rx.select(
        CardState.topic_names,  # ← Simple list[str], safe to render
        on_change=CardState.select_topic_by_name,
    )
```

---

## String Rendering

### ❌ Wrong: f-strings with Vars
```python
# WRONG
rx.text(f"✅ {ReviewState.correct_count} | ❌ {ReviewState.incorrect_count}")
rx.text(f"You reviewed {ReviewState.count} cards")
```

### ✅ Correct: String Concatenation with .to_string()
```python
# CORRECT
rx.text("✅ " + ReviewState.correct_count.to_string() + " | ❌ " + ReviewState.incorrect_count.to_string())
rx.text("You reviewed " + ReviewState.count.to_string() + " cards")
```

### ✅ Correct: Template Strings (Alternative)
```python
# CORRECT - Using template-style
rx.text(
    rx.fragment(
        "✅ ", ReviewState.correct_count, " | ❌ ", ReviewState.incorrect_count
    )
)
```

---

## Collections and Iteration

### ❌ Wrong: Python Comprehensions at Render Time
```python
# WRONG
rx.select([item["name"] for item in State.items])  # VarTypeError
```

### ✅ Correct: Use rx.foreach for Rendering
```python
# CORRECT - For complex components
def item_renderer(item: dict):
    return rx.text(item["name"])

def my_page():
    return rx.vstack(
        rx.foreach(State.items, item_renderer)
    )
```

### ✅ Correct: Precompute Simple Lists
```python
# CORRECT - For simple data like strings
class State(rx.State):
    items: list[dict] = []
    item_names: list[str] = []  # ← Simple extracted list
    
    def load_items(self):
        # Load items...
        self.item_names = [item["name"] for item in self.items]

def my_page():
    return rx.select(State.item_names)  # ← Safe to use directly
```

---

## Comparisons and Conditionals

### ❌ Wrong: Direct Comparison on Reactive Values
```python
# WRONG
rx.cond(
    topic["due_today"] > 0,  # TypeError
    rx.badge("Due"),
)

rx.cond(
    DashboardState.topics.length() > 0,  # May not work as expected
    rx.text("Has topics"),
)

if card["accuracy"] >= 80:  # WRONG - Python if at render time
    return rx.badge("Excellent", color="green")
```

### ✅ Correct: Precomputed Booleans
```python
# CORRECT
class State(rx.State):
    topics: list[dict] = []
    has_topics: bool = False
    
    def load_topics(self):
        # ... load topics
        self.has_topics = len(self.topics) > 0  # Python comparison in method

rx.cond(
    State.has_topics,  # Simple boolean Var
    rx.text("Has topics"),
)
```

### ✅ Correct: Flags in Data
```python
# CORRECT - Add flag during data preparation
def load_data(self):
    items = []
    for item in raw_data:
        items.append({
            "id": item.id,
            "value": item.value,
            "is_high": item.value > 80,  # ← Precomputed in Python
        })
    self.items = items

def item_card(item: dict):
    return rx.cond(
        item["is_high"],  # ← Use flag
        rx.badge("High", color="green"),
        rx.badge("Normal", color="gray"),
    )
```

---

## Type Safety

### Component Prop Types
Many Reflex components expect specific types. The reactive system performs type validation.

### ❌ Wrong: Type Mismatch
```python
# WRONG - rx.progress expects int, not float
@rx.var
def progress_percentage(self) -> float:
    return (self.current / self.total) * 100

rx.progress(value=State.progress_percentage)  # TypeError
```

### ✅ Correct: Match Expected Type
```python
# CORRECT - Return int
@rx.var
def progress_percentage(self) -> int:
    return int((self.current / self.total) * 100)

rx.progress(value=State.progress_percentage)  # ✓ Works
```

### Common Component Type Requirements
| Component | Prop | Expected Type |
|-----------|------|---------------|
| `rx.progress` | `value` | `int` |
| `rx.slider` | `value` | `float` or `int` |
| `rx.select` | items | `list[str]` (not `list[dict]`) |
| `rx.badge` | children | `str` or components |

---

## Comparison String Checks

### ❌ Wrong: Direct String Comparison
```python
# WRONG
rx.cond(
    card["example"] != "",  # Comparing reactive value
    rx.text(card["example"])
)
```

### ✅ Correct: Convert to String First
```python
# CORRECT
rx.cond(
    card["example"].to_string() != "",  # Compare string representation
    rx.text(card["example"])
)
```

### ✅ Alternative: Use Truthiness (where applicable)
```python
# CORRECT - If empty string is falsy in your context
rx.cond(
    card["example"],  # Checks truthiness
    rx.text(card["example"])
)
```

---

## Complete Example: Before and After

### ❌ Before (Multiple Issues)
```python
class DashboardState(rx.State):
    topics: list[dict] = []
    total_due: int = 0

    def load_topics(self):
        # ... fetch topics
        self.topics = topics_list
        self.total_due = sum(t["due_today"] for t in topics_list)

def topic_card(topic: dict):
    return rx.card(
        rx.heading(topic["name"]),
        rx.text(f"{topic['due_today']} cards due"),  # f-string issue
        rx.cond(
            topic["due_today"] > 0,  # Comparison issue
            rx.button("Review Now", variant="solid"),
            rx.button("View Cards", variant="soft"),
        ),
    )

def dashboard_page():
    return rx.vstack(
        rx.cond(
            len(DashboardState.topics) > 0,  # len() issue
            rx.grid(
                rx.foreach(DashboardState.topics, topic_card),
            ),
        ),
    )
```

### ✅ After (All Issues Fixed)
```python
class DashboardState(rx.State):
    topics: list[dict] = []
    total_due: int = 0
    has_topics: bool = False  # ← Added precomputed boolean

    def load_topics(self):
        topics_list = []
        total_due = 0
        
        for t in topics_data:
            due_today_val = int(progress.get("due_today", 0) or 0)
            topics_list.append({
                "id": t.id,
                "name": t.name,
                "due_today": due_today_val,
                "due_positive": due_today_val > 0,  # ← Precomputed flag
            })
            total_due += due_today_val
        
        self.topics = topics_list
        self.total_due = total_due
        self.has_topics = len(topics_list) > 0  # ← Python comparison in method

def topic_card(topic: dict):
    return rx.card(
        rx.heading(topic["name"]),
        rx.text(topic["due_today"].to_string() + " cards due"),  # ← .to_string()
        rx.cond(
            topic["due_positive"],  # ← Use precomputed flag
            rx.button("Review Now", variant="solid"),
            rx.button("View Cards", variant="soft"),
        ),
    )

def dashboard_page():
    return rx.vstack(
        rx.cond(
            DashboardState.has_topics,  # ← Use precomputed boolean
            rx.grid(
                rx.foreach(DashboardState.topics, topic_card),
            ),
        ),
    )
```

---

## Summary Checklist

When writing Reflex components, always:

- ✅ Precompute comparisons in state methods, not at render time
- ✅ Use `.to_string()` for string concatenation with Vars
- ✅ Create simple lists (e.g., `list[str]`) for select/iteration
- ✅ Add boolean flags to data dictionaries for conditionals
- ✅ Use `rx.foreach` for rendering collections
- ✅ Match component prop type requirements
- ✅ Avoid Python operations (`>`, `<`, `len()`, comprehensions) on reactive Vars
- ✅ Test that all Vars are being used reactively, not imperatively

---

## Debugging Tips

### Error: `TypeError: '>' not supported between instances of 'ObjectItemOperation' and 'int'`
- **Cause:** Direct Python comparison on reactive Var
- **Fix:** Precompute the comparison in a state method

### Error: `VarTypeError: Cannot iterate over Var`
- **Cause:** List comprehension or `for` loop over reactive Var
- **Fix:** Use `rx.foreach` or precompute a simple list in state

### Error: `TypeError: Invalid var passed for prop X.value, expected type Y, got type Z`
- **Cause:** Type mismatch between Var type and component prop requirement
- **Fix:** Cast to the correct type in your state method or `@rx.var`

### Warning: `state_auto_setters defaulting to True has been deprecated`
- **Cause:** Using `set_<var_name>` without defining it explicitly
- **Effect:** Just a deprecation warning, won't break the app
- **Fix (optional):** Define setters explicitly or ignore until Reflex 0.9.0

---

## Additional Resources

- [Reflex Documentation](https://reflex.dev/docs)
- [Reflex State Guide](https://reflex.dev/docs/state/overview)
- [Reflex Vars and Operations](https://reflex.dev/docs/state/vars)

---

**Last Updated:** Phase 4 Implementation (October 2025)
