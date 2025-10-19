"""Date calculation utilities for Leitner algorithm."""
from datetime import date, timedelta


# Box review intervals (in days)
BOX_INTERVALS = {
    1: 1,   # Daily
    2: 3,   # Every 3 days
    3: 7,   # Weekly
    4: 14,  # Bi-weekly
    5: 30,  # Monthly
}


def get_review_interval(box_number: int) -> int:
    """
    Get review interval in days for a given box number.
    
    Args:
        box_number: Box number (1-5)
        
    Returns:
        Number of days until next review
        
    Raises:
        ValueError: If box_number is not between 1-5
    """
    if box_number not in BOX_INTERVALS:
        raise ValueError(f"Box number must be between 1-5, got {box_number}")
    
    return BOX_INTERVALS[box_number]


def calculate_next_review_date(box_number: int, last_reviewed: date = None) -> date:
    """
    Calculate next review date based on box number.
    
    Args:
        box_number: Current box number (1-5)
        last_reviewed: Date of last review (defaults to today)
        
    Returns:
        Date of next scheduled review
        
    Examples:
        >>> calculate_next_review_date(1, date(2024, 1, 1))
        date(2024, 1, 2)  # 1 day later
        
        >>> calculate_next_review_date(3, date(2024, 1, 1))
        date(2024, 1, 8)  # 7 days later
    """
    if last_reviewed is None:
        last_reviewed = date.today()
    
    interval_days = get_review_interval(box_number)
    next_date = last_reviewed + timedelta(days=interval_days)
    
    return next_date


def is_due_for_review(next_review_date: date) -> bool:
    """
    Check if a card is due for review today.
    
    Args:
        next_review_date: Scheduled review date
        
    Returns:
        True if review is due (today or overdue), False otherwise
    """
    return next_review_date <= date.today()


def days_until_review(next_review_date: date) -> int:
    """
    Calculate days until next review.
    
    Args:
        next_review_date: Scheduled review date
        
    Returns:
        Number of days (negative if overdue)
    """
    return (next_review_date - date.today()).days
