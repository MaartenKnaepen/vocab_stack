"""Error handling utilities."""
import reflex as rx
from typing import Callable, Any
import traceback


def handle_errors(func: Callable) -> Callable:
    """Decorator for handling errors in state methods."""
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            traceback.print_exc()
            self.error_message = f"An error occurred: {str(e)}"
            return None
    return wrapper


def validate_not_empty(value: str, field_name: str) -> tuple[bool, str]:
    """Validate that a string is not empty."""
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty"
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Basic email validation."""
    if not email or "@" not in email or "." not in email:
        return False, "Invalid email format"
    return True, ""


def validate_range(value: int, min_val: int, max_val: int, field_name: str) -> tuple[bool, str]:
    """Validate that a value is within range."""
    if value < min_val or value > max_val:
        return False, f"{field_name} must be between {min_val} and {max_val}"
    return True, ""
