"""Flashcard review page and state."""
import reflex as rx
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.models import Flashcard


class ReviewState(rx.State):
    cards_to_review: list[Flashcard] = []
    current_index: int = 0
    show_answer: bool = False
    session_complete: bool = False
    loading: bool = False
    correct_count: int = 0
    incorrect_count: int = 0
    
    # User preferences
    show_examples: bool = True
    cards_per_session: int = 20
    review_order: str = "random"
    answer_mode: str = "reveal"  # reveal or type
    
    # Typing functionality
    user_input: str = ""
    answer_checked: bool = False
    is_correct: bool = False
    
    # Topic filtering
    selected_topic_id: int | None = None

    @rx.var
    def current_card(self) -> dict:
        if 0 <= self.current_index < len(self.cards_to_review):
            c = self.cards_to_review[self.current_index]
            return {"id": c.id, "front": c.front, "back": c.back, "example": c.example or ""}
        return {}

    @rx.var
    def progress_text(self) -> str:
        if not self.cards_to_review:
            return "0 / 0"
        return f"{self.current_index + 1} / {len(self.cards_to_review)}"

    @rx.var
    def progress_percentage(self) -> int:
        if not self.cards_to_review:
            return 0
        return int(((self.current_index + 1) / len(self.cards_to_review)) * 100)

    async def on_mount(self):
        """Load review session on page mount."""
        from vocab_stack.pages.auth import AuthState
        
        # Page is already protected by auth middleware
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            return rx.redirect("/")
        
        # Always load cards - use selected_topic_id if set
        self.load_user_preferences(auth.current_user_id)
        self.load_review_cards(auth.current_user_id, topic_id=self.selected_topic_id)
    
    def load_user_preferences(self, user_id: int):
        """Load user preferences from settings."""
        from vocab_stack.services.settings_service import SettingsService
        settings = SettingsService.get_user_settings(user_id)
        self.show_examples = settings.get("show_examples", True)
        self.cards_per_session = settings.get("cards_per_session", 20)
        self.review_order = settings.get("review_order", "random")
        self.answer_mode = settings.get("answer_mode", "reveal")

    def load_review_cards(self, user_id: int, topic_id: int | None = None):
        self.loading = True
        # Store the selected topic for later reloads
        self.selected_topic_id = topic_id
        # Get due cards with user's preferred order, limited by cards_per_session
        all_cards = LeitnerService.get_due_cards(
            topic_id=topic_id,
            user_id=user_id,
            review_order=self.review_order
        )
        self.cards_to_review = all_cards[:self.cards_per_session]
        self.current_index = 0
        self.show_answer = False
        self.session_complete = len(self.cards_to_review) == 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.loading = False
    
    def set_topic_for_review(self, topic_id: int):
        """Set the topic to review (called before navigation)."""
        self.selected_topic_id = topic_id

    def flip_card(self):
        self.show_answer = not self.show_answer

    def mark_correct(self):
        if not self.current_card:
            return
        LeitnerService.process_review(self.current_card["id"], user_id=1, was_correct=True)
        self.correct_count += 1
        self._next_card()

    def mark_incorrect(self):
        if not self.current_card:
            return
        LeitnerService.process_review(self.current_card["id"], user_id=1, was_correct=False)
        self.incorrect_count += 1
        self._next_card()

    def _next_card(self):
        self.show_answer = False
        self.current_index += 1
        if self.current_index >= len(self.cards_to_review):
            self.session_complete = True

    def check_answer(self):
        """Check the user's typed answer against the correct answer."""
        if not self.current_card:
            return
        from vocab_stack.utils.text_comparison import check_answer
        
        # Use text comparison utility with normal strictness (case-insensitive)
        self.is_correct = check_answer(self.user_input, self.current_card["back"], "normal")
        self.answer_checked = True

    def submit_answer(self):
        """Submit the typed answer and process the review."""
        if not self.current_card:
            return
        
        self.check_answer()
        
        # Record the review
        LeitnerService.process_review(self.current_card["id"], user_id=1, was_correct=self.is_correct)
        
        if self.is_correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1
            
        self._next_card()

    def set_user_input(self, user_input: str):
        """Set the user input."""
        self.user_input = user_input
    
    def reset_input(self):
        """Reset the user input for the next question."""
        self.user_input = ""
        self.answer_checked = False
        self.is_correct = False


def reveal_mode_display() -> rx.Component:
    """Display for reveal mode where user can flip the card."""
    return rx.card(
        rx.cond(
            ReviewState.show_answer == False,
            rx.vstack(
                rx.text("Question", size="2", color="gray", weight="bold"),
                rx.heading(ReviewState.current_card["front"], size="7", text_align="center"),
                rx.button("Show Answer", on_click=ReviewState.flip_card, size="3", variant="soft"),
                spacing="4",
                align="center",
            ),
            rx.vstack(
                rx.text("Answer", size="2", color="gray", weight="bold"),
                rx.heading(ReviewState.current_card["back"], size="6", text_align="center"),
                # Only show example if preference is enabled AND card has an example
                rx.cond(
                    ReviewState.show_examples & (ReviewState.current_card["example"].to_string() != ""),
                    rx.box(
                        rx.text("Example:", size="2", color="gray", weight="bold"),
                        rx.text(ReviewState.current_card["example"], size="3", style={"fontStyle": "italic"}),
                        padding="1rem",
                        background="var(--gray-3)",
                        border_radius="0.5rem",
                    ),
                ),
                rx.hstack(
                    rx.button("Incorrect", on_click=ReviewState.mark_incorrect, size="3", color_scheme="red", width="150px"),
                    rx.button("Correct", on_click=ReviewState.mark_correct, size="3", color_scheme="green", width="150px"),
                    spacing="4",
                ),
                spacing="4",
                align="center",
            ),
        ),
        width="100%",
        max_width="640px",
        min_height="380px",
        padding="2.5rem",
    )


def type_mode_display() -> rx.Component:
    """Display for type mode where user types the answer."""
    return rx.card(
        rx.vstack(
            rx.text("Question", size="2", color="gray", weight="bold"),
            rx.heading(ReviewState.current_card["front"], size="7", text_align="center"),
            
            # Input field for typing answer
            rx.vstack(
                rx.text("Type your answer:", size="2", color="gray", weight="bold", text_align="center"),
                rx.input(
                    value=ReviewState.user_input,
                    on_change=ReviewState.set_user_input,
                    on_key_down=lambda key: rx.cond(
                        key == "Enter",
                        ReviewState.submit_answer(),
                        rx.noop()  # Do nothing if not Enter key
                    ),
                    placeholder="Enter your answer...",
                    width="100%",
                    size="3",
                ),
                spacing="2",
                width="100%",
            ),
            
            # Submit button if answer not checked yet
            rx.cond(
                ReviewState.answer_checked == False,
                rx.button(
                    "Check Answer",
                    on_click=ReviewState.submit_answer,
                    size="3",
                    variant="solid",
                    color_scheme="blue",
                    width="100%",
                ),
            ),
            
            # Display result after checking answer
            rx.cond(
                ReviewState.answer_checked,
                rx.vstack(
                    rx.cond(
                        ReviewState.is_correct,
                        rx.text("✅ Correct!", size="3", weight="bold", color="green"),
                        rx.text("❌ Incorrect", size="3", weight="bold", color="red"),
                    ),
                    # Show the correct answer
                    rx.text("Correct answer: ", ReviewState.current_card["back"], size="3"),
                    # Override buttons if needed
                    rx.hstack(
                        rx.button("Mark as Correct", on_click=ReviewState.mark_correct, size="2", color_scheme="green"),
                        rx.button("Mark as Incorrect", on_click=ReviewState.mark_incorrect, size="2", color_scheme="red"),
                        spacing="2",
                    ),
                    spacing="3",
                    width="100%",
                    padding_top="1rem",
                ),
            ),
            
            # Only show example if preference is enabled AND card has an example
            rx.cond(
                ReviewState.show_examples & (ReviewState.current_card["example"].to_string() != ""),
                rx.box(
                    rx.text("Example:", size="2", color="gray", weight="bold"),
                    rx.text(ReviewState.current_card["example"], size="3", style={"fontStyle": "italic"}),
                    padding="1rem",
                    background="var(--gray-3)",
                    border_radius="0.5rem",
                    width="100%",
                ),
            ),
            
            spacing="4",
            width="100%",
        ),
        width="100%",
        max_width="640px",
        min_height="380px",
        padding="2.5rem",
    )


def review_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Review Session", size="7"),
            rx.vstack(
                rx.hstack(
                    rx.text(ReviewState.progress_text, weight="bold"),
                    rx.spacer(),
                    rx.text(
                        "✅ " + ReviewState.correct_count.to_string() + " | ❌ " + ReviewState.incorrect_count.to_string(),
                        color="gray",
                    ),
                    width="100%",
                ),
                rx.progress(value=ReviewState.progress_percentage, width="100%", color_scheme="blue"),
                width="100%",
                spacing="2",
            ),
            rx.cond(
                ReviewState.loading,
                rx.spinner(size="3"),
                rx.cond(
                    ReviewState.session_complete,
                    rx.card(
                        rx.vstack(
                            rx.heading("Session Complete!", size="6"),
                            rx.text(
                                "You reviewed " + (ReviewState.correct_count + ReviewState.incorrect_count).to_string() + " cards",
                                size="4",
                            ),
                            rx.link(rx.button("Back to Dashboard", size="3"), href="/"),
                            spacing="3",
                            align="center",
                        ),
                        padding="2rem",
                    ),
                    # Switch between reveal and type modes based on user preference
                    rx.cond(
                        ReviewState.answer_mode == "reveal",
                        reveal_mode_display(),
                        type_mode_display(),
                    ),
                ),
            ),
            spacing="6",
            width="100%",
            max_width="800px",
        ),
        width="100%",
        padding="2rem",
    )
