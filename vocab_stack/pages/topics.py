"""Topic management page."""
import reflex as rx
from vocab_stack.models import Topic, Flashcard, LeitnerState, ReviewHistory
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
    has_topics: bool = False
    
    # Delete confirmation
    confirm_delete_topic_id: int = -1
    confirm_delete_topic_name: str = ""
    confirm_delete_card_count: int = 0
    
    # Bulk import
    show_bulk_import: bool = False
    import_topic_name: str = ""
    import_data: str = ""
    import_success_count: int = 0
    
    # Reverse topic
    show_reverse_dialog: bool = False
    reverse_source_topic_id: int = -1
    reverse_source_topic_name: str = ""
    reverse_new_topic_name: str = ""
    reverse_card_count: int = 0
    
    async def on_mount(self):
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
            
            self.has_topics = len(self.topics) > 0
        
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
    
    def show_delete_confirmation(self, topic_id: int, topic_name: str):
        """Show confirmation dialog before deleting a topic."""
        self.confirm_delete_topic_id = topic_id
        self.confirm_delete_topic_name = topic_name
        self.error_message = ""
        
        # Count cards in this topic
        with rx.session() as session:
            card_count = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic_id)
            ).all()
            self.confirm_delete_card_count = len(card_count)
    
    def cancel_delete(self):
        """Cancel topic deletion."""
        self.confirm_delete_topic_id = -1
        self.confirm_delete_topic_name = ""
        self.confirm_delete_card_count = 0
    
    async def add_to_review(self, topic_id: int):
        """Add this topic's cards to review and navigate to review page."""
        from vocab_stack.pages.review import ReviewState
        review_state = await self.get_state(ReviewState)
        review_state.set_topic_for_review(topic_id)
        return rx.redirect("/review")
    
    def show_bulk_import_dialog(self):
        """Show bulk import dialog."""
        self.show_bulk_import = True
        self.import_topic_name = ""
        self.import_data = ""
        self.import_success_count = 0
        self.error_message = ""
    
    def cancel_bulk_import(self):
        """Cancel bulk import."""
        self.show_bulk_import = False
        self.import_topic_name = ""
        self.import_data = ""
        self.import_success_count = 0
    
    async def process_bulk_import(self):
        """Process bulk import from pasted data."""
        from vocab_stack.pages.auth import AuthState
        from datetime import date
        
        # Get current user
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            self.error_message = "You must be logged in to import cards"
            return
        
        # Validate inputs
        if not self.import_topic_name.strip():
            self.error_message = "Topic name is required"
            return
        
        if not self.import_data.strip():
            self.error_message = "Card data is required"
            return
        
        topic_name = self.import_topic_name.strip()
        
        try:
            # Parse the pasted data (CSV format: front,back per line)
            lines = self.import_data.strip().split('\n')
            imported_count = 0
            
            with rx.session() as session:
                # Get or create topic
                topic = session.exec(
                    select(Topic).where(Topic.name == topic_name)
                ).first()
                
                if not topic:
                    topic = Topic(name=topic_name, description="Bulk imported")
                    session.add(topic)
                    session.flush()
                
                # Process each line
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Split by comma (simple CSV parsing)
                    parts = [p.strip() for p in line.split(',')]
                    
                    if len(parts) < 2:
                        continue  # Skip invalid lines
                    
                    front = parts[0]
                    back = parts[1]
                    
                    if not front or not back:
                        continue
                    
                    # Create flashcard
                    card = Flashcard(
                        front=front,
                        back=back,
                        topic_id=topic.id,
                        user_id=auth.current_user_id
                    )
                    session.add(card)
                    session.flush()
                    session.refresh(card)  # Ensure card.id is populated
                    
                    # Create Leitner state
                    leitner = LeitnerState(
                        flashcard_id=card.id,
                        box_number=1,
                        next_review_date=date.today()
                    )
                    session.add(leitner)
                    
                    imported_count += 1
                
                session.commit()
            
            # Success
            self.import_success_count = imported_count
            self.error_message = ""
            
            # Reload topics
            self.load_topics()
            
            # Close dialog after 2 seconds
            if imported_count > 0:
                # Keep dialog open to show success message
                pass
            
        except Exception as e:
            self.error_message = f"Import failed: {str(e)}"
    
    def delete_topic_confirmed(self):
        """Delete a topic and all its associated cards."""
        topic_id = self.confirm_delete_topic_id
        
        with rx.session() as session:
            # Get all flashcards for this topic
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic_id)
            ).all()
            
            # Delete related records for each flashcard
            for flashcard in flashcards:
                # Delete LeitnerState records
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == flashcard.id)
                ).all()
                for state in leitner_states:
                    session.delete(state)
                
                # Delete ReviewHistory records
                review_histories = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == flashcard.id)
                ).all()
                for history in review_histories:
                    session.delete(history)
                
                # Delete the flashcard itself
                session.delete(flashcard)
            
            # Finally, delete the topic
            topic = session.get(Topic, topic_id)
            if topic:
                session.delete(topic)
            
            session.commit()
        
        # Reset confirmation state and reload
        self.confirm_delete_topic_id = -1
        self.confirm_delete_topic_name = ""
        self.confirm_delete_card_count = 0
        self.load_topics()
    
    def show_reverse_dialog(self, topic_id: int, topic_name: str):
        """Show dialog to reverse a topic's cards."""
        self.show_reverse_dialog = True
        self.reverse_source_topic_id = topic_id
        self.reverse_source_topic_name = topic_name
        self.reverse_new_topic_name = f"{topic_name} (Reversed)"
        self.error_message = ""
        
        # Count cards in this topic
        with rx.session() as session:
            card_count = session.exec(
                select(Flashcard).where(Flashcard.topic_id == topic_id)
            ).all()
            self.reverse_card_count = len(card_count)
    
    def cancel_reverse(self):
        """Cancel topic reversal."""
        self.show_reverse_dialog = False
        self.reverse_source_topic_id = -1
        self.reverse_source_topic_name = ""
        self.reverse_new_topic_name = ""
        self.reverse_card_count = 0
    
    async def create_reversed_topic(self):
        """Create a new topic with all cards reversed (front/back swapped)."""
        from vocab_stack.pages.auth import AuthState
        from datetime import date
        
        # Get current user
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            self.error_message = "You must be logged in to create reversed topics"
            return
        
        # Validate new topic name
        if not self.reverse_new_topic_name.strip():
            self.error_message = "New topic name is required"
            return
        
        new_topic_name = self.reverse_new_topic_name.strip()
        
        try:
            with rx.session() as session:
                # Check if new topic name already exists
                existing_topic = session.exec(
                    select(Topic).where(Topic.name == new_topic_name)
                ).first()
                
                if existing_topic:
                    self.error_message = f"Topic '{new_topic_name}' already exists"
                    return
                
                # Get source topic
                source_topic = session.get(Topic, self.reverse_source_topic_id)
                if not source_topic:
                    self.error_message = "Source topic not found"
                    return
                
                # Create new topic
                new_topic = Topic(
                    name=new_topic_name,
                    description=f"Reversed from: {source_topic.description or source_topic.name}"
                )
                session.add(new_topic)
                session.flush()
                
                # Get all flashcards from source topic
                source_cards = session.exec(
                    select(Flashcard).where(Flashcard.topic_id == self.reverse_source_topic_id)
                ).all()
                
                # Create reversed cards
                for source_card in source_cards:
                    # Create new card with front and back swapped
                    new_card = Flashcard(
                        front=source_card.back,  # Swap!
                        back=source_card.front,   # Swap!
                        example=source_card.example,
                        topic_id=new_topic.id,
                        user_id=auth.current_user_id
                    )
                    session.add(new_card)
                    session.flush()
                    session.refresh(new_card)
                    
                    # Create Leitner state for new card
                    leitner = LeitnerState(
                        flashcard_id=new_card.id,
                        box_number=1,
                        next_review_date=date.today()
                    )
                    session.add(leitner)
                
                session.commit()
            
            # Success - close dialog and reload
            self.show_reverse_dialog = False
            self.reverse_source_topic_id = -1
            self.reverse_source_topic_name = ""
            self.reverse_new_topic_name = ""
            self.reverse_card_count = 0
            self.error_message = ""
            self.load_topics()
            
        except Exception as e:
            self.error_message = f"Failed to create reversed topic: {str(e)}"


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
                        "Reverse",
                        on_click=lambda: TopicState.show_reverse_dialog(
                            topic["id"],
                            topic["name"],
                        ),
                        size="2",
                        color_scheme="purple",
                        variant="soft",
                    ),
                    rx.button(
                        "Add to Review",
                        on_click=lambda: TopicState.add_to_review(topic["id"]),
                        size="2",
                        color_scheme="green",
                        variant="soft",
                    ),
                    rx.button(
                        "Delete",
                        on_click=lambda: TopicState.show_delete_confirmation(
                            topic["id"],
                            topic["name"],
                        ),
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
                "Bulk Import",
                on_click=TopicState.show_bulk_import_dialog,
                size="3",
                color_scheme="blue",
                variant="soft",
            ),
            rx.button(
                "New Topic",
                on_click=TopicState.toggle_create_form,
                size="3",
            ),
            spacing="2",
            width="100%",
            align="center",
        ),
        
        # Error message
        rx.cond(
            TopicState.error_message.to_string() != "",
            rx.callout(
                TopicState.error_message,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
        
        # Bulk import dialog
        rx.cond(
            TopicState.show_bulk_import,
            rx.card(
                rx.vstack(
                    rx.heading("Bulk Import Cards", size="5", color="blue"),
                    
                    # Success message
                    rx.cond(
                        TopicState.import_success_count > 0,
                        rx.callout(
                            f"Successfully imported {TopicState.import_success_count.to_string()} cards!",
                            icon="check",
                            color_scheme="green",
                        ),
                    ),
                    
                    # Instructions
                    rx.box(
                        rx.vstack(
                            rx.text("Format: One card per line", weight="bold", size="2"),
                            rx.text("Each line: Front,Back", size="2"),
                            rx.text("Example:", size="2", margin_top="0.5rem"),
                            rx.box(
                                rx.text("Hello,Hola", as_="div"),
                                rx.text("Goodbye,Adiós", as_="div"),
                                rx.text("Thank you,Gracias", as_="div"),
                                padding="0.5rem",
                                background="var(--gray-2)",
                                border_radius="0.25rem",
                                font_family="monospace",
                                font_size="0.9em",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        background="var(--gray-3)",
                        border_radius="0.5rem",
                        width="100%",
                    ),
                    
                    # Topic name
                    rx.vstack(
                        rx.text("Topic Name", size="2", weight="bold"),
                        rx.input(
                            value=TopicState.import_topic_name,
                            on_change=TopicState.set_import_topic_name,
                            placeholder="e.g., Spanish Basics",
                            width="100%",
                        ),
                        rx.text(
                            "Will create topic if it doesn't exist",
                            size="1",
                            color="gray",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    
                    # Card data input
                    rx.vstack(
                        rx.text("Card Data", size="2", weight="bold"),
                        rx.text_area(
                            value=TopicState.import_data,
                            on_change=TopicState.set_import_data,
                            placeholder="Hello,Hola\nGoodbye,Adiós\nThank you,Gracias",
                            rows="10",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    
                    # Buttons
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=TopicState.cancel_bulk_import,
                            variant="soft",
                            size="3",
                        ),
                        rx.button(
                            "Import",
                            on_click=TopicState.process_bulk_import,
                            color_scheme="blue",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                width="100%",
            ),
        ),
        
        # Reverse topic dialog
        rx.cond(
            TopicState.show_reverse_dialog,
            rx.card(
                rx.vstack(
                    rx.heading("Reverse Topic Cards", size="5", color="purple"),
                    rx.text(
                        "Create a new topic with all cards from '",
                        rx.text(TopicState.reverse_source_topic_name, weight="bold", as_="span"),
                        "' reversed (front ↔ back).",
                    ),
                    rx.cond(
                        TopicState.reverse_card_count > 0,
                        rx.callout(
                            rx.text(
                                "This will create ",
                                rx.text(TopicState.reverse_card_count.to_string(), weight="bold", as_="span"),
                                " new flashcard(s) with front and back swapped.",
                            ),
                            icon="info",
                            color_scheme="blue",
                        ),
                        rx.callout(
                            "This topic has no flashcards to reverse.",
                            icon="triangle_alert",
                            color_scheme="orange",
                        ),
                    ),
                    rx.vstack(
                        rx.text("New Topic Name", size="2", weight="bold"),
                        rx.input(
                            value=TopicState.reverse_new_topic_name,
                            on_change=TopicState.set_reverse_new_topic_name,
                            placeholder="e.g., Spanish Basics (Reversed)",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=TopicState.cancel_reverse,
                            variant="soft",
                            size="3",
                        ),
                        rx.button(
                            "Create Reversed Topic",
                            on_click=TopicState.create_reversed_topic,
                            color_scheme="purple",
                            size="3",
                            disabled=TopicState.reverse_card_count == 0,
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
            ),
        ),
        
        # Delete confirmation dialog
        rx.cond(
            TopicState.confirm_delete_topic_id != -1,
            rx.card(
                rx.vstack(
                    rx.heading("Confirm Delete", size="5", color="red"),
                    rx.text(
                        "Are you sure you want to delete the topic '",
                        rx.text(TopicState.confirm_delete_topic_name, weight="bold", as_="span"),
                        "'?",
                    ),
                    rx.cond(
                        TopicState.confirm_delete_card_count > 0,
                        rx.callout(
                            rx.text(
                                "This will permanently delete ",
                                rx.text(TopicState.confirm_delete_card_count.to_string(), weight="bold", as_="span"),
                                " flashcard(s) and all associated review history.",
                            ),
                            icon="info",
                            color_scheme="orange",
                        ),
                        rx.text("This topic has no flashcards.", color="gray"),
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=TopicState.cancel_delete,
                            variant="soft",
                            size="3",
                        ),
                        rx.button(
                            "Delete Topic",
                            on_click=TopicState.delete_topic_confirmed,
                            color_scheme="red",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="4",
                    align="start",
                ),
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
                TopicState.has_topics,
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
