# Authentication & Admin Panel - Investigation & Action Plan

## Investigation Summary

### What Exists (Already Implemented)
I found that you've already created authentication and admin functionality:

✅ **Files Created:**
- `vocab_stack/pages/auth.py` - Login and registration pages
- `vocab_stack/pages/admin.py` - Admin dashboard
- User model has `password_hash` field
- Auth routes registered in `app.py`
- Protected routes with `require_auth()` middleware

✅ **Features Implemented:**
- User registration with password hashing (bcrypt)
- Login functionality
- Session management (AuthState.is_logged_in, current_user)
- Protected routes (all main pages require login)
- Admin dashboard (only accessible to "admin" username)
- User statistics view for admins

### What Doesn't Work (The Problems)

Based on the code analysis, here are the likely issues:

#### ❌ Problem 1: Reflex State Persistence
**Issue**: `AuthState.is_logged_in` and `AuthState.current_user` are **not persistent** across page reloads.

**Why it fails:**
- Reflex State is in-memory only
- When you refresh the page, state is lost
- User appears logged out even though they just logged in

**Evidence in code:**
```python
class AuthState(rx.State):
    current_user: Optional[User] = None  # Lost on page reload!
    is_logged_in: bool = False           # Lost on page reload!
```

#### ❌ Problem 2: No Session Storage
**Issue**: No browser cookies or local storage to persist authentication.

**What's missing:**
- No `rx.cookie()` or `rx.local_storage()` usage
- No session tokens
- No "remember me" functionality

#### ❌ Problem 3: Password Hash Storage Issue
**Issue**: `password_hash` field might not exist in database yet.

**Why:**
- User model was originally created without `password_hash`
- Adding it to the model doesn't automatically add the column
- Need an Alembic migration to add `password_hash` to existing users

#### ❌ Problem 4: bcrypt Dependency
**Issue**: Code imports bcrypt but it might not be installed.

**Evidence:**
```python
import bcrypt  # Line 6 in auth.py
```

**Check if installed:**
```bash
pip list | grep bcrypt
```

#### ❌ Problem 5: Theme Loading Breaks on Auth
**Issue**: `get_user_theme()` tries to access `AuthState.current_user.id` at app initialization.

**Why it fails:**
- State not available during app creation
- Causes AttributeError when app starts
- Makes entire app crash

**Evidence:**
```python
# In app.py - BROKEN
if AuthState.is_logged_in and AuthState.current_user:
    settings = SettingsService.get_user_settings(AuthState.current_user.id)
```

#### ❌ Problem 6: Admin Check Logic
**Issue**: Admin panel checks username == "admin" but there's no guaranteed admin user.

**Why it fails:**
- No admin user created during setup
- No way to promote regular users to admin
- No `is_admin` field in User model

---

## Root Causes

### Core Issue: Reflex Doesn't Have Built-in Session Management
Reflex is a stateless framework by design. State is:
- ✅ Preserved during a single session
- ❌ Lost on page refresh
- ❌ Lost when closing browser
- ❌ Not shared across tabs

**This means traditional authentication won't work without custom implementation.**

---

## Action Plan

### Option A: Quick Fix (Partial Auth - Good for Development)

**Goal**: Get basic auth working for single-session use

**Steps:**

1. **Add missing database column**
   ```bash
   alembic revision --autogenerate -m "add password_hash to user"
   # Edit migration to add: batch_op.add_column(sa.Column('password_hash', sa.String(), nullable=False, server_default=''))
   alembic upgrade head
   ```

2. **Install bcrypt**
   ```bash
   pip install bcrypt
   # or
   uv pip install bcrypt
   ```

3. **Create default admin user**
   ```python
   # scripts/create_admin.py
   from vocab_stack.database import get_session
   from vocab_stack.models import User
   import bcrypt
   
   with get_session() as session:
       password = "admin123"  # Change this!
       hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
       
       admin = User(
           username="admin",
           email="admin@vocab.com",
           password_hash=hashed.decode('utf-8')
       )
       session.add(admin)
       session.commit()
       print("Admin user created")
   ```

4. **Fix theme loading to use default**
   ```python
   # In app.py - replace get_user_theme() call with:
   user_theme = "light"  # Simple default
   ```

5. **Add session persistence with cookies** (optional but recommended)
   ```python
   # In AuthState
   def login(self):
       # ... existing login code ...
       if user and bcrypt.checkpw(...):
           self.is_logged_in = True
           self.current_user = user
           # Store user ID in cookie
           return rx.set_cookie("user_id", str(user.id))
   
   def check_auth(self):
       """Check if user is logged in via cookie."""
       user_id = rx.get_cookie("user_id")
       if user_id:
           # Load user from database
           with get_session() as session:
               user = session.get(User, int(user_id))
               if user:
                   self.is_logged_in = True
                   self.current_user = user
   ```

**Limitations:**
- Auth only works within same session
- Refreshing page logs you out
- Not production-ready

---

### Option B: Proper Auth Implementation (Production-Ready)

**Goal**: Full authentication system with persistence

**Required Changes:**

#### 1. Add Session Token System

**Database Change:**
```python
# Add to User model
class User(rx.Model, table=True):
    # ... existing fields ...
    session_token: Optional[str] = None
    token_expires: Optional[datetime] = None
    is_admin: bool = Field(default=False)
```

**Migration:**
```bash
alembic revision --autogenerate -m "add session tokens and is_admin"
alembic upgrade head
```

#### 2. Create AuthService

```python
# vocab_stack/services/auth_service.py
import secrets
from datetime import datetime, timedelta
import bcrypt
from vocab_stack.database import get_session
from vocab_stack.models import User
from sqlmodel import select

class AuthService:
    @staticmethod
    def create_session_token(user_id: int) -> str:
        """Generate and store session token."""
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(days=30)
        
        with get_session() as session:
            user = session.get(User, user_id)
            user.session_token = token
            user.token_expires = expires
            session.add(user)
            session.commit()
        
        return token
    
    @staticmethod
    def validate_token(token: str) -> Optional[User]:
        """Check if token is valid and return user."""
        with get_session() as session:
            user = session.exec(
                select(User).where(User.session_token == token)
            ).first()
            
            if user and user.token_expires > datetime.utcnow():
                return user
        return None
    
    @staticmethod
    def logout(user_id: int):
        """Invalidate session token."""
        with get_session() as session:
            user = session.get(User, user_id)
            user.session_token = None
            user.token_expires = None
            session.add(user)
            session.commit()
```

#### 3. Update AuthState to Use Tokens

```python
class AuthState(rx.State):
    current_user_id: int = 0
    is_logged_in: bool = False
    
    def on_load(self):
        """Check authentication on every page load."""
        token = self.get_cookie("session_token")
        if token:
            user = AuthService.validate_token(token)
            if user:
                self.current_user_id = user.id
                self.is_logged_in = True
                return
        self.is_logged_in = False
        self.current_user_id = 0
    
    def login(self):
        # ... validate credentials ...
        if valid:
            token = AuthService.create_session_token(user.id)
            self.is_logged_in = True
            self.current_user_id = user.id
            return rx.set_cookie("session_token", token, max_age=2592000)
    
    def logout(self):
        AuthService.logout(self.current_user_id)
        self.is_logged_in = False
        self.current_user_id = 0
        return rx.remove_cookie("session_token")
```

#### 4. Add Auth Check to All Pages

```python
# In each page's State
def on_mount(self):
    # Check auth first
    AuthState.on_load()
    if not AuthState.is_logged_in:
        return rx.redirect("/")
    # Then load data...
    self.load_data()
```

#### 5. Update All Services to Use Current User

```python
# Instead of hardcoded user_id=1:
user_id = AuthState.current_user_id

# Example in DashboardState:
def load_dashboard_data(self):
    user_id = AuthState.current_user_id
    progress = LeitnerService.get_topic_progress(topic_id=t.id, user_id=user_id)
```

#### 6. Create Admin Management

```python
# vocab_stack/services/admin_service.py
class AdminService:
    @staticmethod
    def promote_to_admin(user_id: int):
        """Make user an admin."""
        with get_session() as session:
            user = session.get(User, user_id)
            user.is_admin = True
            session.add(user)
            session.commit()
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user is admin."""
        with get_session() as session:
            user = session.get(User, user_id)
            return user.is_admin if user else False
```

---

## Recommended Approach

### For Development/Testing: **Option A**
- Quick to implement
- Gets basic auth working
- Good enough for single-user testing
- **Time: ~1-2 hours**

### For Production/Multi-user: **Option B**
- Proper session management
- Persistent auth across reloads
- Secure and scalable
- **Time: ~4-6 hours**

---

## Immediate Steps (Option A)

### Step 1: Check Current State
```bash
# 1. Check if bcrypt is installed
pip list | grep bcrypt

# 2. Check if password_hash column exists
python -c "from vocab_stack.models import User; print(User.__table__.columns.keys())"

# 3. Try to run auth pages
reflex run
# Navigate to http://localhost:3000/ (should show login page)
```

### Step 2: Fix Database Schema
```bash
# If password_hash doesn't exist:
alembic revision -m "add password_hash to user"
```

Edit the migration file:
```python
def upgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(), nullable=False, server_default=''))
```

```bash
alembic upgrade head
```

### Step 3: Install Dependencies
```bash
pip install bcrypt
# or
uv pip install bcrypt
```

### Step 4: Create Admin User
```bash
python scripts/create_admin.py  # (create this script from template above)
```

### Step 5: Simplify Theme Loading
In `app.py`, replace the complex theme loading with:
```python
user_theme = "light"  # Simple default for now
```

### Step 6: Test Authentication
1. Start app: `reflex run`
2. Go to `http://localhost:3000/`
3. Try to register
4. Try to login
5. Navigate to protected pages

---

## Testing Checklist

### Auth Basics
- [ ] Can register new user
- [ ] Can login with correct credentials
- [ ] Login fails with wrong password
- [ ] Can access dashboard after login
- [ ] Redirected to login if not authenticated

### Admin Panel
- [ ] Can login as admin
- [ ] Can access `/admin` route
- [ ] See list of all users
- [ ] See user statistics
- [ ] Regular users can't access admin

### Session Persistence (Option B only)
- [ ] Stay logged in after page refresh
- [ ] Stay logged in after closing browser
- [ ] Can logout successfully
- [ ] Token expires after 30 days

---

## Known Issues to Fix

### Issue 1: AuthState.current_user is User object
**Problem**: Can't serialize User object in State

**Fix**: Store only user_id instead:
```python
class AuthState(rx.State):
    current_user_id: int = 0  # Instead of current_user: User
    
    @rx.var
    def current_user(self) -> Optional[dict]:
        """Get current user data."""
        if self.current_user_id:
            with get_session() as session:
                user = session.get(User, self.current_user_id)
                return {"id": user.id, "username": user.username}
        return None
```

### Issue 2: Hardcoded user_id=1 everywhere
**Problem**: All services use user_id=1

**Fix**: Create a centralized auth context:
```python
# vocab_stack/utils/auth_context.py
from vocab_stack.pages.auth import AuthState

def get_current_user_id() -> int:
    """Get ID of currently logged in user."""
    return AuthState.current_user_id if AuthState.is_logged_in else 1
```

Then replace all `user_id=1` with `get_current_user_id()`.

---

## Summary

### What You Have:
✅ Auth pages created  
✅ Basic login/register logic  
✅ Protected routes setup  
✅ Admin dashboard structure  

### What's Broken:
❌ State not persistent (logs out on refresh)  
❌ Missing database columns (password_hash)  
❌ Missing dependencies (bcrypt)  
❌ No session management  
❌ Theme loading crashes app  
❌ No admin user exists  

### Quick Fix (1-2 hours):
1. Add password_hash column via migration
2. Install bcrypt
3. Create admin user script
4. Fix theme loading
5. Test basic auth flow

### Proper Fix (4-6 hours):
1. Add session token system
2. Create AuthService
3. Implement cookie-based auth
4. Update all pages to check auth
5. Replace hardcoded user_id=1
6. Add is_admin field and management

---

## SELECTED: Option B Implementation Plan

### Phase 1: Database Schema Updates

#### Step 1.1: Add Missing Fields to User Model
```python
# In vocab_stack/models.py
class User(rx.Model, table=True):
    # ... existing fields ...
    session_token: Optional[str] = None
    token_expires: Optional[datetime] = None
    is_admin: bool = Field(default=False)
    last_login: Optional[datetime] = None
```

#### Step 1.2: Ensure password_hash Exists
Check current schema and add if missing.

#### Step 1.3: Create Migration
```bash
alembic revision --autogenerate -m "add auth session management fields"
# Edit migration to add:
# - session_token (String, nullable)
# - token_expires (DateTime, nullable)
# - is_admin (Boolean, default=False)
# - last_login (DateTime, nullable)
# - password_hash (String, if missing, server_default='')
alembic upgrade head
```

### Phase 2: Create AuthService

#### Step 2.1: Create auth_service.py
```python
# vocab_stack/services/auth_service.py
import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from vocab_stack.database import get_session
from vocab_stack.models import User
from sqlmodel import select

class AuthService:
    TOKEN_EXPIRY_DAYS = 30
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create_session_token(user_id: int) -> str:
        """Generate and store session token."""
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(days=AuthService.TOKEN_EXPIRY_DAYS)
        
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.session_token = token
                user.token_expires = expires
                user.last_login = datetime.utcnow()
                session.add(user)
                session.commit()
        
        return token
    
    @staticmethod
    def validate_token(token: str) -> Optional[int]:
        """Validate token and return user_id if valid."""
        if not token:
            return None
            
        with get_session() as session:
            user = session.exec(
                select(User).where(User.session_token == token)
            ).first()
            
            if user and user.token_expires and user.token_expires > datetime.utcnow():
                return user.id
        return None
    
    @staticmethod
    def logout(user_id: int):
        """Invalidate session token."""
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.session_token = None
                user.token_expires = None
                session.add(user)
                session.commit()
    
    @staticmethod
    def get_user(user_id: int) -> Optional[dict]:
        """Get user data as dict (safe for State)."""
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                }
        return None
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user is admin."""
        with get_session() as session:
            user = session.get(User, user_id)
            return user.is_admin if user else False
```

### Phase 3: Update AuthState with Cookie Persistence

#### Step 3.1: Refactor AuthState
```python
# In vocab_stack/pages/auth.py
class AuthState(rx.State):
    """Authentication state with cookie-based persistence."""
    
    # Store only user_id, not full User object (State serialization issue)
    current_user_id: int = 0
    is_logged_in: bool = False
    
    # Form fields
    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    
    # Messages
    error_message: str = ""
    success_message: str = ""
    
    def on_load(self):
        """Check authentication on every page load via cookie."""
        token = self.router.session.client_token  # Get from Reflex cookie
        if token:
            user_id = AuthService.validate_token(token)
            if user_id:
                self.current_user_id = user_id
                self.is_logged_in = True
                return
        
        # Not authenticated
        self.is_logged_in = False
        self.current_user_id = 0
    
    @rx.var
    def current_user(self) -> dict:
        """Get current user data (computed property)."""
        if self.current_user_id:
            return AuthService.get_user(self.current_user_id) or {}
        return {}
    
    @rx.var
    def is_admin(self) -> bool:
        """Check if current user is admin."""
        return AuthService.is_admin(self.current_user_id)
    
    def register(self):
        """Register a new user."""
        # Validation
        if not self.username or not self.email or not self.password:
            self.error_message = "All fields are required"
            return
        
        if self.password != self.confirm_password:
            self.error_message = "Passwords do not match"
            return
        
        if len(self.password) < 6:
            self.error_message = "Password must be at least 6 characters"
            return
        
        # Check duplicates
        with get_session() as session:
            if session.exec(select(User).where(User.username == self.username)).first():
                self.error_message = "Username already taken"
                return
            
            if session.exec(select(User).where(User.email == self.email)).first():
                self.error_message = "Email already in use"
                return
            
            # Create user
            user = User(
                username=self.username,
                email=self.email,
                password_hash=AuthService.hash_password(self.password)
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            self.success_message = "Registration successful! Please login."
            self.error_message = ""
            # Clear form
            self.username = ""
            self.email = ""
            self.password = ""
            self.confirm_password = ""
    
    def login(self):
        """Login user and create session."""
        if not self.username or not self.password:
            self.error_message = "Username and password required"
            return
        
        with get_session() as session:
            user = session.exec(
                select(User).where(User.username == self.username)
            ).first()
            
            if not user or not AuthService.verify_password(self.password, user.password_hash):
                self.error_message = "Invalid username or password"
                return
            
            # Create session
            token = AuthService.create_session_token(user.id)
            self.current_user_id = user.id
            self.is_logged_in = True
            self.error_message = ""
            
            # Set cookie and redirect
            return [
                rx.set_value("session_token", token),  # Reflex cookie
                rx.redirect("/dashboard")
            ]
    
    def logout(self):
        """Logout user and clear session."""
        AuthService.logout(self.current_user_id)
        self.is_logged_in = False
        self.current_user_id = 0
        
        return [
            rx.remove_cookie("session_token"),
            rx.redirect("/")
        ]
```

### Phase 4: Update All Pages to Use Current User

#### Step 4.1: Create Auth Context Utility
```python
# vocab_stack/utils/auth_context.py
"""Centralized auth context."""
from vocab_stack.pages.auth import AuthState

def get_current_user_id() -> int:
    """Get ID of currently logged in user."""
    return AuthState.current_user_id if AuthState.is_logged_in else 0

def require_login() -> bool:
    """Check if user is logged in."""
    return AuthState.is_logged_in
```

#### Step 4.2: Update Each Page State
Replace all `user_id=1` with `get_current_user_id()`:

- DashboardState.load_dashboard_data()
- ReviewState.load_user_preferences()
- CardState.create_card()
- TopicsState (if using user filtering)
- StatisticsState.load_statistics()
- SettingsState.load_settings()

#### Step 4.3: Add Auth Check to on_mount
```python
# Pattern for each page State:
def on_mount(self):
    # Check auth
    AuthState.on_load()
    if not AuthState.is_logged_in:
        return rx.redirect("/")
    
    # Load data with current user
    self.load_data()
```

### Phase 5: Update Navigation

#### Step 5.1: Add Logout Button to Navbar
```python
# In vocab_stack/components/navigation.py
def navbar():
    return rx.hstack(
        # ... existing nav buttons ...
        rx.spacer(),
        rx.hstack(
            rx.text(f"👤 {AuthState.current_user.get('username', 'User')}", size="2"),
            rx.cond(
                AuthState.is_admin,
                rx.link(rx.button("Admin", variant="soft", size="2"), href="/admin"),
            ),
            rx.button("Logout", on_click=AuthState.logout, variant="soft", size="2"),
            spacing="2",
        ),
    )
```

### Phase 6: Admin Panel Updates

#### Step 6.1: Update AdminState
```python
# In vocab_stack/pages/admin.py
class AdminState(rx.State):
    # ... existing fields ...
    
    def on_mount(self):
        # Check auth
        AuthState.on_load()
        if not AuthState.is_logged_in:
            return rx.redirect("/")
        
        if not AuthState.is_admin:
            return rx.redirect("/dashboard")
        
        self.load_user_stats()
    
    def promote_user(self, user_id: int):
        """Promote user to admin."""
        if not AuthState.is_admin:
            return
        
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.is_admin = True
                session.add(user)
                session.commit()
        
        self.load_user_stats()
```

### Phase 7: Create Admin User Script

#### Step 7.1: Create scripts/create_admin.py
```python
"""Create admin user."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from vocab_stack.database import get_session
from vocab_stack.models import User
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select

def create_admin():
    username = input("Enter admin username [admin]: ") or "admin"
    email = input("Enter admin email [admin@vocab.com]: ") or "admin@vocab.com"
    password = input("Enter admin password: ")
    
    if not password:
        print("❌ Password required")
        return
    
    with get_session() as session:
        # Check if exists
        existing = session.exec(
            select(User).where(User.username == username)
        ).first()
        
        if existing:
            print(f"⚠️  User '{username}' already exists. Promoting to admin...")
            existing.is_admin = True
            session.add(existing)
            session.commit()
            print(f"✅ '{username}' is now an admin")
        else:
            admin = User(
                username=username,
                email=email,
                password_hash=AuthService.hash_password(password),
                is_admin=True
            )
            session.add(admin)
            session.commit()
            print(f"✅ Admin user '{username}' created successfully")

if __name__ == "__main__":
    create_admin()
```

### Phase 8: Testing & Verification

#### Test Checklist
- [ ] Register new user
- [ ] Login with credentials
- [ ] Stay logged in on page refresh
- [ ] Access protected pages
- [ ] Logout successfully
- [ ] Can't access pages after logout
- [ ] Admin can access /admin
- [ ] Regular user can't access /admin
- [ ] User data isolated (see only own cards)
- [ ] Session expires after 30 days

### Phase 9: Documentation Updates

Update all relevant docs to reflect auth changes:
- README.md (add login instructions)
- Phase completion docs
- API integration guide

---

## Implementation Order

1. ✅ Update database schema (migrations)
2. ✅ Create AuthService
3. ✅ Install bcrypt dependency
4. ✅ Update AuthState with cookies
5. ✅ Create auth context utility
6. ✅ Update all page states (replace user_id=1)
7. ✅ Update navigation (add logout)
8. ✅ Update admin panel
9. ✅ Create admin user script
10. ✅ Test thoroughly
11. ✅ Update documentation

---

**Status: Ready to implement Option B**
**Estimated Time: 4-6 hours**
**Starting implementation...**
