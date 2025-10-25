"""Navigation bar and layout components."""
import reflex as rx


def navbar() -> rx.Component:
    """Top navigation bar."""
    return rx.box(
        rx.hstack(
            rx.heading("Vocab App", size="6"),
            rx.spacer(),
            rx.hstack(
                rx.link(rx.button("Dashboard", variant="soft", size="2"), href="/dashboard"),
                rx.link(rx.button("Review", variant="soft", size="2"), href="/review"),
                rx.link(rx.button("Topics", variant="soft", size="2"), href="/topics"),
                rx.link(rx.button("Cards", variant="soft", size="2"), href="/cards"),
                rx.link(rx.button("Statistics", variant="soft", size="2"), href="/statistics"),
                rx.link(rx.button("Settings", variant="soft", size="2"), href="/settings"),
                spacing="3",
            ),
            width="100%",
            align="center",
        ),
        background="var(--accent-3)",
        padding="0.75rem 1rem",
        position="sticky",
        top="0",
        z_index="1000",
        border_bottom="1px solid var(--gray-6)",
        width="100%",
    )


def layout(content: rx.Component) -> rx.Component:
    """Main layout with navbar and page container."""
    return rx.vstack(
        navbar(),
        rx.container(content, padding="1.5rem", max_width="1200px"),
        width="100%",
        min_height="100vh",
        spacing="0",
    )
