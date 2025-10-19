# Settings Features Explained

## Overview
This document explains how the Settings page features work and how to test them.

---

## 1. Success/Error Message Icons

### What They Are
The green (✓ check) and red (⚠ alert) icons are **feedback callouts** that appear after saving changes.

### When They Appear
- **Green Success Icon**: Appears after successfully saving profile or preferences
  - Message: "Profile updated successfully!" or "Preferences saved successfully!"
  - Automatically disappears when you make another change
  
- **Red Error Icon**: Appears when something goes wrong
  - Example: "Username already taken" or "Email already in use"
  - Shows validation errors or database issues

### How to Test
1. Go to Settings page (`/settings`)
2. Change your username or email
3. Click "Save Profile"
4. You should see a **green callout** with success message
5. Try to change username to an existing one (if you have multiple users)
6. You should see a **red callout** with error message

### Why You Don't See Them Initially
- On page load, both `success_message` and `error_message` are empty strings
- The icons only render when these messages have content
- This is by design - no clutter until you perform an action

---

## 2. Show Examples During Review

### What It Does
Controls whether **example sentences** are displayed when reviewing flashcards.

### Current Status
- ✅ **Setting is stored** in database (user.show_examples)
- ✅ **Setting is displayed** in Settings page (toggle switch)
- ✅ **Setting is saved** when you click "Save Preferences"
- ✅ **Setting is now integrated** into the review page (as of latest update)

### How It Works
When reviewing a flashcard:
- If `show_examples = True` (default): Example section appears below the answer (if card has an example)
- If `show_examples = False`: Example section is hidden even if the card has an example

### How to Test
1. Go to Settings → Review Preferences
2. **Toggle OFF** "Show examples during review"
3. Click "Save Preferences"
4. Go to Review page
5. Flip a card that has an example
6. **Result**: Example section should NOT appear
7. Go back to Settings
8. **Toggle ON** "Show examples during review"
9. Click "Save Preferences"
10. Go to Review page again
11. **Result**: Example section should appear for cards with examples

### Technical Implementation
```python
# In review page, example only shows if BOTH conditions are true:
rx.cond(
    ReviewState.show_examples & (ReviewState.current_card["example"] != ""),
    # ... example box ...
)
```

---

## 3. Cards Per Session

### What It Does
Limits the number of cards shown in each review session.

### Current Status
- ✅ **Setting is stored** in database (user.cards_per_session)
- ✅ **Setting is adjustable** via slider (5-100, step=5)
- ✅ **Setting is saved** when you click "Save Preferences"
- ✅ **Setting is now integrated** into review page (as of latest update)

### How It Works
- When you start a review session, the system fetches all due cards
- Then it limits the list to the first N cards (where N = cards_per_session)
- Default: 20 cards per session

### How to Test
1. Ensure you have more than 5 cards due for review
2. Go to Settings → Review Preferences
3. Set "Cards per Session" to **5** (move slider to minimum)
4. Click "Save Preferences"
5. Go to Review page
6. **Result**: Progress should show "1 / 5" (or fewer if you have < 5 due cards)
7. Go back to Settings
8. Set "Cards per Session" to **50**
9. Click "Save Preferences"
10. Reload Review page
11. **Result**: Progress should show up to 50 cards (or all due cards if < 50)

---

## 4. Theme (Light/Dark)

### What It Does
Stores user preference for UI theme (light or dark mode).

### Current Status
- ✅ **Setting is stored** in database (user.theme)
- ✅ **Setting is displayed** in Settings page (dropdown)
- ✅ **Setting is saved** when you click "Save Preferences"
- ❌ **Setting is NOT yet applied** to the app UI (requires app-level integration)

### Why It Doesn't Work Yet
The theme setting is saved correctly, but to actually apply it requires:
1. Loading the theme preference at app initialization
2. Passing it to the Reflex app theme configuration
3. This happens in `app.py` before pages are rendered

### Current Behavior
- You can change the theme setting and it saves to database
- But the UI doesn't change because the app doesn't read this setting yet
- The note "Theme will apply on next page load" is optimistic (planned feature)

### How to Implement (Future)
```python
# In app.py
from vocab_stack.services.settings_service import SettingsService

# Load user's theme preference (would need auth system first)
settings = SettingsService.get_user_settings(1)
theme_mode = settings.get("theme", "light")

app = rx.App(
    theme=rx.theme(
        appearance=theme_mode,  # "light" or "dark"
        accent_color="blue",
        radius="large",
    )
)
```

### Browser/OS Override
Some browsers or operating systems can override theme preferences:
- **Browser Dark Mode**: Some browsers force dark mode regardless of site preferences
- **OS Dark Mode**: macOS/Windows dark mode can affect web content
- **Browser Extensions**: Dark reader extensions can override themes

To test if it's a browser issue:
1. Check browser settings for "Force Dark Mode" or similar
2. Disable any dark mode extensions
3. Try in incognito/private mode

---

## 5. Review Order

### What It Does
Controls the order in which cards are presented during review.

### Options
- **random** (default): Cards shuffled randomly each session
- **oldest_first**: Cards sorted by creation date (oldest first)
- **newest_first**: Cards sorted by creation date (newest first)

### Current Status
- ✅ **Setting is stored** in database (user.review_order)
- ✅ **Setting is displayed** in Settings page (dropdown)
- ✅ **Setting is saved** when you click "Save Preferences"
- ❌ **Setting is NOT yet applied** in review logic (requires LeitnerService update)

### How to Implement (Future)
Update `LeitnerService.get_due_cards()` to accept and apply order parameter.

---

## 6. Daily Goal

### What It Does
Sets a target number of reviews to complete per day.

### Current Status
- ✅ **Setting is stored** in database (user.daily_goal)
- ✅ **Setting is adjustable** via slider (10-200, step=10)
- ✅ **Setting is saved** when you click "Save Preferences"
- ❌ **Setting is NOT yet displayed** as progress indicator (requires Dashboard update)

### How to Implement (Future)
On the Dashboard or Statistics page:
```python
# Compare reviews_today vs daily_goal
progress = (reviews_today / daily_goal) * 100
# Show progress bar
rx.progress(value=progress)
# Show message if goal reached
if reviews_today >= daily_goal:
    rx.badge("🎉 Daily goal reached!", color="green")
```

---

## Summary Table

| Feature | Stored? | UI Control? | Functional? | Notes |
|---------|---------|-------------|-------------|-------|
| Profile (username/email) | ✅ | ✅ | ✅ | Validation works |
| Cards per session | ✅ | ✅ | ✅ | **NOW INTEGRATED** |
| Show examples | ✅ | ✅ | ✅ | **NOW INTEGRATED** |
| Review order | ✅ | ✅ | ❌ | Needs LeitnerService update |
| Daily goal | ✅ | ✅ | ❌ | Needs Dashboard display |
| Theme | ✅ | ✅ | ❌ | Needs app initialization |

---

## Testing Checklist

- [ ] Save profile - see green success message
- [ ] Try duplicate username - see red error message
- [ ] Change cards per session to 5 - review shows max 5 cards
- [ ] Toggle show examples OFF - examples hidden in review
- [ ] Toggle show examples ON - examples visible in review
- [ ] Change theme - setting saves (UI change pending)
- [ ] Adjust daily goal - setting saves (progress display pending)
- [ ] Change review order - setting saves (sorting pending)

---

## Next Steps for Full Integration

### Immediate (Can do now)
- ✅ Integrate show_examples in review page
- ✅ Integrate cards_per_session in review page

### Short-term (Requires small updates)
- Apply review_order in LeitnerService
- Show daily_goal progress on Dashboard
- Add "You've reviewed X/Y cards today" indicator

### Long-term (Requires larger changes)
- Apply theme on app initialization
- Add user authentication (currently hardcoded to user_id=1)
- Persist theme across sessions
- Add more theme options (colors, fonts, etc.)

---

**Last Updated**: Phase 6 completion + review integration
