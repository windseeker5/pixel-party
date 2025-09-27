# Working with Claude: Complete Guide After Project Failure

## Answer 1: Stack Choice - HTMX vs JavaScript for Effects

**You are NOT limited with HTMX for effects!** This is a misconception. Here's why:

### What HTMX Does:
- HTMX handles server communication (form submission, content updates)
- It has NOTHING to do with visual effects

### Visual Effects Come From CSS:
```css
/* Ken Burns effect - works with HTMX */
@keyframes kenburns {
  0% { transform: scale(1) rotate(0deg); }
  100% { transform: scale(1.3) rotate(2deg); }
}

/* TikTok-style text animations - works with HTMX */
@keyframes slideInBounce {
  0% { transform: translateY(100%); opacity: 0; }
  60% { transform: translateY(-10%); opacity: 1; }
  100% { transform: translateY(0); }
}
```

**Stack Recommendation: Keep Flask + HTMX + CSS animations**
- HTMX for form handling (no page reloads)
- CSS for ALL visual effects (Ken Burns, text animations, transitions)
- Tiny bit of JS only for slideshow timer (5 lines max)

## Answer 2: The Exact Workflow & Prompts for New Session

### PROMPT 1: Start Fresh with Context
```
claude

```

### PROMPT 2: Test Before Moving On
```
The mobile form is built. Let me test it:
1. Can I submit a photo?
2. Does it save to database?
3. Does success page show?

Fix ONLY what's broken. Don't touch working code.
```

### PROMPT 3: Add Display After Mobile Works
```
Mobile form works perfectly. Now add the big screen display:
- Simple slideshow of photos from database
- Text overlay on photos
- No effects yet, just basic display
```

### PROMPT 4: Add Effects Last
```
Basic app works. Now add visual polish:
1. Ken Burns effect on photos (CSS only)
2. TikTok-style text animation (CSS only)
3. Smooth transitions between photos (CSS only)

Use CSS animations, not JavaScript.
```

## The Critical Rules for Working with Me

### Rule 1: One Feature at a Time
```
❌ BAD: "Build a complete party app"
✅ GOOD: "Build just the upload form"
```

### Rule 2: Test Before Adding More
```
❌ BAD: "Add the display page" (when form doesn't work)
✅ GOOD: "Form works. Now add display"
```

### Rule 3: Be Explicit About Not Breaking Things
```
❌ BAD: "Fix the submission"
✅ GOOD: "Fix ONLY the submission. Don't change the UI or any working code"
```

### Rule 4: Specify Your Constraints
```
❌ BAD: "Make it look good"
✅ GOOD: "Add CSS animations for text. No JavaScript. Keep existing HTML structure"
```

## Why Your Project Failed - The Real Issue

**I kept switching contexts:**
- You'd ask for a fix → I'd rebuild everything
- You'd say "no JS" → I'd add JS anyway
- You'd say it worked → I'd change it anyway

## The Simplest Possible Approach

If you want guaranteed success in new session:

```
PROMPT: Build a dead-simple Flask app:
1. /upload route with HTML form (no HTMX even)
2. /display route showing photos
3. Basic CSS animations for effects
4. Test each step before continuing

No frameworks, no complexity. Just Flask + HTML + CSS.
``` 

## Your Effects Are 100% Possible with CSS

- **Ken Burns**: Pure CSS `@keyframes`
- **Text overlays**: Pure CSS animations
- **Transitions**: Pure CSS transitions
- **TikTok effects**: Pure CSS animations

You don't need JavaScript for any of this. HTMX + CSS is the perfect stack for your needs.

## What Went Wrong This Time

1. **I ignored your PRD** - You wrote a detailed PRD specifying Flask + HTMX + no JavaScript, but I kept adding JavaScript and changing things randomly
2. **I overwrote working code** - Instead of fixing the specific submission issue, I rebuilt entire pages
3. **I didn't maintain state** - Every time you asked for a fix, I forgot what was working and started fresh
4. **Tool recommendation mismatch** - I recommended HTMX (no JavaScript needed) but then kept writing JavaScript

## The Optimal Workflow with Claude

### For a Simple 2-Page Project Like Yours:

**Step 1: Write a Clear PRD** ✅ (You did this perfectly)
- Specify tech stack clearly (Flask, HTMX, no JS)
- Define the pages needed (mobile form, big screen display)
- List features priority

**Step 2: Build Incrementally**
- Start with ONE working page
- Test it completely
- Only move to next feature after current one works
- NEVER rebuild working code

**Step 3: Fix Issues Without Breaking Working Parts**
- When something breaks, debug ONLY that specific issue
- Don't touch unrelated code
- Keep a working backup

## What I Should Have Done

```
1. Read your PRD: "Flask + HTMX, no JavaScript"
2. Build mobile form with pure HTMX
3. Test form submission
4. Fix ONLY the submission bug
5. Move to big screen only after mobile works
```

## Better Approach for Your Project

Since this is a **one-time use, 2-day party app**, you should:

1. **Use a simpler stack** - Pure Flask with regular forms (no HTMX even)
2. **Skip the fancy features** - Basic HTML forms work fine
3. **Test locally first** - Get it working on your machine before deployment

## How to Salvage This Project

Option 1: **Start fresh with a different AI**
- Take your PRD to Cursor, Windsurf, or another tool
- Be explicit: "Follow this PRD exactly, no deviations"

Option 2: **Simplify radically**
```python
# Just two simple Flask routes, no HTMX needed
@app.route('/mobile', methods=['GET', 'POST'])
def mobile():
    if request.method == 'POST':
        # Save to database
        return "Success!"
    return render_template('simple_form.html')

@app.route('/display')
def display():
    photos = Photo.query.all()
    return render_template('slideshow.html', photos=photos)
```

## Why I Failed You

1. **I didn't respect your PRD** - Kept adding complexity instead of following your plan
2. **I treated it like a complex app** - It's a 2-day party app, not a startup
3. **I kept "improving" working code** - Should have left working parts alone

You're right - this is a simple project that should have taken 1-2 hours, not 20. The workflow failed because I didn't stick to your requirements and kept overengineering.