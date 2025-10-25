"""Statistics and analytics service."""
from datetime import datetime, date, timedelta
from typing import Dict, List
from sqlmodel import select, func, and_
from sqlalchemy import Integer
from vocab_stack.models import ReviewHistory, Flashcard, LeitnerState, Topic
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
                    func.sum(func.cast(ReviewHistory.was_correct, Integer)).label("correct")
                )
                .where(
                    and_(
                        ReviewHistory.user_id == user_id,
                        func.date(ReviewHistory.review_date) >= start_date
                    )
                )
                .group_by(func.date(ReviewHistory.review_date))
            ).all()
            
            # Create data dict - func.date() returns strings, not date objects
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
                
                # Compare with date_str since func.date() returns strings
                if date_str in review_data:
                    total = review_data[date_str]["count"]
                    correct = review_data[date_str]["correct"] or 0
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
            # Get all review dates - func.date() returns strings, so we need to convert them
            review_date_strings = session.exec(
                select(func.date(ReviewHistory.review_date).distinct())
                .where(ReviewHistory.user_id == user_id)
                .order_by(func.date(ReviewHistory.review_date).desc())
            ).all()
            
            if not review_date_strings:
                return {"current_streak": 0, "longest_streak": 0}
            
            # Convert strings to date objects
            review_dates = []
            for date_str in review_date_strings:
                if isinstance(date_str, str):
                    review_dates.append(datetime.strptime(date_str, "%Y-%m-%d").date())
                else:
                    review_dates.append(date_str)
            
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
                days_diff = (review_dates[i - 1] - review_dates[i]).days
                if days_diff == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            
            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
            }
