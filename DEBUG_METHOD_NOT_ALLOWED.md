# 🔍 Debugging "Method Not Allowed" Error

## What I Just Fixed

I've added extensive debugging to help us figure out exactly what's happening:

1. **✅ Added `action="javascript:void(0);"` to all forms** - This prevents any accidental native form submissions
2. **✅ Added detailed console logging** - Every step of the form submission is now logged
3. **✅ Added initialization logging** - Shows when the page loads and handlers attach

---

## 🧪 How to Debug

### Step 1: Restart Your Server

**IMPORTANT:** Stop and restart your server to load the updated code:

```bash
# Press CTRL+C to stop
uvicorn main:app --reload
```

### Step 2: Open Browser with Console

1. Go to `http://localhost:8000/crm`
2. **Open Developer Tools (F12)**
3. **Go to the Console tab**
4. Log in (Username: `gmarr`, Password: `1234`)

### Step 3: Watch the Console on Page Load

When the page loads, you should see:

```
🎬 Initializing CRM page...
✓ Watched form found: true
✓ Want-to-watch form found: true
✓ Blog form found: true
✓ TMDB search setup for watched form
✓ TMDB search setup for want-to-watch form
✅ CRM page initialization complete
📝 Form submission handlers are attached
```

**If you DON'T see this**, the JavaScript isn't loading properly.

### Step 4: Try to Submit a Form

Let's test the **Blog Post** form since it's simplest (no file uploads):

1. Select a watched item from dropdown
2. Fill in:
   - Title: "Test Post"
   - Slug: "test-post"
   - Body: "Testing"
3. Click "Publish entry"

**Watch the console!** You should see:

```
📝 Submitting blog post: {watched_id: '3', title: 'Test Post', slug: 'test-post', body_length: 7}
✓ Default form submission prevented
🚀 Sending POST to /api/blog
📥 Response status: 200 OK
Blog post created successfully: {id: 1, ...}
```

**OR if it fails:**

```
📝 Submitting blog post: {watched_id: '3', title: 'Test Post', ...}
✓ Default form submission prevented
🚀 Sending POST to /api/blog
📥 Response status: 405 Method Not Allowed
❌ Create failed: {detail: "Method Not Allowed"}
```

### Step 5: Check the Network Tab

1. In Developer Tools, click the **Network** tab
2. Try submitting the form again
3. Look for a request to `/api/blog` (or `/api/watched`, etc.)
4. Click on it to see details

**What to check:**

- **Request URL**: Should be `http://localhost:8000/api/blog` (or `/api/watched`)
- **Request Method**: Should be `POST`
- **Status Code**: What is it? 405? 401? 500?
- **Response**: Click "Response" tab to see the error message

---

## 🔎 What Each Error Means

### If you see: `405 Method Not Allowed`

**This means:** The URL exists but doesn't accept POST requests

**Possible causes:**
1. The request is going to the wrong URL (check Network tab)
2. The endpoint isn't configured to accept POST
3. There's a routing issue in FastAPI

**What to check:**
- In Network tab, what's the actual URL being called?
- Is it `/api/blog` or something else like `/crm`?

### If you see: `401 Unauthorized`

**This means:** Authentication failed

**Solution:** You're not logged in or session expired
- Refresh the page and log in again

### If you see: `400 Bad Request`

**This means:** The data you're sending is invalid

**Check terminal logs** for the exact error:
```
ERROR:app.routers.items:Watched item not found: id=999
```

### If you see: `500 Internal Server Error`

**This means:** Server crashed

**Check terminal** for Python traceback showing the error

---

## 📋 What to Tell Me

If it's still failing, copy and paste these from the console:

### 1. Initialization Logs

```
🎬 Initializing CRM page...
... (all the lines)
```

### 2. Submission Logs

```
📝 Submitting blog post: ...
... (all the lines including the error)
```

### 3. Network Request Details

From Network tab:
- Request URL: `_______________`
- Request Method: `_______________`
- Status Code: `_______________`
- Response: `_______________`

### 4. Terminal Output

Any ERROR or WARNING lines from the terminal

---

## 🎯 Expected Behavior

When everything works correctly:

**Console:**
```
🎬 Initializing CRM page...
✓ All forms found
✅ CRM page initialization complete

📝 Submitting blog post: {...}
✓ Default form submission prevented
🚀 Sending POST to /api/blog
📥 Response status: 200 OK
✅ Blog post created successfully
```

**Terminal:**
```
INFO:app.routers.auth:Auth successful for user: 'gmarr'
INFO:app.routers.items:Blog post creation requested: watched_id=3, title='Test Post', slug='test-post'
INFO:app.routers.items:Blog post created successfully: id=1, slug='test-post'
```

**Browser:**
- Form resets
- New blog post appears in the list
- No error alerts

---

## 🚨 Common Issues

### Issue 1: Console shows nothing when clicking submit

**Problem:** JavaScript isn't attaching event handlers

**Solution:**
- Hard refresh the page (CTRL+SHIFT+R)
- Check if there are any JavaScript errors in console
- Make sure you restarted the server

### Issue 2: Request goes to `/crm` instead of `/api/blog`

**Problem:** Native form submission instead of JavaScript

**Solution:**
- The `action="javascript:void(0);"` should prevent this
- Make sure page is fully loaded before submitting
- Check console for initialization logs

### Issue 3: 405 on `/api/blog` specifically

**Problem:** Endpoint might not be registered

**Check terminal on startup** for:
```
INFO:     Application startup complete.
```

And verify routes are registered (no errors on startup)

---

## 💡 Quick Test

Try this in the browser console:

```javascript
fetch('/api/watched', {
    method: 'GET',
    credentials: 'same-origin'
}).then(r => r.json()).then(console.log)
```

This should return your watched items. If this works, the endpoint is fine.

Then try:

```javascript
console.log(document.getElementById('add-blog-form'))
```

This should show the form element. If this returns `null`, the form isn't in the DOM.

---

**Try it now and tell me what you see in the console!**
