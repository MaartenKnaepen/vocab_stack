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
    
    # UI state
    success_message: str = ""
    error_message: str = ""
    
    # Password reset
    reset_user_id: int = -1
    reset_username: str = ""
    new_password: str = ""
    
    # User deletion
    delete_user_id: int = -1
    delete_username: str = ""

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
                total_cards = len(session.exec(
                    select(Flashcard).where(Flashcard.user_id == user.id)
                ).all())
                
                users_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at,
                    "total_cards": total_cards,
                    "reviews_today": stats.get("reviews_today", 0),
                    "reviews_total": stats.get("total_reviews", 0),
                    "streak": stats.get("current_streak", 0),
                    "is_admin": user.is_admin,
                    "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never",
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
    
    # Password Reset Methods
    def show_password_reset(self, user_id: int, username: str):
        """Show password reset dialog."""
        self.reset_user_id = user_id
        self.reset_username = username
        self.new_password = ""
        self.error_message = ""
        self.success_message = ""
    
    def cancel_password_reset(self):
        """Cancel password reset."""
        self.reset_user_id = -1
        self.reset_username = ""
        self.new_password = ""
    
    def reset_user_password(self):
        """Reset a user's password."""
        if not self.is_admin or self.reset_user_id == -1:
            return
        
        if len(self.new_password) < 6:
            self.error_message = "Password must be at least 6 characters"
            return
        
        from vocab_stack.services.auth_service import AuthService
        
        with get_session() as session:
            user = session.get(User, self.reset_user_id)
            if user:
                # Hash the new password
                user.password_hash = AuthService.hash_password(self.new_password)
                session.add(user)
                session.commit()
                
                self.success_message = f"Password reset for {self.reset_username}"
                self.reset_user_id = -1
                self.reset_username = ""
                self.new_password = ""
            else:
                self.error_message = "User not found"
    
    # User Deletion Methods
    def show_delete_user(self, user_id: int, username: str):
        """Show user deletion dialog."""
        self.delete_user_id = user_id
        self.delete_username = username
        self.error_message = ""
        self.success_message = ""
    
    def cancel_delete_user(self):
        """Cancel user deletion."""
        self.delete_user_id = -1
        self.delete_username = ""
    
    async def delete_user_confirmed(self):
        """Delete a user and all their data."""
        if not self.is_admin or self.delete_user_id == -1:
            return
        
        # Don't allow deleting yourself
        auth = await self.get_state(AuthState)
        if self.delete_user_id == auth.current_user_id:
            self.error_message = "You cannot delete your own account"
            return
        
        from vocab_stack.models import LeitnerState, ReviewHistory
        
        with get_session() as session:
            # Get all flashcards for this user
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.user_id == self.delete_user_id)
            ).all()
            
            # Delete related records
            for flashcard in flashcards:
                # Delete LeitnerState records
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == flashcard.id)
                ).all()
                for state in leitner_states:
                    session.delete(state)
                
                # Delete ReviewHistory records
                review_histories = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == flashcard.id)
                ).all()
                for history in review_histories:
                    session.delete(history)
                
                # Delete the flashcard
                session.delete(flashcard)
            
            # Delete the user
            user = session.get(User, self.delete_user_id)
            if user:
                session.delete(user)
                session.commit()
                
                self.success_message = f"User {self.delete_username} deleted successfully"
                self.delete_user_id = -1
                self.delete_username = ""
                self.load_user_stats()
            else:
                self.error_message = "User not found"
    
    # Admin Role Management
    async def toggle_admin(self, user_id: int):
        """Toggle admin status for a user."""
        if not self.is_admin:
            return
        
        # Don't allow removing your own admin status
        auth = await self.get_state(AuthState)
        if user_id == auth.current_user_id:
            self.error_message = "You cannot change your own admin status"
            return
        
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.is_admin = not user.is_admin
                session.add(user)
                session.commit()
                
                status = "granted" if user.is_admin else "revoked"
                self.success_message = f"Admin access {status} for {user.username}"
                self.load_user_stats()
            else:
                self.error_message = "User not found"


def user_card(user: dict) -> rx.Component:
    """Display a user's stats card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(user["username"], size="4"),
                rx.spacer(),
                rx.cond(
                    user["is_admin"],
                    rx.badge("Admin", color_scheme="red"),
                    rx.badge("User", color_scheme="blue"),
                ),
                width="100%",
            ),
            rx.text(f"Email: {user['email']}", color="gray", size="2"),
            rx.text(f"Last Login: {user['last_login']}", color="gray", size="1"),
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
            rx.divider(),
            rx.hstack(
                rx.button(
                    rx.cond(
                        user["is_admin"],
                        "Remove Admin",
                        "Make Admin"
                    ),
                    on_click=lambda: AdminState.toggle_admin(user["id"]),
                    size="2",
                    color_scheme="purple",
                    variant="soft",
                ),
                rx.button(
                    "Reset Password",
                    on_click=lambda: AdminState.show_password_reset(user["id"], user["username"]),
                    size="2",
                    color_scheme="orange",
                    variant="soft",
                ),
                rx.button(
                    "Delete User",
                    on_click=lambda: AdminState.show_delete_user(user["id"], user["username"]),
                    size="2",
                    color_scheme="red",
                    variant="soft",
                ),
                spacing="2",
                width="100%",
            ),
            align="start",
            spacing="3",
        ),
    )


def admin_dashboard_page() -> rx.Component:
    """Admin dashboard page."""
    return rx.vstack(
        rx.heading("Admin Dashboard", size="7"),
        
        # Success/Error messages
        rx.cond(
            AdminState.success_message != "",
            rx.callout(
                AdminState.success_message,
                icon="check",
                color_scheme="green",
            ),
        ),
        rx.cond(
            AdminState.error_message != "",
            rx.callout(
                AdminState.error_message,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
        
        # Password Reset Dialog
        rx.cond(
            AdminState.reset_user_id != -1,
            rx.card(
                rx.vstack(
                    rx.heading("Reset Password", size="5", color="orange"),
                    rx.text(
                        "Reset password for user: ",
                        rx.text(AdminState.reset_username, weight="bold", as_="span"),
                    ),
                    rx.vstack(
                        rx.text("New Password", size="2", weight="bold"),
                        rx.input(
                            value=AdminState.new_password,
                            on_change=AdminState.set_new_password,
                            type="password",
                            placeholder="Enter new password (min 6 characters)",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=AdminState.cancel_password_reset,
                            variant="soft",
                            size="3",
                        ),
                        rx.button(
                            "Reset Password",
                            on_click=AdminState.reset_user_password,
                            color_scheme="orange",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="4",
                    align="start",
                ),
            ),
        ),
        
        # Delete User Dialog
        rx.cond(
            AdminState.delete_user_id != -1,
            rx.card(
                rx.vstack(
                    rx.heading("Confirm Delete", size="5", color="red"),
                    rx.callout(
                        rx.vstack(
                            rx.text(
                                "Are you sure you want to delete user ",
                                rx.text(AdminState.delete_username, weight="bold", as_="span"),
                                "?",
                            ),
                            rx.text(
                                "This will permanently delete:",
                                weight="bold",
                                margin_top="0.5rem",
                            ),
                            rx.text("• All flashcards owned by this user"),
                            rx.text("• All review history for this user"),
                            rx.text("• All learning progress and Leitner states"),
                            rx.text("• The user account itself"),
                            rx.text(
                                "This action cannot be undone!",
                                weight="bold",
                                color="red",
                                margin_top="0.5rem",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        icon="info",
                        color_scheme="red",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=AdminState.cancel_delete_user,
                            variant="soft",
                            size="3",
                        ),
                        rx.button(
                            "Delete User",
                            on_click=AdminState.delete_user_confirmed,
                            color_scheme="red",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="4",
                    align="start",
                ),
            ),
        ),
        
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