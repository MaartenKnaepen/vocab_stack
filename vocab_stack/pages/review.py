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

    def on_mount(self):
        self.load_user_preferences()
        self.load_review_cards()
    
    def load_user_preferences(self):
        """Load user preferences from settings."""
        from vocab_stack.services.settings_service import SettingsService
        settings = SettingsService.get_user_settings(1)
        self.show_examples = settings.get("show_examples", True)
        self.cards_per_session = settings.get("cards_per_session", 20)
        self.review_order = settings.get("review_order", "random")

    def load_review_cards(self, topic_id: int | None = None):
        self.loading = True
        # Get due cards with user's preferred order, limited by cards_per_session
        all_cards = LeitnerService.get_due_cards(
            topic_id=topic_id,
            user_id=1,
            review_order=self.review_order
        )
        self.cards_to_review = all_cards[:self.cards_per_session]
        self.current_index = 0
        self.show_answer = False
        self.session_complete = len(self.cards_to_review) == 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.loading = False

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


def flashcard_display() -> rx.Component:
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
