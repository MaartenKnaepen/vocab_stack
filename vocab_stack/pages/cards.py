"""Flashcard management page."""
import reflex as rx
from vocab_stack.models import Flashcard, Topic, LeitnerState
from vocab_stack.services.leitner_service import LeitnerService
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
    has_cards: bool = False
    topic_names: list[str] = []
    
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
            self.topic_names = [t.name for t in topics_data]
    
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
                    "accuracy": int(stats.get("accuracy", 0)),
                })
            
            self.has_cards = len(self.cards) > 0
        
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
    
    def select_topic_by_name(self, topic_name: str):
        """Select a topic by name for the new card form."""
        for topic in self.topics:
            if topic["name"] == topic_name:
                self.new_topic_id = topic["id"]
                return
        self.new_topic_id = -1


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
                rx.text("(Edit topic not supported inline)", size="1", color="gray")
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
            rx.table.cell(rx.badge("Box " + card["box"].to_string(), color_scheme="blue")),
            rx.table.cell(rx.text(card["accuracy"].to_string() + "%", color="green")),
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
            CardState.error_message.to_string() != "",
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
                        CardState.topic_names,
                        placeholder="Select topic",
                        on_change=CardState.select_topic_by_name,
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
                CardState.has_cards,
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
