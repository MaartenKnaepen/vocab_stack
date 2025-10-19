# Phase 3: Basic UI Components - Implementation Guide

## Overview
This guide covers implementing the core UI components using Reflex for the vocabulary learning app.

**Estimated Time**: 5-6 hours  
**Goal**: Working flashcard review interface with basic navigation

---

## Prerequisites

- ✅ Phase 1 completed (database models)
- ✅ Phase 2 completed (Leitner algorithm)
- ✅ Understanding of Reflex UI components

---

## Reflex UI Fundamentals

### Key Concepts
- **Components**: UI building blocks (`rx.button`, `rx.text`, etc.)
- **State**: Backend state management (subclass `rx.State`)
- **Events**: User interactions trigger state updates
- **Styling**: Inline props or theme configuration

### Common Components
```python
rx.heading()      # Headings
rx.text()         # Text display
rx.button()       # Buttons
rx.input()        # Text input
rx.vstack()       # Vertical layout
rx.hstack()       # Horizontal layout
rx.card()         # Card container
rx.foreach()      # Iterate over lists
rx.cond()         # Conditional rendering
```

---

## Step 1: Create Navigation Component (45 minutes)

Create `vocab_app/components/navigation.py`:

```python
"""Navigation bar component."""
import reflex as rx


def navbar() -> rx.Component:
    """Top navigation bar."""
    return rx.box(
        rx.hstack(
            rx.heading("🎴 Vocab App", size="7"),
            rx.spacer(),
            rx.hstack(
                rx.link(
                    rx.button("Dashboard", variant="soft"),
                    href="/",
                ),
                rx.link(
                    rx.button("Review", variant="soft"),
                    href="/review",
                ),
                rx.link(
                    rx.button("Topics", variant="soft"),
                    href="/topics",
                ),
                rx.link(
                    rx.button("Cards", variant="soft"),
                    href="/cards",
                ),
                spacing="3",
            ),
            width="100%",
            padding="1rem",
            align="center",
        ),
        background="var(--accent-3)",
        position="sticky",
        top="0",
        z_index="1000",
        border_bottom="1px solid var(--gray-6)",
    )


def layout(content: rx.Component) -> rx.Component:
    """Main layout wrapper with navigation."""
    return rx.vstack(
        navbar(),
        rx.container(
            content,
            padding="2rem",
            max_width="1200px",
        ),
        width="100%",
        min_height="100vh",
        spacing="0",
    )
```

---

## Step 2: Create Dashboard State & UI (60 minutes)

Create `vocab_app/pages/dashboard.py`:

```python
"""Dashboard page - overview of learning progress."""
import reflex as rx
from vocab_app.services.leitner_service import LeitnerService
from vocab_app.models import Topic
from sqlmodel import select


class DashboardState(rx.State):
    """State for dashboard page."""
    
    topics: list[dict] = []
    total_due: int = 0
    loading: bool = False
    
    def on_mount(self):
        """Load dashboard data on page mount."""
        self.load_dashboard_data()
    
    def load_dashboard_data(self):
        """Load all dashboard statistics."""
        self.loading = True
        
        with rx.session() as session:
            # Get all topics
            topics_data = session.exec(select(Topic)).all()
            
            self.topics = []
            total_due = 0
            
            for topic in topics_data:
                # Get progress for each topic (assuming user_id=1)
                progress = LeitnerService.get_topic_progress(
                    topic_id=topic.id,
                    user_id=1
                )
                
                self.topics.append({
                    "id": topic.id,
                    "name": topic.name,
                    "description": topic.description or "",
                    "total_cards": progress["total"],
                    "due_today": progress["due_today"],
                    "mastered": progress["mastered"],
                    "mastered_percentage": progress["mastered_percentage"],
                })
                
                total_due += progress["due_today"]
            
            self.total_due = total_due
        
        self.loading = False


def topic_card(topic: dict) -> rx.Component:
    """Render a topic card with statistics."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(topic["name"], size="5"),
                rx.spacer(),
                rx.badge(
                    f"{topic['due_today']} due",
                    color_scheme="orange" if topic["due_today"] > 0 else "gray",
                ),
                width="100%",
            ),
            rx.text(topic["description"], color="gray"),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Total Cards", size="1", color="gray"),
                    rx.heading(str(topic["total_cards"]), size="6"),
                    align="start",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Mastered", size="1", color="gray"),
                    rx.heading(
                        f"{topic['mastered_percentage']}%",
                        size="6",
                        color="green",
                    ),
                    align="start",
                    spacing="1",
                ),
                spacing="6",
            ),
            rx.link(
                rx.button(
                    "Review Now" if topic["due_today"] > 0 else "View Cards",
                    width="100%",
                    variant="solid" if topic["due_today"] > 0 else "soft",
                ),
                href=f"/review?topic_id={topic['id']}",
            ),
            spacing="3",
            align="start",
        ),
    )


def dashboard_page() -> rx.Component:
    """Dashboard page content."""
    return rx.vstack(
        rx.heading("Dashboard", size="8"),
        rx.cond(
            DashboardState.loading,
            rx.spinner(size="3"),
            rx.vstack(
                # Summary card
                rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.heading("Cards Due Today", size="3", color="gray"),
                            rx.heading(
                                DashboardState.total_due.to_string(),
                                size="9",
                                color="orange",
                            ),
                            align="start",
                        ),
                        rx.spacer(),
                        rx.link(
                            rx.button(
                                "Start Review",
                                size="3",
                                disabled=DashboardState.total_due == 0,
                            ),
                            href="/review",
                        ),
                        width="100%",
                        align="center",
                    ),
                    width="100%",
                ),
                # Topics grid
                rx.heading("Your Topics", size="5", margin_top="2rem"),
                rx.cond(
                    DashboardState.topics.length() > 0,
                    rx.grid(
                        rx.foreach(
                            DashboardState.topics,
                            topic_card,
                        ),
                        columns="3",
                        spacing="4",
                        width="100%",
                    ),
                    rx.text("No topics yet. Create your first topic!", color="gray"),
                ),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        spacing="6",
    )
```

---

## Step 3: Create Flashcard Review UI (90 minutes)

Create `vocab_app/pages/review.py`:

```python
"""Flashcard review page."""
import reflex as rx
from vocab_app.services.leitner_service import LeitnerService
from vocab_app.models import Flashcard


class ReviewState(rx.State):
    """State for flashcard review."""
    
    # Current session data
    cards_to_review: list[Flashcard] = []
    current_index: int = 0
    show_answer: bool = False
    session_complete: bool = False
    
    # Statistics
    correct_count: int = 0
    incorrect_count: int = 0
    
    # Loading state
    loading: bool = False
    
    @rx.var
    def current_card(self) -> dict:
        """Get current flashcard."""
        if 0 <= self.current_index < len(self.cards_to_review):
            card = self.cards_to_review[self.current_index]
            return {
                "id": card.id,
                "front": card.front,
                "back": card.back,
                "example": card.example or "",
            }
        return {}
    
    @rx.var
    def progress_text(self) -> str:
        """Get progress text."""
        if not self.cards_to_review:
            return "0 / 0"
        return f"{self.current_index + 1} / {len(self.cards_to_review)}"
    
    @rx.var
    def progress_percentage(self) -> float:
        """Get progress percentage."""
        if not self.cards_to_review:
            return 0
        return ((self.current_index + 1) / len(self.cards_to_review)) * 100
    
    def on_mount(self):
        """Load cards when page loads."""
        self.load_review_cards()
    
    def load_review_cards(self, topic_id: int = None):
        """Load cards due for review."""
        self.loading = True
        
        # Get due cards (user_id=1 for demo)
        self.cards_to_review = LeitnerService.get_due_cards(
            topic_id=topic_id,
            user_id=1
        )
        
        self.current_index = 0
        self.show_answer = False
        self.session_complete = False
        self.correct_count = 0
        self.incorrect_count = 0
        
        self.loading = False
        
        if len(self.cards_to_review) == 0:
            self.session_complete = True
    
    def flip_card(self):
        """Show/hide answer."""
        self.show_answer = not self.show_answer
    
    def mark_correct(self):
        """Mark current card as correct and move to next."""
        if not self.current_card:
            return
        
        # Process review
        LeitnerService.process_review(
            flashcard_id=self.current_card["id"],
            user_id=1,
            was_correct=True
        )
        
        self.correct_count += 1
        self._next_card()
    
    def mark_incorrect(self):
        """Mark current card as incorrect and move to next."""
        if not self.current_card:
            return
        
        # Process review
        LeitnerService.process_review(
            flashcard_id=self.current_card["id"],
            user_id=1,
            was_correct=False
        )
        
        self.incorrect_count += 1
        self._next_card()
    
    def _next_card(self):
        """Move to next card."""
        self.show_answer = False
        self.current_index += 1
        
        if self.current_index >= len(self.cards_to_review):
            self.session_complete = True


def flashcard_display() -> rx.Component:
    """Display the current flashcard."""
    return rx.card(
        rx.cond(
            ReviewState.show_answer == False,
            # Front of card
            rx.vstack(
                rx.text("Question", size="2", color="gray", weight="bold"),
                rx.heading(
                    ReviewState.current_card["front"],
                    size="8",
                    text_align="center",
                ),
                rx.button(
                    "Show Answer",
                    on_click=ReviewState.flip_card,
                    size="3",
                    variant="soft",
                ),
                spacing="4",
                align="center",
            ),
            # Back of card
            rx.vstack(
                rx.text("Answer", size="2", color="gray", weight="bold"),
                rx.heading(
                    ReviewState.current_card["back"],
                    size="7",
                    text_align="center",
                ),
                rx.cond(
                    ReviewState.current_card["example"] != "",
                    rx.box(
                        rx.text("Example:", size="2", color="gray", weight="bold"),
                        rx.text(
                            ReviewState.current_card["example"],
                            size="3",
                            style={"font-style": "italic"},
                        ),
                        padding="1rem",
                        background="var(--gray-3)",
                        border_radius="0.5rem",
                    ),
                ),
                rx.hstack(
                    rx.button(
                        "❌ Incorrect",
                        on_click=ReviewState.mark_incorrect,
                        size="3",
                        color_scheme="red",
                        width="150px",
                    ),
                    rx.button(
                        "✅ Correct",
                        on_click=ReviewState.mark_correct,
                        size="3",
                        color_scheme="green",
                        width="150px",
                    ),
                    spacing="4",
                ),
                spacing="4",
                align="center",
            ),
        ),
        width="100%",
        max_width="600px",
        min_height="400px",
        padding="3rem",
    )


def review_page() -> rx.Component:
    """Review page content."""
    return rx.center(
        rx.vstack(
            rx.heading("Review Session", size="8"),
            
            # Progress bar
            rx.vstack(
                rx.hstack(
                    rx.text(ReviewState.progress_text, weight="bold"),
                    rx.spacer(),
                    rx.text(
                        f"✅ {ReviewState.correct_count.to_string()} | "
                        f"❌ {ReviewState.incorrect_count.to_string()}",
                        color="gray",
                    ),
                    width="100%",
                ),
                rx.progress(
                    value=ReviewState.progress_percentage,
                    width="100%",
                    color_scheme="blue",
                ),
                width="100%",
                spacing="2",
            ),
            
            # Main content
            rx.cond(
                ReviewState.loading,
                rx.spinner(size="3"),
                rx.cond(
                    ReviewState.session_complete,
                    # Session complete
                    rx.card(
                        rx.vstack(
                            rx.heading("🎉 Session Complete!", size="7"),
                            rx.text(
                                f"You reviewed {ReviewState.correct_count + ReviewState.incorrect_count} cards",
                                size="4",
                            ),
                            rx.divider(),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Correct", color="green", weight="bold"),
                                    rx.heading(
                                        ReviewState.correct_count.to_string(),
                                        size="8",
                                        color="green",
                                    ),
                                ),
                                rx.vstack(
                                    rx.text("Incorrect", color="red", weight="bold"),
                                    rx.heading(
                                        ReviewState.incorrect_count.to_string(),
                                        size="8",
                                        color="red",
                                    ),
                                ),
                                spacing="6",
                            ),
                            rx.link(
                                rx.button("Back to Dashboard", size="3"),
                                href="/",
                            ),
                            spacing="4",
                            align="center",
                        ),
                        padding="3rem",
                    ),
                    # Show flashcard
                    flashcard_display(),
                ),
            ),
            
            spacing="6",
            width="100%",
            max_width="800px",
        ),
        width="100%",
        padding="2rem",
    )
```

---

## Step 4: Setup App Routes (30 minutes)

Update `vocab_app/__init__.py` or create `vocab_app/app.py`:

```python
"""Main application setup."""
import reflex as rx
from vocab_app.components.navigation import layout
from vocab_app.pages.dashboard import dashboard_page, DashboardState
from vocab_app.pages.review import review_page, ReviewState


# Create app
app = rx.App(
    theme=rx.theme(
        accent_color="blue",
        radius="large",
    ),
)

# Add pages
app.add_page(
    lambda: layout(dashboard_page()),
    route="/",
    title="Dashboard - Vocab App",
    on_load=DashboardState.on_mount,
)

app.add_page(
    lambda: layout(review_page()),
    route="/review",
    title="Review - Vocab App",
    on_load=ReviewState.on_mount,
)
```

---

## Step 5: Run the Application (15 minutes)

```bash
# Run development server
reflex run

# Or for production
reflex run --env prod
```

Visit `http://localhost:3000` to see your app!

---

## Verification Checklist

- [ ] Navigation bar displays correctly
- [ ] Dashboard shows topics and statistics
- [ ] Can navigate to review page
- [ ] Flashcards display front/back
- [ ] Can mark cards correct/incorrect
- [ ] Progress bar updates
- [ ] Session complete screen shows statistics
- [ ] Can return to dashboard

---

## Next Steps

**Ready for Phase 4**: Topic & Card Management

This will add CRUD operations for topics and flashcards.

---

**Phase 3 Complete!** 🎉
