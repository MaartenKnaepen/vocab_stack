# Render.com Deployment Guide for Vocab Stack

Deploy your Vocab Stack app to Render.com's **FREE tier** with **persistent SQLite storage**!

## Why Render.com?

- ✅ **FREE tier with persistent disk** (25GB!)
- ✅ SQLite database survives deployments
- ✅ GitHub auto-deploy
- ✅ Automatic HTTPS
- ✅ Simple setup

**Trade-off:** Free tier spins down after 15 min inactivity (30s cold start)

---

## Quick Start (5 Minutes)

### Step 1: Push to GitHub (if not already done)
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Sign Up for Render
1. Go to https://render.com
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (easiest)
4. Authorize Render to access your repositories

### Step 3: Deploy with One Click! 🚀

#### Option A: Using render.yaml (Recommended)

1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your **vocab_stack** repository
3. Render auto-detects `render.yaml`
4. Click **"Apply"**
5. Wait 5-10 minutes for deployment ☕

That's it! Render sets everything up automatically from the `render.yaml` file.

#### Option B: Manual Setup (if Blueprint doesn't work)

1. Click **"New +"** → **"Web Service"**
2. Connect your **vocab_stack** repository
3. Configure:
   - **Name:** `vocab-stack`
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install uv && uv sync --frozen && uv run reflex init && uv run reflex export --frontend-only --no-zip
     ```
   - **Start Command:**
     ```bash
     uv run alembic upgrade head && uv run reflex run --env prod --loglevel info
     ```
   - **Instance Type:** `Free`

4. Click **"Advanced"** → **"Add Disk"**
   - **Name:** `vocab-data`
   - **Mount Path:** `/data`
   - **Size:** `1 GB` (free)

5. Click **"Advanced"** → **"Environment Variables"**
   ```
   DATABASE_URL = sqlite:////data/vocab_stack.db
   ENV = production
   PYTHON_VERSION = 3.11
   ```

6. Click **"Create Web Service"**

### Step 4: Get Your SECRET_KEY

After deployment:
1. Go to your service → **"Environment"** tab
2. Render auto-generated a `SECRET_KEY` - keep it!
3. Or add one manually:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### Step 5: Update ALLOWED_ORIGINS

1. Copy your app URL (e.g., `https://vocab-stack.onrender.com`)
2. Go to **"Environment"** tab
3. Add environment variable:
   ```
   ALLOWED_ORIGINS = https://vocab-stack.onrender.com
   ```
4. Click **"Save Changes"** (auto-redeploys)

### Step 6: Test Your App! 🎉

1. Open your Render URL
2. Sign up for an account
3. Create topics and flashcards
4. Test review sessions
5. Share with your users!

---

## Understanding Render Free Tier

### What You Get (FREE):
- ✅ 750 hours/month (enough for always-on for 31 days!)
- ✅ 25GB persistent disk for your database
- ✅ Automatic HTTPS/SSL
- ✅ GitHub auto-deploy
- ✅ Custom domain support
- ✅ Unlimited bandwidth (fair use)

### Limitations:
- ⚠️ Spins down after **15 minutes** of inactivity
- ⚠️ First request after sleep takes **~30 seconds** (cold start)
- ⚠️ 512MB RAM limit
- ⚠️ Shared CPU

### For 5 Users:
This is **perfect**! The cold starts are the only annoyance, but for a side project with light usage, it's completely fine.

---

## How Your Database Works

### Storage Architecture:
```
Render Web Service:
├── /opt/render/project/src/     (your code - replaced on deploy)
└── /data/                        (persistent disk - SAFE!)
    └── vocab_stack.db            (your database)
```

### On Code Deployment:
- ✅ Code gets updated
- ✅ Container restarts
- ✅ `/data` disk remounts
- ✅ **Database is untouched!**

### On Service Sleep/Wake:
- ✅ Container stops
- ✅ Disk persists
- ✅ Container restarts on request
- ✅ Database still there!

---

## Auto-Deploy from GitHub

Once set up, deploying is automatic:

```bash
# Make changes
git add .
git commit -m "New feature"
git push origin main

# Render automatically:
# 1. Detects push
# 2. Builds your app
# 3. Deploys new version
# 4. Runs migrations
# 5. Restarts service
```

You'll see deployment progress in Render dashboard → **"Events"** tab.

---

## Monitoring Your App

### View Logs:
1. Render dashboard → Your service
2. Click **"Logs"** tab
3. See real-time application logs

### View Metrics:
1. Click **"Metrics"** tab
2. See CPU, memory, bandwidth usage

### Health Checks:
Render automatically monitors your app at `/` every 30 seconds.

---

## Database Migrations

Migrations run **automatically** on every deploy via the start command:
```bash
uv run alembic upgrade head && uv run reflex run ...
```

If you need to run migrations manually:
1. Go to **"Shell"** tab in Render dashboard
2. Run: `uv run alembic upgrade head`

---

## Backing Up Your Database

### Option 1: Manual Backup via Shell
1. Go to **"Shell"** tab
2. Run:
   ```bash
   sqlite3 /data/vocab_stack.db .dump > backup.sql
   cat backup.sql
   ```
3. Copy output to local file

### Option 2: Download via Script
Create a protected admin endpoint to download backups (implement carefully with authentication!)

### Option 3: Scheduled Backups
For a small app, manual backups before major changes are usually enough.

---

## Troubleshooting

### Build Fails

**Error: "uv: command not found"**
- Solution: Make sure build command includes `pip install uv`

**Error: "reflex: command not found"**
- Solution: Check that `uv sync` is in build command

**Error: "No module named 'vocab_stack'"**
- Solution: Ensure all files are committed to git

### App Won't Start

**Error: "Address already in use"**
- Usually resolves on retry, Render handles this

**Error: "Database locked"**
- Check disk is mounted at `/data`
- Verify `DATABASE_URL` is set correctly

### Can't Access App

**503 Service Unavailable**
- App might be sleeping (free tier)
- Wait 30s for cold start
- Check logs for startup errors

**CORS errors**
- Update `ALLOWED_ORIGINS` to your Render URL
- Clear browser cache

### Database Issues

**Database resets on deploy**
- ❌ Disk not mounted correctly
- ✅ Verify disk mount path is `/data`
- ✅ Check `DATABASE_URL` points to `/data/vocab_stack.db`

**"Database is locked"**
- SQLite can have issues with concurrent writes
- For 5 users, shouldn't be a problem
- If persistent, consider PostgreSQL

---

## Upgrading from Free Tier

If you need more (no cold starts, more resources):

### Starter Plan ($7/month):
- ✅ No spin-down (always on!)
- ✅ 1GB RAM
- ✅ Faster CPU
- ✅ Priority builds

### For 5 Users:
Free tier is probably fine! Only upgrade if cold starts are annoying.

---

## Alternative: Using Docker

If the native Python buildpack has issues, you can use Docker:

1. In Render dashboard, select **"Docker"** as runtime
2. Render will use `Dockerfile.render` automatically
3. Everything else stays the same

---

## Environment Variables Reference

### Set Automatically (by render.yaml):
- `DATABASE_URL` - Database location
- `SECRET_KEY` - Auto-generated secure key
- `ENV` - Set to "production"
- `PYTHON_VERSION` - Set to "3.11"

### Set Manually (after first deploy):
- `ALLOWED_ORIGINS` - Your Render URL

### Optional:
- `SESSION_LIFETIME_DAYS` - Session duration (default: 30)
- `RATE_LIMIT_ENABLED` - Enable rate limiting (default: True)
- `LOGIN_MAX_ATTEMPTS` - Max login attempts (default: 5)

---

## Security Checklist

Before going live:

- ✅ `SECRET_KEY` is set (auto-generated by Render)
- ✅ `ALLOWED_ORIGINS` is your actual Render URL
- ✅ HTTPS is enabled (automatic on Render)
- ✅ Database file is in `/data` (persistent)
- ✅ `.env` file is not committed to git
- ✅ All sensitive data in environment variables

---

## Performance Tips

### Reduce Cold Start Time:
- Export Reflex frontend during build (already configured)
- Use `--no-dev` flag with uv (already configured)
- Keep dependencies minimal

### Keep App Warm (Free Tier):
- Use a free uptime monitoring service (like UptimeRobot)
- Ping your app every 14 minutes
- Prevents spin-down

### If You Outgrow SQLite:
For more than 20-30 concurrent users, consider:
- PostgreSQL (Render offers free tier: 90 days, 256MB)
- Or upgrade to Render's persistent database

---

## Comparison: Render vs Other Platforms

| Feature | Render Free | Koyeb Free | Fly.io Free |
|---------|------------|------------|-------------|
| **Persistent Storage** | ✅ 25GB | ❌ No | ✅ 3GB |
| **Always On** | ❌ Spins down | ✅ Yes | ✅ Yes |
| **Cold Start** | ~30s | N/A | N/A |
| **RAM** | 512MB | 512MB | 256MB |
| **Auto-deploy** | ✅ Yes | ✅ Yes | Manual |
| **HTTPS** | ✅ Auto | ✅ Auto | ✅ Auto |
| **Setup Difficulty** | 😊 Easy | 😊 Easy | 😐 Medium |

**For SQLite:** Render is the clear winner on free tier!

---

## Next Steps

After deployment:

1. ✅ Test all features thoroughly
2. ✅ Set up uptime monitoring (optional)
3. ✅ Share with your 5 users
4. ✅ Monitor logs for errors
5. ✅ Backup database before major updates

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **Reflex Docs:** https://reflex.dev/docs
- **Your app:** Check Render dashboard for logs

---

## FAQ

**Q: Will my database be deleted when I deploy updates?**
A: NO! The database is on a persistent disk at `/data`. Only your code gets updated.

**Q: What happens if I delete the service?**
A: The disk is deleted too. Backup your database first!

**Q: Can I use PostgreSQL instead?**
A: Yes! Render offers free PostgreSQL (90 days, then $7/month). Better for production.

**Q: How do I reduce cold starts?**
A: Use an uptime monitor to ping your app every 14 minutes (keeps it warm).

**Q: Is 512MB RAM enough?**
A: For 5 users with Reflex + SQLite, yes! If you have issues, upgrade to $7/month tier.

**Q: Can I use my own domain?**
A: Yes! Render supports custom domains even on free tier.

---

**Ready to deploy? Follow the Quick Start above!** 🚀
