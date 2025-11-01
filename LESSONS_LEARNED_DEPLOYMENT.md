# Lessons Learned: Deploying Reflex Apps to Production

## 🎓 What We Learned Deploying to Render.com

This document captures all the hard-won lessons from deploying a Reflex + SQLModel app to production on free hosting.

---

## 📋 Table of Contents

1. [The Free Hosting Landscape](#the-free-hosting-landscape)
2. [Critical Issues We Hit](#critical-issues-we-hit)
3. [The Working Solution](#the-working-solution)
4. [Deployment Checklist](#deployment-checklist)
5. [Common Pitfalls](#common-pitfalls)
6. [Configuration Files Explained](#configuration-files-explained)
7. [Debugging Tips](#debugging-tips)
8. [Next Time Checklist](#next-time-checklist)

---

## 🌍 The Free Hosting Landscape

### What We Tried:

1. **Koyeb Free Tier** ❌
   - **Problem:** No persistent volumes on free tier
   - **Lesson:** SQLite needs persistent storage
   - **Verdict:** Can't use SQLite on free tier

2. **Render Free Tier + SQLite** ❌
   - **Problem:** No persistent disks on free tier
   - **Lesson:** Same as Koyeb - file-based databases need persistent storage
   - **Verdict:** Can't use SQLite on free tier

3. **Render Free Tier + PostgreSQL (Supabase)** ✅
   - **Solution:** External PostgreSQL database with connection pooler
   - **Lesson:** Cloud databases work on free tiers without persistent volumes
   - **Verdict:** This works!

### Key Insight:
**Free tier hosting platforms no longer support persistent volumes/disks. Use cloud databases instead.**

---

## 🔥 Critical Issues We Hit

### Issue 1: Database Choice - SQLite vs PostgreSQL

**Problem:**
- Started with SQLite (simple, file-based)
- Free hosting tiers don't provide persistent storage
- Database would be wiped on every deployment

**Solution:**
- Converted to PostgreSQL
- Used Supabase free tier (500MB database)
- Cloud-hosted database persists regardless of app restarts

**Code Changes Required:**
```python
# Before (SQLite):
DATABASE_URL = "sqlite:///vocab_stack.db"

# After (PostgreSQL):
DATABASE_URL = "postgresql://user:pass@host:5432/dbname"

# DateTime fixes for PostgreSQL compatibility:
# Changed from:
created_at: datetime = Field(default_factory=datetime.utcnow)
# To:
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Dependencies Added:**
```toml
dependencies = [
    "psycopg2-binary>=2.9.9",  # PostgreSQL driver
    # ... other deps
]
```

### Issue 2: Special Characters in Database Passwords

**Problem:**
```
DATABASE_URL = postgresql://postgres:H@lfpikant1@db.supabase.co:5432/postgres
                                       ↑ This @ breaks the URL parsing!
```

**Solution:**
URL-encode special characters:
```
@ becomes %40
: becomes %3A
/ becomes %2F
```

**Correct URL:**
```
postgresql://postgres:H%40lfpikant1@db.supabase.co:5432/postgres
```

**Python helper to encode:**
```python
from urllib.parse import quote
password = "H@lfpikant1"
encoded = quote(password, safe='')
print(encoded)  # H%40lfpikant1
```

### Issue 3: IPv6 vs IPv4 Network Issues

**Problem:**
```
psycopg2.OperationalError: connection to server at "db.xxx.supabase.co" 
(2a05:d016:571:a423:...) failed: Network is unreachable
```

Render's free tier doesn't support IPv6.

**Solution:**
Use Supabase's **Connection Pooler** instead of direct connection:

```
# Before (Direct - uses IPv6):
postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres

# After (Pooler - uses IPv4):
postgresql://postgres:pass@aws-0-region.pooler.supabase.com:6543/postgres
```

**Key Differences:**
- Direct connection: Port **5432**, IPv6
- Session pooler: Port **6543**, IPv4
- Use **Session Mode** pooler (not Transaction Mode)

### Issue 4: Alembic Using Wrong Database

**Problem:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
```

Alembic was using SQLite while the app used PostgreSQL!

**Root Cause:**
`alembic.ini` had hardcoded SQLite URL:
```ini
sqlalchemy.url = sqlite:///reflex.db
```

**Solution:**
Update `alembic/env.py` to read from environment variable:

```python
import os
from alembic import context

config = context.config

# Override with DATABASE_URL if set
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
```

**Lesson:** Migration tools need explicit configuration to use environment variables.

### Issue 5: Port Binding - Frontend vs Backend

**Problem:**
```
App running at: http://0.0.0.0:3000/
Backend running at: http://0.0.0.0:10000
```

Reflex ran frontend on port 3000, backend on 10000. Render only forwarded to one port (10000), so frontend wasn't accessible.

**Solution:**
Use `--single-port` flag:
```bash
reflex run --env prod --single-port
```

This runs both frontend and backend on the same port (from `PORT` env var).

**Configuration in rxconfig.py:**
```python
import os

config = rx.Config(
    app_name="vocab_stack",
    backend_host="0.0.0.0",  # Bind to all interfaces
    backend_port=int(os.getenv("PORT", "8000")),
    api_url="https://your-app.onrender.com",  # Production URL
    deploy_url="https://your-app.onrender.com",
)
```

### Issue 6: Build vs Run Separation

**Problem:**
Initially tried to export frontend during build and serve it separately.

**What Didn't Work:**
```yaml
buildCommand: "reflex export --frontend-only"
startCommand: "reflex run --backend-only"
```

**What Works:**
```yaml
buildCommand: "reflex init"
startCommand: "reflex run --env prod --single-port"
```

**Lesson:** Let Reflex handle both frontend and backend in production mode with `--single-port`.

---

## ✅ The Working Solution

### Final Architecture:

```
┌─────────────────────────────────────────────┐
│  RENDER.COM (Free Tier)                     │
│                                              │
│  Reflex App (Single Port)                   │
│  • Frontend: React/Next.js                  │
│  • Backend: FastAPI                         │
│  • Port: 10000 (from PORT env var)         │
│  • Spins down after 15 min inactivity      │
│                                              │
│  ↓ PostgreSQL Connection (IPv4 pooler)     │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│  SUPABASE (Free Tier)                       │
│                                              │
│  PostgreSQL Database                        │
│  • 500MB storage                            │
│  • Session Mode Pooler                      │
│  • Always available                         │
│  • Automatic backups                        │
└─────────────────────────────────────────────┘
```

### Final Files:

**render.yaml:**
```yaml
services:
  - type: web
    name: vocab-stack
    runtime: python
    plan: free
    branch: main
    buildCommand: "pip install uv && uv sync --frozen && uv run reflex init"
    startCommand: "uv run alembic upgrade head && uv run python scripts/create_admin.py || true && uv run reflex run --env prod --single-port --loglevel info"
    
    envVars:
      - key: DATABASE_URL
        sync: false  # Set in dashboard with Supabase URL
      - key: PYTHON_VERSION
        value: "3.11"
      - key: ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_ORIGINS
        sync: false  # Set to your Render URL
    
    healthCheckPath: /
    autoDeploy: true
```

**rxconfig.py:**
```python
import reflex as rx
import os

config = rx.Config(
    app_name="vocab_stack",
    db_url=os.getenv("DATABASE_URL"),
    backend_host="0.0.0.0",
    backend_port=int(os.getenv("PORT", "8000")),
    api_url=f"https://vocab-stack.onrender.com",
    deploy_url=f"https://vocab-stack.onrender.com",
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)
```

**alembic/env.py (critical addition):**
```python
import os

config = context.config

# Override with environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
```

**pyproject.toml (PostgreSQL driver):**
```toml
dependencies = [
    "psycopg2-binary>=2.9.9",  # Critical for PostgreSQL
    # ... other deps
]
```

---

## 📋 Deployment Checklist

### Pre-Deployment:

- [ ] **Choose Database**
  - ❌ SQLite on free hosting (needs persistent disk)
  - ✅ PostgreSQL on Supabase (free, cloud-hosted)

- [ ] **Update Code for PostgreSQL**
  - [ ] Add `psycopg2-binary` to dependencies
  - [ ] Fix datetime fields: `datetime.now(timezone.utc)` not `datetime.utcnow()`
  - [ ] Update `DATABASE_URL` to use environment variable

- [ ] **Configure Alembic**
  - [ ] Update `alembic/env.py` to read `DATABASE_URL` from environment
  - [ ] Test migrations locally with PostgreSQL

- [ ] **Configure Reflex**
  - [ ] Set `backend_host="0.0.0.0"`
  - [ ] Use `PORT` environment variable for port
  - [ ] Set `api_url` and `deploy_url` to production URL

- [ ] **Handle Special Characters**
  - [ ] URL-encode passwords with special characters (@, :, /, etc.)

### Supabase Setup:

- [ ] **Create Supabase Project**
  - [ ] Sign up at supabase.com
  - [ ] Create new project
  - [ ] Choose region close to your users
  - [ ] Set strong database password

- [ ] **Get Connection String**
  - [ ] Go to Settings → Database → Connection String
  - [ ] Select **"Session Mode"** pooler tab (NOT Direct connection)
  - [ ] Copy URI format connection string
  - [ ] URL-encode password if it has special characters
  - [ ] Example: `postgresql://postgres.xxx:PASS%40WORD@aws-0-region.pooler.supabase.com:6543/postgres`

### Render Setup:

- [ ] **Create Render Service**
  - [ ] Sign up at render.com with GitHub
  - [ ] Create new Web Service
  - [ ] Connect your repository
  - [ ] Select branch (usually `main`)

- [ ] **Configure Build**
  - [ ] Runtime: Python 3
  - [ ] Build Command: `pip install uv && uv sync --frozen && uv run reflex init`
  - [ ] Start Command: `uv run alembic upgrade head && uv run python scripts/create_admin.py || true && uv run reflex run --env prod --single-port --loglevel info`

- [ ] **Set Environment Variables**
  - [ ] `DATABASE_URL` → Supabase connection string (with pooler!)
  - [ ] `PYTHON_VERSION` → `3.11`
  - [ ] `ENV` → `production`
  - [ ] `SECRET_KEY` → Auto-generate or set manually
  - [ ] `ALLOWED_ORIGINS` → Will set after first deploy

- [ ] **Deploy**
  - [ ] Click "Create Web Service"
  - [ ] Wait 5-10 minutes for build
  - [ ] Check logs for errors

### Post-Deployment:

- [ ] **Update ALLOWED_ORIGINS**
  - [ ] Copy your Render URL (e.g., `https://your-app.onrender.com`)
  - [ ] Go to Environment tab in Render
  - [ ] Set `ALLOWED_ORIGINS` to your URL
  - [ ] Save (triggers redeploy)

- [ ] **Test Application**
  - [ ] Visit your Render URL
  - [ ] Sign up for account
  - [ ] Login/logout
  - [ ] Test all features
  - [ ] Check WebSocket connections work

- [ ] **Login as Admin**
  - [ ] Username: `admin`
  - [ ] Password: `admin123`
  - [ ] **Change password immediately!**

- [ ] **Monitor**
  - [ ] Check Render logs for errors
  - [ ] Check Supabase database for data
  - [ ] Test after 15 min (cold start behavior)

---

## 🚨 Common Pitfalls

### 1. Database Connection String Format

**Wrong:**
```
postgresql://user:pass@word@host:5432/db  # @ in password breaks it!
```

**Right:**
```
postgresql://user:pass%40word@host:5432/db  # URL-encoded
```

### 2. Using Direct Connection Instead of Pooler

**Wrong:**
```
postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres  # IPv6, won't work
```

**Right:**
```
postgresql://postgres:pass@aws-0-region.pooler.supabase.com:6543/postgres  # IPv4 pooler
```

### 3. Forgetting to Update Alembic

**Problem:**
Alembic still uses SQLite while app uses PostgreSQL.

**Solution:**
Always update `alembic/env.py` to read `DATABASE_URL` from environment.

### 4. Wrong Reflex Run Mode

**Wrong:**
```bash
reflex run --env prod  # Starts frontend on 3000, backend on 10000
```

**Right:**
```bash
reflex run --env prod --single-port  # Both on PORT env var
```

### 5. Missing Production URLs

**Problem:**
Not setting `api_url` and `deploy_url` in `rxconfig.py`.

**Solution:**
```python
config = rx.Config(
    api_url="https://your-app.onrender.com",
    deploy_url="https://your-app.onrender.com",
)
```

### 6. Not URL-Encoding Credentials

**Problem:**
Special characters in passwords/usernames break URL parsing.

**Solution:**
Always URL-encode:
```python
from urllib.parse import quote
encoded_password = quote("P@ss:word/123", safe='')
```

---

## 📄 Configuration Files Explained

### render.yaml

**Purpose:** Defines how Render builds and runs your app.

**Key Sections:**

```yaml
# Build phase - runs once per deploy
buildCommand: "pip install uv && uv sync --frozen && uv run reflex init"

# Run phase - runs on every start
startCommand: "uv run alembic upgrade head && uv run reflex run --env prod --single-port"

# Environment variables
envVars:
  - key: DATABASE_URL
    sync: false  # Set manually in dashboard
```

**Why `sync: false`?**
- Means "don't auto-sync from repo"
- We set it manually in Render dashboard
- Keeps secrets out of version control

### rxconfig.py

**Purpose:** Configures Reflex app behavior.

**Critical Settings:**

```python
backend_host="0.0.0.0"  # Required for Docker/cloud hosting
backend_port=int(os.getenv("PORT", "8000"))  # Use cloud platform's PORT
api_url="https://your-app.onrender.com"  # Production API URL
deploy_url="https://your-app.onrender.com"  # Where app is deployed
```

**Why these matter:**
- `backend_host="0.0.0.0"` → Allows external connections
- `PORT` env var → Cloud platforms assign dynamic ports
- `api_url/deploy_url` → Tells frontend where backend is

### alembic/env.py

**Purpose:** Configures database migrations.

**Critical Addition:**

```python
import os

database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
```

**Why needed:**
- `alembic.ini` has hardcoded SQLite URL
- Environment variable overrides it
- Ensures migrations run on correct database

### pyproject.toml

**Purpose:** Defines Python dependencies.

**PostgreSQL Requirement:**

```toml
dependencies = [
    "psycopg2-binary>=2.9.9",  # PostgreSQL adapter
    # ... other deps
]
```

**Why psycopg2-binary:**
- `psycopg2-binary` → Includes pre-compiled binaries
- `psycopg2` → Requires compilation (harder on cloud platforms)
- Always use `-binary` for deployment

---

## 🔍 Debugging Tips

### Check Which Database Alembic is Using

**Look for this in logs:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.  # BAD - using SQLite
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.  # GOOD - using PostgreSQL
```

### Test Database Connection Locally

```bash
# Set environment variable
export DATABASE_URL="postgresql://user:pass@host:6543/db"

# Test connection
python3 -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); conn = engine.connect(); print('Connected!'); conn.close()"
```

### Verify Environment Variables on Render

In Render dashboard:
1. Go to your service
2. Click "Environment" tab
3. Verify all variables are set correctly
4. Check for typos in DATABASE_URL

### Check Logs for Port Issues

**Look for:**
```
App running at: http://0.0.0.0:3000/  # BAD - wrong port
Backend running at: http://0.0.0.0:10000/

App running at: http://0.0.0.0:10000/  # GOOD - single port
Backend running at: http://0.0.0.0:10000/
```

### Test Connection Pooler

```bash
# Test if pooler is reachable
psql "postgresql://user:pass@aws-0-region.pooler.supabase.com:6543/postgres"
```

---

## ✅ Next Time Checklist

When deploying a new Reflex app:

### 1. **Database Decision (First Thing!)**

- [ ] Don't use SQLite for production
- [ ] Set up PostgreSQL on Supabase immediately
- [ ] Get Session Mode pooler connection string
- [ ] URL-encode password

### 2. **Code Preparation**

- [ ] Add `psycopg2-binary` to dependencies
- [ ] Use `datetime.now(timezone.utc)` not `datetime.utcnow()`
- [ ] Update `alembic/env.py` to read `DATABASE_URL` from environment
- [ ] Configure `rxconfig.py` with:
  - `backend_host="0.0.0.0"`
  - `backend_port=int(os.getenv("PORT", "8000"))`
  - `api_url` and `deploy_url` set to production domain

### 3. **Render Configuration**

- [ ] Create `render.yaml` with:
  - Build command: `pip install uv && uv sync --frozen && uv run reflex init`
  - Start command: `uv run alembic upgrade head && uv run reflex run --env prod --single-port`
- [ ] Set environment variables:
  - `DATABASE_URL` (Supabase pooler URL)
  - `ENV=production`
  - `SECRET_KEY` (auto-generate)
  - `PYTHON_VERSION=3.11`

### 4. **Deployment**

- [ ] Push to GitHub
- [ ] Create Render service from repo
- [ ] Wait for build
- [ ] Update `ALLOWED_ORIGINS` after first deploy
- [ ] Test thoroughly

### 5. **Verification**

- [ ] Check logs show `PostgresqlImpl` not `SQLiteImpl`
- [ ] Check logs show single port (not 3000 + 10000)
- [ ] Test signup/login
- [ ] Test WebSocket connections
- [ ] Verify data persists after redeploy

---

## 📊 Free Tier Comparison

| Platform | Persistent Storage | SQLite Support | PostgreSQL | Cold Starts | Complexity |
|----------|-------------------|----------------|------------|-------------|------------|
| **Render Free** | ❌ No | ❌ No | ✅ Yes (external) | ✅ 15 min | 😊 Easy |
| **Koyeb Free** | ❌ No | ❌ No | ✅ Yes (external) | ❌ None | 😊 Easy |
| **Fly.io Free** | ✅ 3GB | ✅ Yes | ✅ Yes | ❌ None | 😐 Medium |
| **Railway** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ None | 😊 Easy |
| **Supabase Free** | N/A (DB only) | ❌ No | ✅ 500MB | N/A | 😊 Easy |

**Our Choice:**
- **Render** (app hosting) + **Supabase** (database)
- Total cost: $0/month
- Trade-off: Cold starts after 15 min inactivity

---

## 🎓 Key Lessons Summary

1. **Free hosting no longer supports persistent volumes** → Use cloud databases
2. **SQLite needs persistent storage** → Not viable on free tiers anymore
3. **Special characters must be URL-encoded** → Use `urllib.parse.quote()`
4. **IPv6 support is limited** → Use connection poolers (IPv4)
5. **Alembic needs explicit configuration** → Override `sqlalchemy.url` from env
6. **Reflex needs single-port mode** → Use `--single-port` flag
7. **Production URLs must be explicit** → Set `api_url` and `deploy_url`
8. **Session pooler > Direct connection** → Better compatibility on cloud platforms
9. **Build once, run many** → Don't export frontend separately in production
10. **Environment variables are king** → Never hardcode database URLs

---

## 🚀 Performance Notes

### Render Free Tier Characteristics:

**Cold Starts:**
- After 15 minutes of inactivity, service spins down
- First request after sleep takes 30-60 seconds
- Subsequent requests are fast

**Mitigation:**
- Use UptimeRobot or similar to ping every 14 minutes
- Keeps service warm for active hours
- Still spins down overnight (acceptable for side projects)

**Build Times:**
- 5-10 minutes per deployment
- Most time spent on dependency installation
- Caching helps but limited on free tier

**Runtime Performance:**
- Adequate for small apps (5-50 users)
- 512MB RAM limit (sufficient for Reflex apps)
- Shared CPU (slower than dedicated)

### When to Upgrade:

**Signs you need paid tier:**
- Users complain about cold starts
- Build times too long (>10 min)
- Out of memory errors
- Need faster response times

**Upgrade Options:**
- Render Starter: $7/month (1GB RAM, no spin-down)
- Railway: $5/month (better DX)
- Fly.io: Pay as you go (still cheap for small apps)

---

## 📚 Resources

### Documentation:
- **Render:** https://render.com/docs
- **Supabase:** https://supabase.com/docs
- **Reflex:** https://reflex.dev/docs
- **Alembic:** https://alembic.sqlalchemy.org/

### Connection Strings:
- **PostgreSQL format:** `postgresql://user:pass@host:port/database`
- **URL encoding:** https://www.urlencoder.org/
- **Supabase pooler docs:** https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler

### Troubleshooting:
- **Render status:** https://status.render.com/
- **Supabase status:** https://status.supabase.com/
- **Common errors:** https://render.com/docs/troubleshooting-deploys

---

## 🏁 Conclusion

Deploying a Reflex app to free hosting in 2024 requires:

1. **Using external cloud databases** (not file-based SQLite)
2. **Careful URL encoding** of credentials
3. **Proper port binding** configuration
4. **Environment variable management** across tools
5. **Understanding platform limitations** (cold starts, IPv6, etc.)

**The good news:**
- It's still possible to deploy for free!
- Supabase + Render work well together
- Perfect for side projects and learning

**The effort:**
- More complex than "just deploy SQLite"
- But you learn production best practices
- Skills transfer to paid platforms too

---

**Remember:** Next time, start with PostgreSQL from day one. It's easier to develop with the same database you'll deploy to!

---

*Document created after successfully deploying a Reflex vocabulary learning app to Render + Supabase on free tiers. Total time: ~4 hours (including troubleshooting). Final cost: $0/month.* 🎉
