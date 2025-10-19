"""Dashboard page showing topic summaries and due counts."""
import reflex as rx
from sqlmodel import select
from vocab_stack.services.leitner_service import LeitnerService
from vocab_stack.models import Topic


class DashboardState(rx.State):
    topics: list[dict] = []
    total_due: int = 0
    loading: bool = False
    has_topics: bool = False

    def on_mount(self):
        self.load_dashboard_data()

    def load_dashboard_data(self):
        self.loading = True
        topics_list: list[dict] = []
        total_due = 0
        with rx.session() as session:
            rows = session.exec(select(Topic)).all()
            for t in rows:
                progress = LeitnerService.get_topic_progress(topic_id=t.id, user_id=1)
                due_today_val = int(progress.get("due_today", 0) or 0)
                topics_list.append({
                    "id": t.id,
                    "name": t.name,
                    "description": t.description or "",
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
        self.loading = False


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
                rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Cards Due Today", size="2", color="gray"),
                            rx.heading(DashboardState.total_due.to_string(), size="9", color="orange"),
                            align="start",
                        ),
                        rx.spacer(),
                        rx.link(rx.button("Start Review", size="3", disabled=DashboardState.total_due == 0), href="/review"),
                        width="100%",
                        align="center",
                    ),
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
