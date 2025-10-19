# Phase 5: Statistics & Progress Tracking - Implementation Guide

## Overview
This guide covers implementing comprehensive statistics and progress tracking features.

**Estimated Time**: 3-4 hours  
**Goal**: Visual statistics dashboard with charts and progress metrics

---

## Prerequisites

- ✅ Phase 4 completed (CRUD operations)
- ✅ Review history being recorded
- ✅ Leitner states tracking correctly

---

## Step 1: Create Statistics Service (60 minutes)

Create `vocab_app/services/statistics_service.py`:

```python
"""Statistics and analytics service."""
from datetime import datetime, date, timedelta
from typing import Dict, List
from sqlmodel import select, func, and_
from vocab_app.models import ReviewHistory, Flashcard, LeitnerState, Topic
import reflex as rx


class StatisticsService:
    """Service for calculating statistics and analytics."""
    
    @staticmethod
    def get_user_overview(user_id: int) -> dict:
        """Get overall user statistics."""
        with rx.session() as session:
            # Total cards
            total_cards = session.exec(
                select(func.count(Flashcard.id)).where(Flashcard.user_id == user_id)
            ).one()
            
            # Total reviews
            total_reviews = session.exec(
                select(func.count(ReviewHistory.id)).where(ReviewHistory.user_id == user_id)
            ).one()
            
            # Reviews today
            today = datetime.utcnow().date()
            reviews_today = session.exec(
                select(func.count(ReviewHistory.id)).where(
                    and_(
                        ReviewHistory.user_id == user_id,
                        func.date(ReviewHistory.review_date) == today
                    )
                )
            ).one()
            
            # Cards by box
            box_distribution = {}
            for box in range(1, 6):
                count = session.exec(
                    select(func.count(LeitnerState.id))
                    .join(Flashcard)
                    .where(
                        and_(
                            Flashcard.user_id == user_id,
                            LeitnerState.box_number == box
                        )
                    )
                ).one()
                box_distribution[box] = count
            
            # Cards due today
            cards_due = session.exec(
                select(func.count(LeitnerState.id))
                .join(Flashcard)
                .where(
                    and_(
                        Flashcard.user_id == user_id,
                        LeitnerState.next_review_date <= date.today()
                    )
                )
            ).one()
            
            # Overall accuracy
            correct_reviews = session.exec(
                select(func.count(ReviewHistory.id)).where(
                    and_(
                        ReviewHistory.user_id == user_id,
                        ReviewHistory.was_correct == True
                    )
                )
            ).one()
            
            accuracy = (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0
            
            return {
                "total_cards": total_cards,
                "total_reviews": total_reviews,
                "reviews_today": reviews_today,
                "cards_due": cards_due,
                "box_distribution": box_distribution,
                "overall_accuracy": round(accuracy, 2),
                "mastered_cards": box_distribution.get(5, 0),
            }
    
    @staticmethod
    def get_review_history_chart(user_id: int, days: int = 7) -> dict:
        """Get review history for the last N days."""
        with rx.session() as session:
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)
            
            # Get reviews grouped by date
            reviews = session.exec(
                select(
                    func.date(ReviewHistory.review_date).label("date"),
                    func.count(ReviewHistory.id).label("count"),
                    func.sum(func.cast(ReviewHistory.was_correct, type_=1)).label("correct")
                )
                .where(
                    and_(
                        ReviewHistory.user_id == user_id,
                        func.date(ReviewHistory.review_date) >= start_date
                    )
                )
                .group_by(func.date(ReviewHistory.review_date))
            ).all()
            
            # Create data dict
            review_data = {r[0]: {"count": r[1], "correct": r[2]} for r in reviews}
            
            # Fill in missing dates
            result = {
                "dates": [],
                "total": [],
                "correct": [],
                "incorrect": [],
            }
            
            for i in range(days):
                current_date = start_date + timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")
                
                result["dates"].append(date_str)
                
                if current_date in review_data:
                    total = review_data[current_date]["count"]
                    correct = review_data[current_date]["correct"] or 0
                    result["total"].append(total)
                    result["correct"].append(correct)
                    result["incorrect"].append(total - correct)
                else:
                    result["total"].append(0)
                    result["correct"].append(0)
                    result["incorrect"].append(0)
            
            return result
    
    @staticmethod
    def get_topic_statistics(user_id: int) -> List[dict]:
        """Get statistics for each topic."""
        with rx.session() as session:
            topics = session.exec(select(Topic)).all()
            
            result = []
            for topic in topics:
                # Total cards
                total = session.exec(
                    select(func.count(Flashcard.id)).where(
                        and_(
                            Flashcard.topic_id == topic.id,
                            Flashcard.user_id == user_id
                        )
                    )
                ).one()
                
                if total == 0:
                    continue
                
                # Mastered cards (Box 5)
                mastered = session.exec(
                    select(func.count(LeitnerState.id))
                    .join(Flashcard)
                    .where(
                        and_(
                            Flashcard.topic_id == topic.id,
                            Flashcard.user_id == user_id,
                            LeitnerState.box_number == 5
                        )
                    )
                ).one()
                
                # Total reviews for topic
                reviews = session.exec(
                    select(func.count(ReviewHistory.id))
                    .join(Flashcard)
                    .where(
                        and_(
                            Flashcard.topic_id == topic.id,
                            ReviewHistory.user_id == user_id
                        )
                    )
                ).one()
                
                # Correct reviews
                correct = session.exec(
                    select(func.count(ReviewHistory.id))
                    .join(Flashcard)
                    .where(
                        and_(
                            Flashcard.topic_id == topic.id,
                            ReviewHistory.user_id == user_id,
                            ReviewHistory.was_correct == True
                        )
                    )
                ).one()
                
                accuracy = (correct / reviews * 100) if reviews > 0 else 0
                
                result.append({
                    "topic_name": topic.name,
                    "total_cards": total,
                    "mastered": mastered,
                    "mastered_percentage": round(mastered / total * 100, 2),
                    "total_reviews": reviews,
                    "accuracy": round(accuracy, 2),
                })
            
            return result
    
    @staticmethod
    def get_learning_streak(user_id: int) -> dict:
        """Calculate current learning streak."""
        with rx.session() as session:
            # Get all review dates
            review_dates = session.exec(
                select(func.date(ReviewHistory.review_date).distinct())
                .where(ReviewHistory.user_id == user_id)
                .order_by(func.date(ReviewHistory.review_date).desc())
            ).all()
            
            if not review_dates:
                return {"current_streak": 0, "longest_streak": 0}
            
            # Calculate current streak
            current_streak = 0
            check_date = date.today()
            
            for review_date in review_dates:
                if review_date == check_date or review_date == check_date - timedelta(days=1):
                    current_streak += 1
                    check_date = review_date - timedelta(days=1)
                else:
                    break
            
            # Calculate longest streak
            longest_streak = 1
            temp_streak = 1
            
            for i in range(1, len(review_dates)):
                if review_dates[i - 1] - review_dates[i] == timedelta(days=1):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            
            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
            }
```

---

## Step 2: Create Statistics Page (90 minutes)

Create `vocab_app/pages/statistics.py`:

```python
"""Statistics and analytics page."""
import reflex as rx
from vocab_app.services.statistics_service import StatisticsService


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
    box_distribution: dict = {}
    
    # Review history
    review_dates: list[str] = []
    review_totals: list[int] = []
    review_correct: list[int] = []
    review_incorrect: list[int] = []
    
    # Topic stats
    topic_stats: list[dict] = []
    
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
        self.box_distribution = overview["box_distribution"]
        
        # Get review history (last 7 days)
        history = StatisticsService.get_review_history_chart(user_id, days=7)
        self.review_dates = history["dates"]
        self.review_totals = history["total"]
        self.review_correct = history["correct"]
        self.review_incorrect = history["incorrect"]
        
        # Get topic statistics
        self.topic_stats = StatisticsService.get_topic_statistics(user_id)
        
        # Get streak
        streak = StatisticsService.get_learning_streak(user_id)
        self.current_streak = streak["current_streak"]
        self.longest_streak = streak["longest_streak"]
        
        self.loading = False


def stat_card(title: str, value: str, color: str = "blue") -> rx.Component:
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
                rx.foreach(
                    [1, 2, 3, 4, 5],
                    lambda box: rx.hstack(
                        rx.text(f"Box {box}", width="60px"),
                        rx.box(
                            width=f"{StatsState.box_distribution.get(str(box), 0) * 20}px",
                            height="30px",
                            background=f"var(--{['red', 'orange', 'yellow', 'green', 'blue'][box - 1]}-9)",
                            border_radius="4px",
                        ),
                        rx.text(
                            StatsState.box_distribution.get(str(box), 0).to_string(),
                            weight="bold",
                        ),
                        width="100%",
                        align="center",
                    ),
                ),
                width="100%",
                spacing="2",
            ),
            spacing="4",
            align="start",
        ),
    )


def review_history_display() -> rx.Component:
    """Display review history as simple bars."""
    return rx.card(
        rx.vstack(
            rx.heading("Review History (Last 7 Days)", size="5"),
            rx.vstack(
                rx.foreach(
                    StatsState.review_dates,
                    lambda date, idx: rx.hstack(
                        rx.text(date[-5:], width="60px", size="2"),  # Show MM-DD
                        rx.hstack(
                            rx.box(
                                width=f"{StatsState.review_correct[idx] * 10}px",
                                height="25px",
                                background="var(--green-9)",
                                border_radius="4px 0 0 4px",
                            ),
                            rx.box(
                                width=f"{StatsState.review_incorrect[idx] * 10}px",
                                height="25px",
                                background="var(--red-9)",
                                border_radius="0 4px 4px 0",
                            ),
                            spacing="0",
                        ),
                        rx.text(
                            f"{StatsState.review_totals[idx]} reviews",
                            size="2",
                            color="gray",
                        ),
                        width="100%",
                        align="center",
                    ),
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


def topic_stats_table() -> rx.Component:
    """Display topic statistics table."""
    return rx.card(
        rx.vstack(
            rx.heading("Topic Statistics", size="5"),
            rx.cond(
                StatsState.topic_stats.length() > 0,
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
                            lambda topic: rx.table.row(
                                rx.table.cell(rx.text(topic["topic_name"], weight="bold")),
                                rx.table.cell(topic["total_cards"].to_string()),
                                rx.table.cell(
                                    rx.text(
                                        f"{topic['mastered']} ({topic['mastered_percentage']}%)",
                                        color="green",
                                    )
                                ),
                                rx.table.cell(topic["total_reviews"].to_string()),
                                rx.table.cell(
                                    rx.text(
                                        f"{topic['accuracy']}%",
                                        color="blue",
                                    )
                                ),
                            ),
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
                    stat_card("Overall Accuracy", f"{StatsState.overall_accuracy}%", "blue"),
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
                            rx.heading(f"{StatsState.current_streak} days", size="7", color="orange"),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                    ),
                    rx.card(
                        rx.vstack(
                            rx.text("🏆 Longest Streak", size="3", weight="bold"),
                            rx.heading(f"{StatsState.longest_streak} days", size="7", color="gold"),
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
```

---

## Step 3: Add Statistics to Navigation (10 minutes)

Update `vocab_app/components/navigation.py`:

```python
def navbar() -> rx.Component:
    """Top navigation bar."""
    return rx.box(
        rx.hstack(
            rx.heading("🎴 Vocab App", size="7"),
            rx.spacer(),
            rx.hstack(
                rx.link(rx.button("Dashboard", variant="soft"), href="/"),
                rx.link(rx.button("Review", variant="soft"), href="/review"),
                rx.link(rx.button("Topics", variant="soft"), href="/topics"),
                rx.link(rx.button("Cards", variant="soft"), href="/cards"),
                rx.link(rx.button("Statistics", variant="soft"), href="/statistics"),  # NEW
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
```

---

## Step 4: Update App Routes (10 minutes)

Update `vocab_app/app.py`:

```python
from vocab_app.pages.statistics import statistics_page, StatsState

# Add statistics page
app.add_page(
    lambda: layout(statistics_page()),
    route="/statistics",
    title="Statistics - Vocab App",
    on_load=StatsState.on_mount,
)
```

---

## Verification Checklist

- [ ] Overview statistics display correctly
- [ ] Box distribution chart shows all 5 boxes
- [ ] Review history shows last 7 days
- [ ] Topic statistics table populated
- [ ] Current streak calculates correctly
- [ ] Longest streak tracks properly
- [ ] All percentages rounded to 2 decimals
- [ ] Page updates on navigation

---

## Next Steps

**Ready for Phase 6**: Settings & User Preferences

---

**Phase 5 Complete!** 🎉
