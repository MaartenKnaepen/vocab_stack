"""Statistics and analytics page."""
import reflex as rx
from vocab_stack.services.statistics_service import StatisticsService


class StatsState(rx.State):
    """State for statistics page."""
    
    # Overview stats
    total_cards: int = 0
    total_reviews: int = 0
    reviews_today: int = 0
    cards_due: int = 0
    overall_accuracy: float = 0
    mastered_cards: int = 0
    
    # Box distribution
    box_1_count: int = 0
    box_2_count: int = 0
    box_3_count: int = 0
    box_4_count: int = 0
    box_5_count: int = 0
    
    # Review history
    review_dates: list[str] = []
    review_totals: list[int] = []
    review_correct: list[int] = []
    review_incorrect: list[int] = []
    
    # Topic stats
    topic_stats: list[dict] = []
    has_topic_stats: bool = False
    
    # Streak
    current_streak: int = 0
    longest_streak: int = 0
    
    loading: bool = False
    
    def on_mount(self):
        """Load statistics on page mount."""
        self.load_statistics()
    
    def load_statistics(self):
        """Load all statistics."""
        self.loading = True
        
        # User ID hardcoded to 1 for demo
        user_id = 1
        
        # Get overview
        overview = StatisticsService.get_user_overview(user_id)
        self.total_cards = overview["total_cards"]
        self.total_reviews = overview["total_reviews"]
        self.reviews_today = overview["reviews_today"]
        self.cards_due = overview["cards_due"]
        self.overall_accuracy = overview["overall_accuracy"]
        self.mastered_cards = overview["mastered_cards"]
        
        # Box distribution - extract to separate state vars for safe rendering
        box_dist = overview["box_distribution"]
        self.box_1_count = box_dist.get(1, 0)
        self.box_2_count = box_dist.get(2, 0)
        self.box_3_count = box_dist.get(3, 0)
        self.box_4_count = box_dist.get(4, 0)
        self.box_5_count = box_dist.get(5, 0)
        
        # Get review history (last 7 days)
        history = StatisticsService.get_review_history_chart(user_id, days=7)
        self.review_dates = history["dates"]
        self.review_totals = history["total"]
        self.review_correct = history["correct"]
        self.review_incorrect = history["incorrect"]
        
        # Get topic statistics
        topic_stats = StatisticsService.get_topic_statistics(user_id)
        self.topic_stats = topic_stats
        self.has_topic_stats = len(topic_stats) > 0
        
        # Get streak
        streak = StatisticsService.get_learning_streak(user_id)
        self.current_streak = streak["current_streak"]
        self.longest_streak = streak["longest_streak"]
        
        self.loading = False


def stat_card(title: str, value: rx.Var, color: str = "blue") -> rx.Component:
    """Render a statistic card."""
    return rx.card(
        rx.vstack(
            rx.text(title, size="2", color="gray", weight="bold"),
            rx.heading(value, size="8", color=color),
            spacing="2",
            align="center",
        ),
        width="100%",
    )


def box_distribution_chart() -> rx.Component:
    """Render box distribution visualization."""
    return rx.card(
        rx.vstack(
            rx.heading("Box Distribution", size="5"),
            rx.vstack(
                # Box 1
                rx.hstack(
                    rx.text("Box 1", width="60px"),
                    rx.box(
                        width=rx.cond(StatsState.box_1_count > 0, StatsState.box_1_count.to_string() + "0px", "0px"),
                        height="30px",
                        background="var(--red-9)",
                        border_radius="4px",
                    ),
                    rx.text(StatsState.box_1_count.to_string(), weight="bold"),
                    width="100%",
                    align="center",
                ),
                # Box 2
                rx.hstack(
                    rx.text("Box 2", width="60px"),
                    rx.box(
                        width=rx.cond(StatsState.box_2_count > 0, StatsState.box_2_count.to_string() + "0px", "0px"),
                        height="30px",
                        background="var(--orange-9)",
                        border_radius="4px",
                    ),
                    rx.text(StatsState.box_2_count.to_string(), weight="bold"),
                    width="100%",
                    align="center",
                ),
                # Box 3
                rx.hstack(
                    rx.text("Box 3", width="60px"),
                    rx.box(
                        width=rx.cond(StatsState.box_3_count > 0, StatsState.box_3_count.to_string() + "0px", "0px"),
                        height="30px",
                        background="var(--yellow-9)",
                        border_radius="4px",
                    ),
                    rx.text(StatsState.box_3_count.to_string(), weight="bold"),
                    width="100%",
                    align="center",
                ),
                # Box 4
                rx.hstack(
                    rx.text("Box 4", width="60px"),
                    rx.box(
                        width=rx.cond(StatsState.box_4_count > 0, StatsState.box_4_count.to_string() + "0px", "0px"),
                        height="30px",
                        background="var(--green-9)",
                        border_radius="4px",
                    ),
                    rx.text(StatsState.box_4_count.to_string(), weight="bold"),
                    width="100%",
                    align="center",
                ),
                # Box 5
                rx.hstack(
                    rx.text("Box 5", width="60px"),
                    rx.box(
                        width=rx.cond(StatsState.box_5_count > 0, StatsState.box_5_count.to_string() + "0px", "0px"),
                        height="30px",
                        background="var(--blue-9)",
                        border_radius="4px",
                    ),
                    rx.text(StatsState.box_5_count.to_string(), weight="bold"),
                    width="100%",
                    align="center",
                ),
                width="100%",
                spacing="2",
            ),
            spacing="4",
            align="start",
        ),
    )


def review_history_item(date: str, idx: int) -> rx.Component:
    """Render a single review history item."""
    return rx.hstack(
        rx.text(date[-5:], width="60px", size="2"),  # Show MM-DD
        rx.hstack(
            rx.box(
                width=rx.cond(
                    StatsState.review_correct[idx] > 0,
                    StatsState.review_correct[idx].to_string() + "px",
                    "0px"
                ),
                height="25px",
                background="var(--green-9)",
                border_radius="4px 0 0 4px",
            ),
            rx.box(
                width=rx.cond(
                    StatsState.review_incorrect[idx] > 0,
                    StatsState.review_incorrect[idx].to_string() + "px",
                    "0px"
                ),
                height="25px",
                background="var(--red-9)",
                border_radius="0 4px 4px 0",
            ),
            spacing="0",
        ),
        rx.text(
            StatsState.review_totals[idx].to_string() + " reviews",
            size="2",
            color="gray",
        ),
        width="100%",
        align="center",
    )


def review_history_display() -> rx.Component:
    """Display review history as simple bars."""
    return rx.card(
        rx.vstack(
            rx.heading("Review History (Last 7 Days)", size="5"),
            rx.vstack(
                rx.foreach(
                    StatsState.review_dates,
                    lambda date, idx: review_history_item(date, idx),
                ),
                width="100%",
                spacing="2",
            ),
            rx.hstack(
                rx.hstack(
                    rx.box(width="15px", height="15px", background="var(--green-9)"),
                    rx.text("Correct", size="2"),
                    spacing="2",
                ),
                rx.hstack(
                    rx.box(width="15px", height="15px", background="var(--red-9)"),
                    rx.text("Incorrect", size="2"),
                    spacing="2",
                ),
                spacing="4",
            ),
            spacing="4",
            align="start",
        ),
    )


def topic_stats_row(topic: dict) -> rx.Component:
    """Render a topic statistics row."""
    return rx.table.row(
        rx.table.cell(rx.text(topic["topic_name"], weight="bold")),
        rx.table.cell(topic["total_cards"].to_string()),
        rx.table.cell(
            rx.text(
                topic["mastered"].to_string() + " (" + topic["mastered_percentage"].to_string() + "%)",
                color="green",
            )
        ),
        rx.table.cell(topic["total_reviews"].to_string()),
        rx.table.cell(
            rx.text(
                topic["accuracy"].to_string() + "%",
                color="blue",
            )
        ),
    )


def topic_stats_table() -> rx.Component:
    """Display topic statistics table."""
    return rx.card(
        rx.vstack(
            rx.heading("Topic Statistics", size="5"),
            rx.cond(
                StatsState.has_topic_stats,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Topic"),
                            rx.table.column_header_cell("Cards"),
                            rx.table.column_header_cell("Mastered"),
                            rx.table.column_header_cell("Reviews"),
                            rx.table.column_header_cell("Accuracy"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            StatsState.topic_stats,
                            topic_stats_row,
                        ),
                    ),
                ),
                rx.text("No topic data available", color="gray"),
            ),
            spacing="3",
            align="start",
        ),
    )


def statistics_page() -> rx.Component:
    """Statistics page content."""
    return rx.vstack(
        rx.heading("Statistics & Progress", size="8"),
        
        rx.cond(
            StatsState.loading,
            rx.spinner(size="3"),
            rx.vstack(
                # Overview stats
                rx.grid(
                    stat_card("Total Cards", StatsState.total_cards.to_string()),
                    stat_card("Cards Due", StatsState.cards_due.to_string(), "orange"),
                    stat_card("Reviews Today", StatsState.reviews_today.to_string(), "green"),
                    stat_card("Overall Accuracy", StatsState.overall_accuracy.to_string() + "%", "blue"),
                    stat_card("Mastered", StatsState.mastered_cards.to_string(), "green"),
                    stat_card("Total Reviews", StatsState.total_reviews.to_string(), "purple"),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                
                # Streak cards
                rx.hstack(
                    rx.card(
                        rx.vstack(
                            rx.text("🔥 Current Streak", size="3", weight="bold"),
                            rx.heading(StatsState.current_streak.to_string() + " days", size="7", color="orange"),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                    ),
                    rx.card(
                        rx.vstack(
                            rx.text("🏆 Longest Streak", size="3", weight="bold"),
                            rx.heading(StatsState.longest_streak.to_string() + " days", size="7", color="gold"),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                
                # Charts
                rx.grid(
                    box_distribution_chart(),
                    review_history_display(),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                
                # Topic stats
                topic_stats_table(),
                
                width="100%",
                spacing="6",
            ),
        ),
        
        spacing="6",
        width="100%",
    )
