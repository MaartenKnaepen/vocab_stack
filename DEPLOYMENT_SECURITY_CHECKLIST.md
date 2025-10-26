# Production Deployment Security Checklist

## Quick Reference - Must Do Before Going Live

### ⚠️ CRITICAL - Do Not Deploy Without These

- [ ] **Generate SECRET_KEY**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Add to `.env` file

- [ ] **Set up HTTPS/SSL Certificate**
  - Let's Encrypt (free)
  - Cloudflare
  - Or your hosting provider

- [ ] **Update .env file**
  ```env
  ENV=production
  DEBUG=False
  SESSION_COOKIE_SECURE=True
  FORCE_HTTPS=True
  SECRET_KEY=your-generated-key-here
  ```

- [ ] **Configure CORS**
  ```env
  CORS_ORIGINS=https://yourdomain.com
  ```
  Remove `*` wildcard!

- [ ] **Use Production Database**
  ```env
  DATABASE_URL=postgresql://user:pass@host/db
  ```
  Not SQLite!

### 🔍 Validate Configuration

Run this before deploying:
```python
from vocab_stack.config import config

errors = config.validate_production_config()
if errors:
    print("❌ FIX THESE BEFORE DEPLOYING:")
    for error in errors:
        print(f"  - {error}")
    exit(1)
else:
    print("✅ Configuration valid - ready to deploy!")
```

### 🧪 Test Security Features

```bash
# Run security tests
pytest tests/test_security.py -v

# Run all tests
pytest tests/ -v
```

All tests should pass!

### 📋 Security Features Checklist

- [x] Rate limiting on login (5 attempts per 15 min)
- [x] Password requirements (8+ chars, letter + number)
- [x] Secure session tokens (30-day expiration)
- [x] Input sanitization
- [x] Security headers
- [x] CORS configuration
- [x] HTTPS ready

### 🚀 Deployment Quick Steps

1. **Copy production config:**
   ```bash
   cp .env.production.example .env
   ```

2. **Edit .env:**
   - Set SECRET_KEY
   - Set your domain for CORS_ORIGINS
   - Configure database URL

3. **Validate:**
   ```bash
   python -c "from vocab_stack.config import config; print(config.validate_production_config())"
   ```

4. **Test:**
   ```bash
   pytest tests/test_security.py
   ```

5. **Deploy with HTTPS enabled**

### 📚 Documentation

- Full guide: `docs/SECURITY.md`
- Config options: `.env.production.example`
- Implementation details: `docs/SECURITY_IMPLEMENTATION_COMPLETE.md`

### 🆘 If Something Goes Wrong

1. Check logs for errors
2. Verify .env file is loaded
3. Ensure HTTPS is working
4. Check CORS origins match your domain
5. Review `docs/SECURITY.md`

---

**Status:** ✅ Security implementation complete
**Ready for:** Production deployment with HTTPS
