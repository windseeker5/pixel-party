# Simple Messenger Thread Downloader

Downloads all photos, videos, and messages from a specific Facebook Messenger group thread using a two-step process.

## Quick Setup

1. **Install dependencies:**
   ```bash
   cd utils/messenger_downloader
   pip install playwright python-dotenv requests
   playwright install chromium
   ```

2. **Setup thread URL:**
   ```bash
   cp .env.example .env
   # Edit .env with your thread URL
   ```

3. **Get your thread URL:**
   - Open messenger.com in browser
   - Go to your group conversation
   - Copy the URL (looks like: `https://www.messenger.com/t/123456789`)

4. **Configure .env file:**
   ```
   MESSENGER_THREAD_URL=https://www.messenger.com/t/your_thread_id
   ```

## Two-Step Process

### Step 1: Login and Save Session

```bash
python login_helper.py
```

This will:
- Open browser to your thread
- Let you login manually (handle CAPTCHAs, 2FA, 6-digit codes)
- Save cookies when you close the browser
- **No terminal access issues!**

### Step 2: Download Content

```bash
python download_messages.py
```

This will:
- Use saved cookies (no login needed)
- Download all photos, videos, and messages
- Save everything to `output/` folder

## Output Structure

```
utils/messenger_downloader/output/
├── photos/
│   ├── photo_001.jpg
│   ├── photo_002.jpg
│   └── ...
├── videos/
│   ├── video_001.mp4
│   ├── video_002.mp4
│   └── ...
└── messages.json  (all text messages with timestamps)
```

## Important Notes

- **Login Once**: Step 1 saves cookies, so you only need to login once
- **Session Persistence**: Cookies stay valid for days/weeks
- **No Credentials Stored**: Only your thread URL is needed in .env
- **Re-downloadable**: Run Step 2 multiple times without re-login
- **Terminal Access**: No issues losing terminal - close browser when done

## Troubleshooting

- **Session expired**: Re-run `python login_helper.py`
- **No cookies file**: Make sure you ran Step 1 first
- **Login redirects**: Complete all steps manually in browser, then close
- **Missing images**: Facebook may have changed - script will adapt

## Benefits

✅ **No terminal access problems**
✅ **Login once, download many times**
✅ **Handle all security challenges manually**
✅ **Restart downloads without re-login**
✅ **Simple two-step process**

That's it! Login once, download everything.