# Phase 4: Topic & Card Management - Implementation Guide

## Overview
This guide covers implementing full CRUD operations for topics and flashcards.

**Estimated Time**: 4-5 hours  
**Goal**: Complete topic and card management with create, read, update, delete functionality

---

## Prerequisites

- ✅ Phase 3 completed (basic UI components)
- ✅ Navigation and layout working
- ✅ Understanding of Reflex forms and state management

---

## Step 1: Create Topic Management Page (90 minutes)

Create `vocab_app/pages/topics.py`:

```python
"""Topic management page."""
import reflex as rx
from vocab_app.models import Topic
from sqlmodel import select


class TopicState(rx.State):
    """State for topic management."""
    
    topics: list[dict] = []
    
    # Form fields
    new_topic_name: str = ""
    new_topic_description: str = ""
    
    # Edit mode
    editing_topic_id: int = -1
    edit_name: str = ""
    edit_description: str = ""
    
    # UI state
    show_create_form: bool = False
    loading: bool = False
    error_message: str = ""
    
    def on_mount(self):
        """Load topics on page mount."""
        self.load_topics()
    
    def load_topics(self):
        """Load all topics from database."""
        self.loading = True
        
        with rx.session() as session:
            topics_data = session.exec(select(Topic)).all()
            
            self.topics = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description or "",
                    "created_at": t.created_at.strftime("%Y-%m-%d"),
                }
                for t in topics_data
            ]
        
        self.loading = False
    
    def toggle_create_form(self):
        """Show/hide create form."""
        self.show_create_form = not self.show_create_form
        self.error_message = ""
        if not self.show_create_form:
            self.new_topic_name = ""
            self.new_topic_description = ""
    
    def create_topic(self):
        """Create a new topic."""
        if not self.new_topic_name.strip():
            self.error_message = "Topic name is required"
            return
        
        with rx.session() as session:
            # Check for duplicate name
            existing = session.exec(
                select(Topic).where(Topic.name == self.new_topic_name)
            ).first()
            
            if existing:
                self.error_message = "Topic with this name already exists"
                return
            
            # Create topic
            topic = Topic(
                name=self.new_topic_name,
                description=self.new_topic_description
            )
            session.add(topic)
            session.commit()
        
        # Reset form and reload
        self.new_topic_name = ""
        self.new_topic_description = ""
        self.show_create_form = False
        self.error_message = ""
        self.load_topics()
    
    def start_edit(self, topic_id: int, name: str, description: str):
        """Start editing a topic."""
        self.editing_topic_id = topic_id
        self.edit_name = name
        self.edit_description = description
        self.error_message = ""
    
    def cancel_edit(self):
        """Cancel editing."""
        self.editing_topic_id = -1
        self.edit_name = ""
        self.edit_description = ""
        self.error_message = ""
    
    def save_edit(self):
        """Save topic edits."""
        if not self.edit_name.strip():
            self.error_message = "Topic name is required"
            return
        
        with rx.session() as session:
            topic = session.get(Topic, self.editing_topic_id)
            if topic:
                topic.name = self.edit_name
                topic.description = self.edit_description
                session.add(topic)
                session.commit()
        
        self.editing_topic_id = -1
        self.error_message = ""
        self.load_topics()
    
    def delete_topic(self, topic_id: int):
        """Delete a topic."""
        with rx.session() as session:
            topic = session.get(Topic, topic_id)
            if topic:
                # Note: This will fail if there are flashcards referencing this topic
                # In production, you'd want to handle this gracefully
                try:
                    session.delete(topic)
                    session.commit()
                except Exception as e:
                    self.error_message = "Cannot delete topic with existing flashcards"
                    return
        
        self.load_topics()


def topic_row(topic: dict) -> rx.Component:
    """Render a topic row."""
    return rx.cond(
        TopicState.editing_topic_id == topic["id"],
        # Edit mode
        rx.table.row(
            rx.table.cell(
                rx.input(
                    value=TopicState.edit_name,
                    on_change=TopicState.set_edit_name,
                    width="100%",
                )
            ),
            rx.table.cell(
                rx.input(
                    value=TopicState.edit_description,
                    on_change=TopicState.set_edit_description,
                    width="100%",
                )
            ),
            rx.table.cell(topic["created_at"]),
            rx.table.cell(
                rx.hstack(
                    rx.button(
                        "Save",
                        on_click=TopicState.save_edit,
                        size="2",
                        color_scheme="green",
                    ),
                    rx.button(
                        "Cancel",
                        on_click=TopicState.cancel_edit,
                        size="2",
                        variant="soft",
                    ),
                    spacing="2",
                )
            ),
        ),
        # View mode
        rx.table.row(
            rx.table.cell(rx.text(topic["name"], weight="bold")),
            rx.table.cell(rx.text(topic["description"])),
            rx.table.cell(rx.text(topic["created_at"], color="gray")),
            rx.table.cell(
                rx.hstack(
                    rx.link(
                        rx.button(
                            "Cards",
                            size="2",
                            variant="soft",
                        ),
                        href=f"/cards?topic_id={topic['id']}",
                    ),
                    rx.button(
                        "Edit",
                        on_click=lambda: TopicState.start_edit(
                            topic["id"],
                            topic["name"],
                            topic["description"],
                        ),
                        size="2",
                        variant="soft",
                    ),
                    rx.button(
                        "Delete",
                        on_click=lambda: TopicState.delete_topic(topic["id"]),
                        size="2",
                        color_scheme="red",
                        variant="soft",
                    ),
                    spacing="2",
                )
            ),
        ),
    )


def topics_page() -> rx.Component:
    """Topics management page."""
    return rx.vstack(
        rx.hstack(
            rx.heading("Topics", size="8"),
            rx.spacer(),
            rx.button(
                "New Topic",
                on_click=TopicState.toggle_create_form,
                size="3",
            ),
            width="100%",
            align="center",
        ),
        
        # Error message
        rx.cond(
            TopicState.error_message != "",
            rx.callout(
                TopicState.error_message,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
        
        # Create form
        rx.cond(
            TopicState.show_create_form,
            rx.card(
                rx.vstack(
                    rx.heading("Create New Topic", size="5"),
                    rx.input(
                        placeholder="Topic name",
                        value=TopicState.new_topic_name,
                        on_change=TopicState.set_new_topic_name,
                    ),
                    rx.text_area(
                        placeholder="Description (optional)",
                        value=TopicState.new_topic_description,
                        on_change=TopicState.set_new_topic_description,
                        rows="3",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=TopicState.toggle_create_form,
                            variant="soft",
                        ),
                        rx.button(
                            "Create",
                            on_click=TopicState.create_topic,
                        ),
                        spacing="2",
                    ),
                    spacing="3",
                    align="start",
                ),
            ),
        ),
        
        # Topics table
        rx.cond(
            TopicState.loading,
            rx.spinner(size="3"),
            rx.cond(
                TopicState.topics.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Name"),
                            rx.table.column_header_cell("Description"),
                            rx.table.column_header_cell("Created"),
                            rx.table.column_header_cell("Actions"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(TopicState.topics, topic_row),
                    ),
                    width="100%",
                ),
                rx.text("No topics yet. Create your first topic!", color="gray"),
            ),
        ),
        
        spacing="4",
        width="100%",
    )
```

---

## Step 2: Create Card Management Page (120 minutes)

Create `vocab_app/pages/cards.py`:

```python
"""Flashcard management page."""
import reflex as rx
from vocab_app.models import Flashcard, Topic, LeitnerState
from vocab_app.services.leitner_service import LeitnerService
from sqlmodel import select
from datetime import date


class CardState(rx.State):
    """State for card management."""
    
    cards: list[dict] = []
    topics: list[dict] = []
    selected_topic_id: int = -1
    
    # Form fields
    new_front: str = ""
    new_back: str = ""
    new_example: str = ""
    new_topic_id: int = -1
    
    # Edit mode
    editing_card_id: int = -1
    edit_front: str = ""
    edit_back: str = ""
    edit_example: str = ""
    edit_topic_id: int = -1
    
    # UI state
    show_create_form: bool = False
    loading: bool = False
    error_message: str = ""
    
    def on_mount(self):
        """Load data on page mount."""
        self.load_topics()
        self.load_cards()
    
    def load_topics(self):
        """Load all topics for dropdown."""
        with rx.session() as session:
            topics_data = session.exec(select(Topic)).all()
            self.topics = [
                {"id": t.id, "name": t.name}
                for t in topics_data
            ]
    
    def load_cards(self, topic_id: int = None):
        """Load flashcards, optionally filtered by topic."""
        self.loading = True
        
        with rx.session() as session:
            query = select(Flashcard)
            
            if topic_id and topic_id > 0:
                query = query.where(Flashcard.topic_id == topic_id)
                self.selected_topic_id = topic_id
            
            cards_data = session.exec(query).all()
            
            self.cards = []
            for card in cards_data:
                stats = LeitnerService.get_card_statistics(card.id)
                self.cards.append({
                    "id": card.id,
                    "front": card.front,
                    "back": card.back,
                    "example": card.example or "",
                    "topic_name": card.topic.name,
                    "topic_id": card.topic_id,
                    "box": stats.get("box_number", 1),
                    "accuracy": stats.get("accuracy", 0),
                })
        
        self.loading = False
    
    def toggle_create_form(self):
        """Show/hide create form."""
        self.show_create_form = not self.show_create_form
        self.error_message = ""
        if not self.show_create_form:
            self.new_front = ""
            self.new_back = ""
            self.new_example = ""
            self.new_topic_id = -1
    
    def create_card(self):
        """Create a new flashcard."""
        if not self.new_front.strip():
            self.error_message = "Front text is required"
            return
        
        if not self.new_back.strip():
            self.error_message = "Back text is required"
            return
        
        if self.new_topic_id <= 0:
            self.error_message = "Please select a topic"
            return
        
        with rx.session() as session:
            # Create flashcard (user_id=1 for demo)
            card = Flashcard(
                front=self.new_front,
                back=self.new_back,
                example=self.new_example if self.new_example else None,
                topic_id=self.new_topic_id,
                user_id=1,
            )
            session.add(card)
            session.flush()
            
            # Create initial Leitner state
            leitner = LeitnerState(
                flashcard_id=card.id,
                box_number=1,
                next_review_date=date.today(),
            )
            session.add(leitner)
            session.commit()
        
        # Reset form and reload
        self.new_front = ""
        self.new_back = ""
        self.new_example = ""
        self.new_topic_id = -1
        self.show_create_form = False
        self.error_message = ""
        self.load_cards(self.selected_topic_id if self.selected_topic_id > 0 else None)
    
    def start_edit(self, card_id: int, front: str, back: str, example: str, topic_id: int):
        """Start editing a card."""
        self.editing_card_id = card_id
        self.edit_front = front
        self.edit_back = back
        self.edit_example = example
        self.edit_topic_id = topic_id
        self.error_message = ""
    
    def cancel_edit(self):
        """Cancel editing."""
        self.editing_card_id = -1
        self.error_message = ""
    
    def save_edit(self):
        """Save card edits."""
        if not self.edit_front.strip() or not self.edit_back.strip():
            self.error_message = "Front and back text are required"
            return
        
        with rx.session() as session:
            card = session.get(Flashcard, self.editing_card_id)
            if card:
                card.front = self.edit_front
                card.back = self.edit_back
                card.example = self.edit_example if self.edit_example else None
                card.topic_id = self.edit_topic_id
                session.add(card)
                session.commit()
        
        self.editing_card_id = -1
        self.error_message = ""
        self.load_cards(self.selected_topic_id if self.selected_topic_id > 0 else None)
    
    def delete_card(self, card_id: int):
        """Delete a flashcard."""
        with rx.session() as session:
            card = session.get(Flashcard, card_id)
            if card:
                session.delete(card)
                session.commit()
        
        self.load_cards(self.selected_topic_id if self.selected_topic_id > 0 else None)
    
    def filter_by_topic(self, topic_id: str):
        """Filter cards by topic."""
        topic_id_int = int(topic_id) if topic_id else -1
        self.load_cards(topic_id_int if topic_id_int > 0 else None)


def card_row(card: dict) -> rx.Component:
    """Render a card row."""
    return rx.cond(
        CardState.editing_card_id == card["id"],
        # Edit mode
        rx.table.row(
            rx.table.cell(
                rx.input(
                    value=CardState.edit_front,
                    on_change=CardState.set_edit_front,
                )
            ),
            rx.table.cell(
                rx.input(
                    value=CardState.edit_back,
                    on_change=CardState.set_edit_back,
                )
            ),
            rx.table.cell(
                rx.input(
                    value=CardState.edit_example,
                    on_change=CardState.set_edit_example,
                )
            ),
            rx.table.cell(
                rx.select(
                    [t["name"] for t in CardState.topics],
                    value=str(CardState.edit_topic_id),
                    on_change=lambda v: CardState.set_edit_topic_id(int(v)),
                )
            ),
            rx.table.cell("-"),
            rx.table.cell("-"),
            rx.table.cell(
                rx.hstack(
                    rx.button("Save", on_click=CardState.save_edit, size="2", color_scheme="green"),
                    rx.button("Cancel", on_click=CardState.cancel_edit, size="2", variant="soft"),
                    spacing="2",
                )
            ),
        ),
        # View mode
        rx.table.row(
            rx.table.cell(rx.text(card["front"], weight="bold")),
            rx.table.cell(rx.text(card["back"])),
            rx.table.cell(rx.text(card["example"], color="gray", style={"font-style": "italic"})),
            rx.table.cell(rx.badge(card["topic_name"], variant="soft")),
            rx.table.cell(rx.badge(f"Box {card['box']}", color_scheme="blue")),
            rx.table.cell(rx.text(f"{card['accuracy']}%", color="green")),
            rx.table.cell(
                rx.hstack(
                    rx.button(
                        "Edit",
                        on_click=lambda: CardState.start_edit(
                            card["id"],
                            card["front"],
                            card["back"],
                            card["example"],
                            card["topic_id"],
                        ),
                        size="2",
                        variant="soft",
                    ),
                    rx.button(
                        "Delete",
                        on_click=lambda: CardState.delete_card(card["id"]),
                        size="2",
                        color_scheme="red",
                        variant="soft",
                    ),
                    spacing="2",
                )
            ),
        ),
    )


def cards_page() -> rx.Component:
    """Cards management page."""
    return rx.vstack(
        rx.hstack(
            rx.heading("Flashcards", size="8"),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["All Topics"] + [t["name"] for t in CardState.topics],
                    placeholder="Filter by topic",
                    on_change=CardState.filter_by_topic,
                ),
                rx.button(
                    "New Card",
                    on_click=CardState.toggle_create_form,
                    size="3",
                ),
                spacing="3",
            ),
            width="100%",
            align="center",
        ),
        
        # Error message
        rx.cond(
            CardState.error_message != "",
            rx.callout(
                CardState.error_message,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
        
        # Create form
        rx.cond(
            CardState.show_create_form,
            rx.card(
                rx.vstack(
                    rx.heading("Create New Flashcard", size="5"),
                    rx.input(
                        placeholder="Front (question/word)",
                        value=CardState.new_front,
                        on_change=CardState.set_new_front,
                    ),
                    rx.input(
                        placeholder="Back (answer/definition)",
                        value=CardState.new_back,
                        on_change=CardState.set_new_back,
                    ),
                    rx.text_area(
                        placeholder="Example (optional)",
                        value=CardState.new_example,
                        on_change=CardState.set_new_example,
                        rows="2",
                    ),
                    rx.select(
                        [t["name"] for t in CardState.topics],
                        placeholder="Select topic",
                        on_change=lambda v: CardState.set_new_topic_id(
                            next((t["id"] for t in CardState.topics if t["name"] == v), -1)
                        ),
                    ),
                    rx.hstack(
                        rx.button("Cancel", on_click=CardState.toggle_create_form, variant="soft"),
                        rx.button("Create", on_click=CardState.create_card),
                        spacing="2",
                    ),
                    spacing="3",
                    align="start",
                ),
            ),
        ),
        
        # Cards table
        rx.cond(
            CardState.loading,
            rx.spinner(size="3"),
            rx.cond(
                CardState.cards.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Front"),
                            rx.table.column_header_cell("Back"),
                            rx.table.column_header_cell("Example"),
                            rx.table.column_header_cell("Topic"),
                            rx.table.column_header_cell("Box"),
                            rx.table.column_header_cell("Accuracy"),
                            rx.table.column_header_cell("Actions"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(CardState.cards, card_row),
                    ),
                    width="100%",
                ),
                rx.text("No cards yet. Create your first flashcard!", color="gray"),
            ),
        ),
        
        spacing="4",
        width="100%",
    )
```

---

## Step 3: Update App Routes (15 minutes)

Update `vocab_app/app.py`:

```python
"""Main application setup."""
import reflex as rx
from vocab_app.components.navigation import layout
from vocab_app.pages.dashboard import dashboard_page, DashboardState
from vocab_app.pages.review import review_page, ReviewState
from vocab_app.pages.topics import topics_page, TopicState
from vocab_app.pages.cards import cards_page, CardState


app = rx.App(
    theme=rx.theme(
        accent_color="blue",
        radius="large",
    ),
)

# Add all pages
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

app.add_page(
    lambda: layout(topics_page()),
    route="/topics",
    title="Topics - Vocab App",
    on_load=TopicState.on_mount,
)

app.add_page(
    lambda: layout(cards_page()),
    route="/cards",
    title="Cards - Vocab App",
    on_load=CardState.on_mount,
)
```

---

## Verification Checklist

- [ ] Can view all topics
- [ ] Can create new topics
- [ ] Can edit topic name/description
- [ ] Can delete topics (without cards)
- [ ] Can view all flashcards
- [ ] Can filter cards by topic
- [ ] Can create new flashcards
- [ ] Can edit flashcard content
- [ ] Can delete flashcards
- [ ] Form validation working
- [ ] Error messages display correctly

---

## Next Steps

**Ready for Phase 5**: Statistics & Progress Tracking

---

**Phase 4 Complete!** 🎉
