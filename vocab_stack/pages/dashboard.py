import reflex as rx
from sqlmodel import select
from typing import List
from vocab_stack.models import Flashcard, LeitnerState, User, Topic
from vocab_stack.database import get_session
from vocab_stack.services.statistics_service import StatisticsService
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.pages.auth import AuthState


class DashboardState(rx.State):
    topics: list[dict] = []
    total_due: int = 0
    loading: bool = False
    has_topics: bool = False
    
    # Daily goal tracking
    daily_goal: int = 50
    reviews_today: int = 0
    goal_percentage: int = 0
    goal_reached: bool = False

    async def on_mount(self):
        """Load dashboard on page mount."""
        # Page is already protected by auth middleware
        auth = await self.get_state(AuthState)
        if not auth.current_user_id:
            return rx.redirect("/")
        
        self.load_dashboard_data(auth.current_user_id)

    def load_dashboard_data(self, user_id: int):
        """Load all dashboard data for the given user."""
        self.loading = True
        topics_list: list[dict] = []
        total_due = 0
        
        # Get user-specific data
        with rx.session() as session:
            # Get all topics where the user has flashcards
            from sqlmodel import func
            
            # Get all topics for this user's flashcards
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.user_id == user_id)
            ).all()
            
            # Group by topic and get unique topics
            topic_ids = set(fc.topic_id for fc in flashcards)
            
            for topic_id in topic_ids:
                progress = LeitnerService.get_topic_progress(
                    topic_id=topic_id, 
                    user_id=user_id
                )
                due_today_val = int(progress.get("due_today", 0) or 0)
                
                # Get topic details
                topic = session.exec(
                    select(Topic).where(Topic.id == topic_id)
                ).first()
                
                if topic:
                    topics_list.append({
                        "id": topic.id,
                        "name": topic.name,
                        "description": topic.description or "",
                        "total_cards": int(progress.get("total", 0) or 0),
                        "due_today": due_today_val,
                        "due_positive": due_today_val > 0,
                        "mastered": int(progress.get("mastered", 0) or 0),
                        "mastered_percentage": float(progress.get("mastered_percentage", 0.0) or 0.0),
                    })
                    total_due += due_today_val
                    
        self.topics = topics_list
        self.total_due = total_due
        self.has_topics = len(topics_list) > 0
        
        # Load daily goal progress
        self.load_daily_goal_progress(user_id)
        
        self.loading = False
    
    def load_daily_goal_progress(self, user_id: int):
        """Load user's daily goal and today's review count."""
        from vocab_stack.services.settings_service import SettingsService
        from vocab_stack.services.statistics_service import StatisticsService
        
        # Get user preferences
        settings = SettingsService.get_user_settings(user_id)
        self.daily_goal = settings.get("daily_goal", 50)
        
        # Get today's review count
        overview = StatisticsService.get_user_overview(user_id)
        self.reviews_today = overview.get("reviews_today", 0)
        
        # Calculate progress
        if self.daily_goal > 0:
            self.goal_percentage = min(int((self.reviews_today / self.daily_goal) * 100), 100)
        else:
            self.goal_percentage = 0
        
        self.goal_reached = self.reviews_today >= self.daily_goal


def topic_card(topic: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(topic["name"], size="4"),
                rx.spacer(),
                rx.cond(
                    topic["due_positive"],
                    rx.badge(topic["due_today"].to_string() + " due", color_scheme="orange"),
                    rx.badge(topic["due_today"].to_string() + " due", color_scheme="gray"),
                ),
                width="100%",
            ),
            rx.text(topic["description"], color="gray"),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Total", size="1", color="gray"),
                    rx.heading(topic["total_cards"].to_string(), size="6"),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Mastered", size="1", color="gray"),
                    rx.heading(topic["mastered_percentage"].to_string() + "%", size="6", color="green"),
                    align="start",
                ),
                spacing="6",
            ),
            rx.cond(
                topic["due_positive"],
                rx.link(
                    rx.button("Review Now", width="100%", variant="solid"),
                    href=f"/review?topic_id={topic['id']}",
                ),
                rx.link(
                    rx.button("View Cards", width="100%", variant="soft"),
                    href=f"/review?topic_id={topic['id']}",
                ),
            ),
            align="start",
            spacing="3",
        ),
    )


def dashboard_page() -> rx.Component:
    return rx.vstack(
        rx.heading("Dashboard", size="7"),
        rx.cond(
            DashboardState.loading,
            rx.spinner(size="3"),
            rx.vstack(
                # Cards due and daily goal cards
                rx.grid(
                    rx.card(
                        rx.vstack(
                            rx.text("Cards Due Today", size="2", color="gray"),
                            rx.heading(DashboardState.total_due.to_string(), size="9", color="orange"),
                            rx.link(
                                rx.button("Start Review", size="3", disabled=DashboardState.total_due == 0),
                                href="/review"
                            ),
                            align="center",
                            spacing="3",
                        ),
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Daily Goal", size="2", color="gray", weight="bold"),
                                rx.spacer(),
                                rx.cond(
                                    DashboardState.goal_reached,
                                    rx.badge("🎉 Goal Reached!", color_scheme="green"),
                                ),
                                width="100%",
                            ),
                            rx.heading(
                                DashboardState.reviews_today.to_string() + " / " + DashboardState.daily_goal.to_string(),
                                size="7",
                                color="blue",
                            ),
                            rx.progress(
                                value=DashboardState.goal_percentage,
                                width="100%",
                                color_scheme="blue",
                            ),
                            rx.text(
                                DashboardState.goal_percentage.to_string() + "% complete",
                                size="2",
                                color="gray",
                            ),
                            align="start",
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.heading("Your Topics", size="5", margin_top="1rem"),
                rx.cond(
                    DashboardState.has_topics,
                    rx.grid(
                        rx.foreach(DashboardState.topics, topic_card),
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
