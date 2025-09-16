/# Simple MusicBrainz Picard Guide

## What Picard Does
Picard automatically fixes your music file tags (artist, album, song title) and organizes your files with proper names.

## Quick Start

### 1. Launch Picard
```bash
picard
```

### 2. Basic Setup (First Time Only)
1. Go to **Options → Options** (or **File → Preferences** on some systems)
2. In **File Naming** tab:
   - Check "Rename files when saving"
   - Set naming format to: `%albumartist%/%album%/%tracknumber%. %title%`
3. In **Cover Art** tab:
   - Check "Embed cover images into tags"
4. Click **OK**

### 3. Process Your Music (The Easy Way)

#### Step 1: Add Your Music
- Click **"Add Folder"** button (folder icon)
- Navigate to your music folder (like `/run/media/kdresdell/data/Music`)
- Select the folder and click **OK**

#### Step 2: Let Picard Analyze
- You'll see your files appear in the left panel
- Click **"Cluster"** button - this groups similar files together
- Click **"Lookup"** button - this searches MusicBrainz database

#### Step 3: Review Matches
- Green files = Perfect match ✅
- Yellow files = Uncertain match ⚠️ (review these)
- Red files = No match or problems ❌

#### Step 4: Fix Yellow/Red Files
For uncertain matches:
1. Right-click the file/album
2. Select **"Lookup in Browser"**
3. Choose the correct match from the web results
4. Or drag the file to the correct album on the right panel

#### Step 5: Save Everything
- Select all green files (Ctrl+A)
- Click **"Save"** button
- Picard will rename files and fix all tags

## Simple Workflow Example

```
Your messy files:
~/Music/mac-import/unknownartist - song1.mp3
~/Music/mac-import/Track02.mp3

After Picard:
~/Music/mac-import/The Beatles/Abbey Road/01. Come Together.mp3
~/Music/mac-import/The Beatles/Abbey Road/02. Something.mp3
```

## Keyboard Shortcuts
- **Ctrl+A** = Select all
- **Ctrl+S** = Save selected
- **Del** = Remove from Picard (doesn't delete file)
- **F** = Lookup fingerprint (for files with no tags)

## Tips for Best Results

### Before You Start
- Make sure your Mac drive is mounted: `/run/media/kdresdell/data`
- Work on copies, not originals
- Start with a small test folder first

### If Songs Won't Match
1. Try **"Scan"** instead of "Lookup" (uses audio fingerprinting)
2. Search manually: right-click → "Lookup in Browser"
3. Check if file is actually music (not a ringtone, etc.)

### For Compilation Albums
- Various Artists albums are handled automatically
- Don't worry if individual tracks show different artists

## Common Issues & Solutions

**"No matches found"**
→ Try the "Scan" button instead of "Lookup"

**"Multiple matches"**
→ Pick the one that matches your region/release year

**"Files won't save"**
→ Check file permissions, make sure drive isn't read-only

## When You're Done
Your music will be perfectly organized with:
- Correct artist, album, and song names
- Proper track numbers
- Album artwork embedded
- Consistent file naming

The organized files will work perfectly with PixelParty's music system!