"""Authentication pages: login, register, logout."""

import reflex as rx


class AuthState(rx.State):
    """Authentication state for managing user login/registration."""

    # Form fields
    username_input: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""

    # Error messages
    error_message: str = ""
    success_message: str = ""

    # Current user info (store only ID, not entire User object)
    current_user_id: int = 0
    username: str = ""
    is_logged_in: bool = False
    is_admin: bool = False

    # Session token stored as cookie
    session_token: str = rx.Cookie(name="session_token", max_age=2592000)  # 30 days

    def on_load(self):
        """Check authentication on every page load."""
        from vocab_stack.services.auth_service import AuthService

        if self.session_token:
            user = AuthService.validate_token(self.session_token)
            if user:
                self.current_user_id = user.id
                self.username = user.username
                self.is_admin = user.is_admin
                self.is_logged_in = True
                return

        # Not logged in
        self.is_logged_in = False
        self.current_user_id = 0
        self.username = ""
        self.is_admin = False

    def register(self) -> rx.event:
        """Register a new user."""
        from vocab_stack.services.auth_service import AuthService

        # Clear previous messages
        self.error_message = ""
        self.success_message = ""

        # Validate confirm password
        if self.password != self.confirm_password:
            self.error_message = "Passwords do not match."
            return []

        # Use AuthService to register
        success, message, user = AuthService.register_user(
            self.username_input, self.email, self.password
        )

        if success and user:
            # Auto-login after registration
            token = AuthService.create_session_token(user.id)
            self.session_token = token
            self.current_user_id = user.id
            self.username = user.username
            self.is_admin = user.is_admin
            self.is_logged_in = True
            self.error_message = ""

            # Clear form fields
            self.username_input = ""
            self.email = ""
            self.password = ""
            self.confirm_password = ""

            return rx.redirect("/dashboard")
        else:
            self.error_message = message
            return []

    def login(self) -> rx.event:
        """Log in an existing user."""
        from vocab_stack.services.auth_service import AuthService

        # Clear previous messages
        self.error_message = ""
        self.success_message = ""

        # Use AuthService to authenticate
        success, message, user = AuthService.login_user(
            self.username_input, self.password
        )

        if success and user:
            token = AuthService.create_session_token(user.id)
            self.session_token = token
            self.current_user_id = user.id
            self.username = user.username
            self.is_admin = user.is_admin
            self.is_logged_in = True
            self.error_message = ""

            # Clear form fields
            self.username_input = ""
            self.password = ""

            return rx.redirect("/dashboard")
        else:
            self.error_message = message
            return []

    def logout(self) -> rx.event:
        """Log out the current user."""
        from vocab_stack.services.auth_service import AuthService

        if self.current_user_id:
            AuthService.logout(self.current_user_id)

        self.is_logged_in = False
        self.current_user_id = 0
        self.username = ""
        self.is_admin = False
        self.session_token = ""  # Clear the cookie

        return rx.redirect("/")


def login_page():
    """Login page component."""
    return rx.vstack(
        rx.heading("Login", size="9", mb=6),
        rx.text(
            "Don't have an account? ",
            rx.link("Sign up here", href="/register", color="blue.500"),
            mb=4,
        ),
        rx.cond(
            AuthState.error_message != "",
            rx.callout(
                AuthState.error_message, icon="triangle_alert", color_scheme="red", mb=4
            ),
        ),
        rx.cond(
            AuthState.success_message != "",
            rx.callout(
                AuthState.success_message, icon="check", color_scheme="green", mb=4
            ),
        ),
        rx.form(
            rx.vstack(
                rx.input(
                    placeholder="Username",
                    value=AuthState.username_input,
                    on_change=AuthState.set_username_input,
                    mb=4,
                ),
                rx.input(
                    type="password",
                    placeholder="Password",
                    value=AuthState.password,
                    on_change=AuthState.set_password,
                    mb=4,
                ),
                rx.button(
                    "Login", type="submit", width="100%", color_scheme="blue"
                ),
                width="100%",
            ),
            on_submit=AuthState.login,
        ),
        width="100%",
        max_width="400px",
        align_items="center",
        spacing="4",
        padding="4",
    )


def register_page():
    """Registration page component."""
    return rx.vstack(
        rx.heading("Create Account", size="9", mb=6),
        rx.text(
            "Already have an account? ",
            rx.link("Log in here", href="/", color="blue.500"),
            mb=4,
        ),
        rx.cond(
            AuthState.error_message != "",
            rx.callout(
                AuthState.error_message, icon="triangle_alert", color_scheme="red", mb=4
            ),
        ),
        rx.cond(
            AuthState.success_message != "",
            rx.callout(
                AuthState.success_message, icon="check", color_scheme="green", mb=4
            ),
        ),
        rx.form(
            rx.vstack(
                rx.input(
                    placeholder="Username",
                    value=AuthState.username_input,
                    on_change=AuthState.set_username_input,
                    mb=4,
                ),
                rx.input(
                    type="email",
                    placeholder="Email",
                    value=AuthState.email,
                    on_change=AuthState.set_email,
                    mb=4,
                ),
                rx.input(
                    type="password",
                    placeholder="Password",
                    value=AuthState.password,
                    on_change=AuthState.set_password,
                    mb=4,
                ),
                rx.input(
                    type="password",
                    placeholder="Confirm Password",
                    value=AuthState.confirm_password,
                    on_change=AuthState.set_confirm_password,
                    mb=4,
                ),
                rx.button(
                    "Register",
                    type="submit",
                    width="100%",
                    color_scheme="blue",
                ),
                width="100%",
            ),
            on_submit=AuthState.register,
        ),
        width="100%",
        max_width="400px",
        align_items="center",
        spacing="4",
        padding="4",
    )
