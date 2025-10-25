"""Topic management page."""
import reflex as rx
from vocab_stack.models import Topic
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
            TopicState.error_message.to_string() != "",
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
