"""Admin dashboard for monitoring users."""
import reflex as rx
from sqlmodel import select
from typing import List
from vocab_stack.models import User, Flashcard
from vocab_stack.database import get_session
from vocab_stack.services.statistics_service import StatisticsService
from vocab_stack.pages.auth import AuthState


class AdminState(rx.State):
    """Admin state for managing and monitoring users."""
    
    # User management
    users: List[dict] = []
    total_users: int = 0
    loading: bool = False
    
    # Permissions
    is_admin: bool = False

    async def on_mount(self):
        # Check if current user has admin privileges
        auth = await self.get_state(AuthState)
        if auth.is_logged_in and auth.is_admin:
            self.is_admin = True
            self.load_user_stats()
        else:
            # This will redirect to dashboard since page is protected
            pass

    def load_user_stats(self):
        if not self.is_admin:
            return
            
        self.loading = True
        users_list: List[dict] = []
        
        with get_session() as session:
            all_users = session.exec(select(User)).all()
            for user in all_users:
                # Get user statistics
                stats = StatisticsService.get_user_overview(user.id)
                total_cards = session.exec(
                    select(Flashcard).where(Flashcard.user_id == user.id)
                ).count()
                
                users_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at,
                    "total_cards": total_cards,
                    "reviews_today": stats.get("reviews_today", 0),
                    "reviews_total": stats.get("total_reviews", 0),
                    "streak": stats.get("current_streak", 0),
                })
        
        self.users = users_list
        self.total_users = len(users_list)
        self.loading = False
    
    @rx.var
    def active_users_today(self) -> int:
        """Count of users who reviewed cards today."""
        return sum(1 for user in self.users if user.get("reviews_today", 0) > 0)
    
    @rx.var
    def total_cards_all_users(self) -> int:
        """Total cards across all users."""
        return sum(user.get("total_cards", 0) for user in self.users)


def user_card(user: dict) -> rx.Component:
    """Display a user's stats card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(user["username"], size="4"),
                rx.spacer(),
                rx.badge("User", color_scheme="blue"),
                width="100%",
            ),
            rx.text(f"Email: {user['email']}", color="gray", size="2"),
            rx.divider(),
            rx.grid(
                rx.vstack(
                    rx.text("Total Cards", size="2", color="gray"),
                    rx.heading(user["total_cards"].to_string(), size="6"),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Reviews (Today)", size="2", color="gray"),
                    rx.heading(user["reviews_today"].to_string(), size="6"),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Total Reviews", size="2", color="gray"),
                    rx.heading(user["reviews_total"].to_string(), size="6"),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Current Streak", size="2", color="gray"),
                    rx.heading(user["streak"].to_string(), size="6"),
                    align="start",
                ),
                columns="4",
                spacing="4",
            ),
            align="start",
            spacing="3",
        ),
    )


def admin_dashboard_page() -> rx.Component:
    """Admin dashboard page."""
    return rx.vstack(
        rx.heading("Admin Dashboard", size="7"),
        rx.cond(
            AdminState.is_admin,
            rx.vstack(
                rx.cond(
                    AdminState.loading,
                    rx.spinner(size="3"),
                    rx.vstack(
                        # Summary cards
                        rx.grid(
                            rx.card(
                                rx.vstack(
                                    rx.text("Total Users", size="2", color="gray"),
                                    rx.heading(AdminState.total_users.to_string(), size="9", color="blue"),
                                    align="center",
                                ),
                            ),
                            rx.card(
                                rx.vstack(
                                    rx.text("Active Today", size="2", color="gray"),
                                    rx.heading(
                                        AdminState.active_users_today,
                                        size="9",
                                        color="green"
                                    ),
                                    align="center",
                                ),
                            ),
                            rx.card(
                                rx.vstack(
                                    rx.text("Total Cards", size="2", color="gray"),
                                    rx.heading(
                                        AdminState.total_cards_all_users,
                                        size="9",
                                        color="purple"
                                    ),
                                    align="center",
                                ),
                            ),
                            columns="3",
                            spacing="4",
                            width="100%",
                        ),
                        
                        rx.heading("Users", size="5", margin_top="1rem"),
                        rx.grid(
                            rx.foreach(AdminState.users, user_card),
                            columns="2",
                            spacing="4",
                            width="100%",
                        ),
                        width="100%",
                        spacing="4",
                    ),
                ),
                width="100%",
            ),
            rx.vstack(
                rx.heading("Access Denied", size="9"),
                rx.text("You must be an admin to access this page."),
                width="100%",
                height="80vh",
                align="center",
                justify="center",
            )
        ),
        width="100%",
        spacing="6",
    )


def register_admin_routes(app):
    """Register admin routes with authentication."""
    def require_auth(page):
        """Middleware to require authentication for a page."""
        def protected_page():
            return rx.cond(
                AuthState.is_logged_in,
                page(),
                rx.vstack(
                    rx.heading("Please log in", size="9"),
                    rx.link("Go to login", href="/", color="blue.500"),
                    width="100%",
                    height="80vh",
                    align="center",
                    justify="center",
                )
            )
        return protected_page
    
    def require_admin(page):
        """Middleware to require admin privileges."""
        def protected_page():
            return rx.cond(
                AuthState.is_admin,
                page(),
                rx.vstack(
                    rx.heading("Admin Access Only", size="9"),
                    rx.text("You need admin privileges to access this page."),
                    rx.link("Go to dashboard", href="/dashboard", color="blue.500"),
                    width="100%",
                    height="80vh",
                    align="center",
                    justify="center",
                )
            )
        return protected_page
    
    # Add admin routes
    app.add_page(
        lambda: require_auth(require_admin(admin_dashboard_page))(),
        route="/admin",
        title="Admin Dashboard - Vocab App",
        on_load=[AuthState.on_load, AdminState.on_mount],
    )