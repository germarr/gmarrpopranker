# 🚀 Quick Start Guide - Movie Ranker 2026

## ✅ All Issues Have Been Fixed!

### What Was Wrong:

1. **❌ Forms missing attributes** → Form inputs not being sent properly
2. **❌ TMDB API using wrong auth** → Bearer token not supported
3. **❌ USERNAME conflict** → System variable overriding .env

### What's Now Fixed:

1. **✅ All forms have proper attributes** → `method="POST"` and `enctype="multipart/form-data"`
2. **✅ TMDB supports Bearer tokens** → Automatically detects and uses correct auth
3. **✅ No more USERNAME conflict** → Using `BASIC_AUTH_USERNAME` instead
4. **✅ Comprehensive logging** → See exactly what's happening in terminal and console

---

## 📋 Step-by-Step Instructions

### Step 1: Verify Configuration

Run the startup check:

```bash
python startup_check.py
```

**Expected output:**
```
✅ ALL CHECKS PASSED!
```

If you see any ❌ errors, fix them before continuing.

---

### Step 2: Start the Server

```bash
uvicorn main:app --reload
```

**Watch the terminal!** You should see:

```
INFO:app.routers.auth:Loaded .env file from: .../app/.env
INFO:app.routers.auth:DEBUG - Loaded BASIC_AUTH_USERNAME: 'gmarr'
INFO:app.routers.auth:DEBUG - Loaded BASIC_AUTH_PASSWORD: '1234'
INFO:app.routers.items:Loaded .env file from: .../app/.env
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### Step 3: Open Your Browser

1. Navigate to: `http://localhost:8000/crm`
2. **Open Developer Tools (F12)** → Go to Console tab
3. Log in with:
   - **Username**: `gmarr`
   - **Password**: `1234`

**Watch the terminal!** You should see:

```
INFO:app.routers.auth:DEBUG - Auth attempt - Provided username: 'gmarr'
INFO:app.routers.auth:DEBUG - Expected username: 'gmarr'
INFO:app.routers.auth:DEBUG - Username match: True
INFO:app.routers.auth:DEBUG - Password match: True
INFO:app.routers.auth:Auth successful for user: 'gmarr'
```

---

### Step 4: Test TMDB Search

1. In the "Add to Watched" form, find "TMDB search"
2. Type: **"The Matrix"**
3. Click **"Search"**

**Watch BOTH:**

**Terminal:**
```
INFO:app.routers.items:TMDB search requested: query='The Matrix', media_type='None'
INFO:app.routers.items:Using Bearer token authentication for TMDB request to /search/multi
INFO:app.routers.items:TMDB search returned 20 results
```

**Browser Console:**
```
TMDB search: The Matrix null
TMDB search response status: 200
TMDB search results: Array(20)
```

**You should see:**
- Movie posters appearing in the results
- Clickable results with titles and years

4. **Click on "The Matrix (1999)"**

**Watch the logs again!**

**Terminal:**
```
INFO:app.routers.items:TMDB details requested: media_type='movie', id=603
INFO:app.routers.items:Using Bearer token authentication for TMDB request to /movie/603
```

**Browser Console:**
```
Fetching TMDB details for: {id: 603, media_type: 'movie', ...}
TMDB details response status: 200
TMDB details received: {tmdb_id: 603, title: 'The Matrix', ...}
```

**You should see:**
- Form fields auto-filled
- Movie poster preview appearing
- Metadata (year, runtime, genres, rating) showing

---

### Step 5: Add a Watched Item

1. Fill in the remaining fields:
   - **Score**: 9
   - **Comment**: "Mind-bending classic"
   - **Watch date**: Select a date
2. Click **"Add to watched"**

**Watch the terminal and console!**

If successful:
- Item appears in "Watched list" below
- Form resets
- No errors

If it fails:
- Check the browser console for the error message
- Check the terminal for detailed error logs

---

### Step 6: Create a Blog Post

1. Scroll to "Blog entries" section
2. Select a watched item from dropdown
3. Fill in:
   - **Title**: "Why The Matrix Still Matters"
   - **Slug**: Auto-filled as "why-the-matrix-still-matters"
   - **Body**: Write your blog post
4. Watch the live preview update as you type
5. Click **"Publish entry"**

**Watch the logs!**

**Terminal:**
```
INFO:app.routers.auth:Auth successful for user: 'gmarr'
INFO:app.routers.items:Blog post creation requested: watched_id=X, title='Why The Matrix Still Matters', slug='why-the-matrix-still-matters'
INFO:app.routers.items:Blog post created successfully: id=1, slug='why-the-matrix-still-matters'
```

**Browser Console:**
```
Submitting blog post: {watched_id: '3', title: '...', slug: '...', body_length: 42}
Blog post response status: 200
Blog post created successfully: {id: 1, ...}
```

**Success indicators:**
- Blog post appears in the blog list below
- Form resets
- No error alerts

---

## 🔍 Troubleshooting

### If TMDB Search Still Doesn't Work:

1. **Check the error in browser console** - It will tell you the exact problem
2. **Check terminal logs** - Look for ERROR messages
3. **Verify API key** - Run `python test_tmdb_bearer.py`
4. **Common issues:**
   - `401 Unauthorized` → API key is invalid or expired
   - `502 Bad Gateway` → Network issue or TMDB is down
   - `500 Internal Server Error` → Check terminal for Python traceback

### If Blog Posts Don't Submit:

1. **Check browser console** - You'll see the exact error
2. **Common issues:**
   - "Could not add blog post. Check the console..." → Look at the error.message in console
   - `401 Unauthorized` → Authentication failed (check username/password)
   - `400 Bad Request - Watched item not found` → Select a valid watched item from dropdown
   - `400 Bad Request - Slug already exists` → Change the slug to something unique

### If Authentication Fails:

**Terminal will show:**
```
INFO:app.routers.auth:DEBUG - Auth attempt - Provided username: 'XXX'
INFO:app.routers.auth:DEBUG - Expected username: 'gmarr'
INFO:app.routers.auth:DEBUG - Username match: False
```

**Fix:**
- Make sure you're typing exactly: `gmarr` and `1234`
- Case-sensitive!
- Check `app/.env` file has correct values

---

## 🎯 What to Watch For

### Good Signs ✅:

- Terminal shows INFO logs for every action
- Browser console shows success messages
- No red errors in either place
- Forms reset after successful submission
- Items appear in lists immediately

### Bad Signs ❌:

- Red ERROR messages in terminal
- Red errors in browser console
- Alert popups saying "Could not..."
- Forms don't reset
- Nothing happens when you click buttons

**If you see bad signs:**
1. Read the error message carefully
2. Check BOTH terminal AND browser console
3. The error message will tell you exactly what's wrong

---

## 📞 Still Stuck?

1. **Copy the exact error message** from browser console
2. **Copy the ERROR log** from terminal
3. **Tell me:**
   - What you were trying to do
   - What you expected to happen
   - What actually happened
   - The error messages from both places

---

## 🎉 Success Checklist

After following this guide, you should be able to:

- [ ] Log in to /crm with gmarr / 1234
- [ ] Search TMDB and see movie results
- [ ] Click on a movie and see the form auto-fill
- [ ] Add a watched item successfully
- [ ] Create a blog post about a watched item
- [ ] See comprehensive logs in terminal showing everything working

---

**Everything is configured correctly now. The issue was the form attributes. Just restart your server and follow the steps above!**
