"""Toast notification components."""
import reflex as rx


def show_success(message: str) -> rx.Component:
    """Show success notification."""
    return rx.callout(
        message,
        icon="check",
        color_scheme="green",
    )


def show_error(message: str) -> rx.Component:
    """Show error notification."""
    return rx.callout(
        message,
        icon="triangle_alert",
        color_scheme="red",
    )


def show_info(message: str) -> rx.Component:
    """Show info notification."""
    return rx.callout(
        message,
        icon="info",
        color_scheme="blue",
    )


def show_warning(message: str) -> rx.Component:
    """Show warning notification."""
    return rx.callout(
        message,
        icon="alert_triangle",
        color_scheme="orange",
    )
