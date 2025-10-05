"""Mobile interface routes for guests with HTMX support."""

import os
import uuid
import threading
import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from app import db
from app.models import Guest, Photo, MusicQueue, get_setting
from app.services.auth import guest_required, is_admin_authenticated, is_guest_authenticated

mobile_bp = Blueprint('mobile', __name__)


def validate_utf8_text(text):
    """Validate that text is properly UTF-8 encoded and safe for database storage."""
    if not text:
        return True, text

    try:
        # Ensure it's a string (not bytes)
        if isinstance(text, bytes):
            text = text.decode('utf-8')

        # Validate that we can encode and decode without issues
        text.encode('utf-8').decode('utf-8')

        # Remove any null bytes or other problematic characters
        cleaned_text = text.replace('\x00', '').strip()

        return True, cleaned_text
    except (UnicodeDecodeError, UnicodeEncodeError) as e:
        current_app.logger.error(f"UTF-8 validation failed: {e}")
        return False, text


def download_youtube_async(video_url, title, artist, app, music_request_id):
    """Download YouTube audio in background thread."""
    import traceback
    import time

    # Create debug log file for thread debugging
    def log_to_file(message):
        """Log to debug file with timestamp"""
        try:
            with open('youtube_download_debug.log', 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] ID:{music_request_id} - {message}\n")
                f.flush()
        except Exception as log_error:
            print(f"Failed to write debug log: {log_error}")

    log_to_file(f"🚀 Thread started: '{title}' by '{artist}' from {video_url}")

    try:
        with app.app_context():
            from app import db
            from app.models import MusicQueue

            log_to_file("✅ App context acquired")

            music_request = None
            try:
                # Update status to downloading
                log_to_file("📊 Querying database for music request")
                music_request = MusicQueue.query.get(music_request_id)
                if music_request:
                    log_to_file(f"✅ Found music request: {music_request.song_title}")
                    music_request.status = 'downloading'
                    db.session.flush()  # Immediate flush for status visibility
                    db.session.commit()
                    log_to_file("✅ Status updated to 'downloading'")
                    current_app.logger.info(f"🎵 Starting background download: {title} by {artist} (ID: {music_request_id})")
                else:
                    log_to_file("❌ Music request not found in database")
                    current_app.logger.error(f"❌ Music request {music_request_id} not found in database")
                    return

                log_to_file("🔧 Getting YouTube service")
                from app.services.youtube_service import get_youtube_service
                youtube_service = get_youtube_service()
                log_to_file("✅ YouTube service acquired")

                log_to_file(f"⬇️ Starting download from: {video_url}")
                copied_filename = youtube_service.download_audio(video_url, title, artist)
                log_to_file(f"📁 Download returned filename: {copied_filename}")

                # More robust file verification - try multiple approaches
                import os
                import glob
                import re
                from pathlib import Path

                actual_filename = None

                if copied_filename:
                    # First try the exact filename returned
                    file_path = os.path.join('media/music', copied_filename)
                    log_to_file(f"🔍 Checking for file: {file_path}")
                    if os.path.exists(file_path):
                        actual_filename = copied_filename
                        log_to_file(f"✅ Found file using exact filename: {copied_filename}")
                        current_app.logger.info(f"✅ Found file using exact filename: {copied_filename}")
                    else:
                        log_to_file(f"⚠️ Exact filename not found: {file_path}")
                        current_app.logger.warning(f"⚠️ Exact filename not found: {file_path}")

                if not actual_filename:
                    # Try to find the file using pattern matching
                    log_to_file(f"🔍 Searching for downloaded file matching: '{title}' by '{artist}'")
                    current_app.logger.info(f"🔍 Searching for downloaded file matching: '{title}' by '{artist}'")

                    # Create search patterns
                    def create_safe_filename(title, artist):
                        """Create safe filename patterns for search"""
                        safe_title = re.sub(r'[^\w\s-]', '', title or '').strip()
                        safe_artist = re.sub(r'[^\w\s-]', '', artist or '').strip()

                        patterns = []
                        if safe_artist and safe_title:
                            patterns.append(f"{safe_artist}_-_{safe_title}")
                            patterns.append(f"{safe_artist}_{safe_title}")
                            patterns.append(f"{safe_title}")  # Sometimes only title is used
                        elif safe_title:
                            patterns.append(safe_title)
                        elif safe_artist:
                            patterns.append(safe_artist)

                        # Handle spaces in different ways
                        final_patterns = []
                        for pattern in patterns:
                            final_patterns.append(re.sub(r'\s+', '_', pattern))
                            final_patterns.append(re.sub(r'\s+', ' ', pattern))
                            final_patterns.append(re.sub(r'\s+', '', pattern))

                        return final_patterns

                    search_patterns = create_safe_filename(title, artist)
                    log_to_file(f"🔍 Search patterns: {search_patterns}")
                    current_app.logger.info(f"🔍 Search patterns: {search_patterns}")

                    # Search for matching files in music directory
                    music_dir = Path('media/music')
                    for pattern in search_patterns:
                        if not pattern:
                            continue

                        # Try exact match first
                        exact_file = music_dir / f"{pattern}.mp3"
                        if exact_file.exists():
                            actual_filename = exact_file.name
                            current_app.logger.info(f"✅ Found file using exact pattern: {actual_filename}")
                            break

                        # Try glob pattern matching
                        glob_pattern = f"*{pattern}*.mp3"
                        matches = list(music_dir.glob(glob_pattern))
                        if matches:
                            actual_filename = matches[0].name
                            current_app.logger.info(f"✅ Found file using glob pattern '{glob_pattern}': {actual_filename}")
                            break

                    # If still not found, try fuzzy matching with all files
                    if not actual_filename:
                        log_to_file(f"🔍 Trying fuzzy matching for: '{title}'")
                        current_app.logger.info(f"🔍 Trying fuzzy matching for: '{title}'")
                        title_words = re.sub(r'[^\w\s]', '', title.lower()).split()

                        best_match = None
                        best_score = 0

                        for mp3_file in music_dir.glob("*.mp3"):
                            filename_lower = mp3_file.stem.lower()
                            score = sum(1 for word in title_words if word in filename_lower)

                            if score > best_score and score >= len(title_words) * 0.5:  # At least 50% match
                                best_match = mp3_file.name
                                best_score = score

                        if best_match:
                            actual_filename = best_match
                            log_to_file(f"✅ Found file using fuzzy matching: {actual_filename} (score: {best_score})")
                            current_app.logger.info(f"✅ Found file using fuzzy matching: {actual_filename} (score: {best_score})")

                if actual_filename:
                    # Update database entry with filename and status
                    log_to_file(f"✅ Found file, updating database with: {actual_filename}")
                    music_request = MusicQueue.query.get(music_request_id)  # Re-query to avoid stale session
                    if music_request:
                        music_request.filename = actual_filename
                        music_request.status = 'ready'
                        try:
                            db.session.flush()  # Immediate flush for status visibility
                            db.session.commit()
                            log_to_file(f"✅ Background download complete: {actual_filename}")
                            current_app.logger.info(f"✅ Background download complete: {actual_filename} (ID: {music_request_id})")
                        except Exception as db_error:
                            db.session.rollback()
                            log_to_file(f"❌ Database commit failed: {db_error}")
                            current_app.logger.error(f"❌ Database commit failed for {music_request_id}: {db_error}")
                            raise
                    else:
                        log_to_file("❌ Music request disappeared from database")
                        current_app.logger.error(f"❌ Music request {music_request_id} disappeared from database")
                else:
                    error_msg = f"Downloaded file not found for '{title}' by '{artist}'"
                    log_to_file(f"❌ {error_msg}")
                    current_app.logger.error(f"❌ {error_msg}")
                    current_app.logger.info(f"📁 Available files: {[f.name for f in Path('media/music').glob('*.mp3')]}")
                    raise FileNotFoundError(error_msg)

            except Exception as e:
                # Mark as error with more robust error handling
                log_to_file(f"❌ Download error: {e}")
                log_to_file(f"❌ Full traceback: {traceback.format_exc()}")
                current_app.logger.error(f"❌ Background YouTube download error for {music_request_id}: {e}")
                current_app.logger.error(f"❌ Full traceback: {traceback.format_exc()}")

                try:
                    if music_request_id:
                        music_request = MusicQueue.query.get(music_request_id)  # Re-query to avoid stale session
                        if music_request:
                            music_request.status = 'error'
                            db.session.flush()  # Immediate flush for status visibility
                            db.session.commit()
                            log_to_file("✅ Marked as error in database")
                            current_app.logger.info(f"⚠️ Marked request {music_request_id} as error")
                        else:
                            current_app.logger.error(f"❌ Could not mark {music_request_id} as error - not found in database")
                except Exception as db_error:
                    db.session.rollback()
                    log_to_file(f"❌ Failed to update error status: {db_error}")
                    current_app.logger.error(f"❌ Failed to update error status for {music_request_id}: {db_error}")

    except Exception as thread_error:
        # Catch any thread-level errors
        error_msg = f"❌ Thread crashed: {thread_error}"
        log_to_file(error_msg)
        log_to_file(f"❌ Thread traceback: {traceback.format_exc()}")

        try:
            # Try to mark as error in database
            with app.app_context():
                from app import db
                from app.models import MusicQueue
                music_request = MusicQueue.query.get(music_request_id)
                if music_request:
                    music_request.status = 'error'
                    db.session.flush()  # Immediate flush for status visibility
                    db.session.commit()
                    log_to_file("✅ Marked as error in database")
        except Exception as final_error:
            log_to_file(f"❌ Final error marking failed: {final_error}")

    log_to_file("🏁 Thread finished")


@mobile_bp.route('/')
def index():
    """Mobile index goes directly to the main form."""
    return redirect(url_for('mobile.main_form'))


def allowed_file(filename):
    """Check if file extension is allowed."""
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'])


def is_htmx_request():
    """Check if request is from HTMX."""
    return request.headers.get('HX-Request') == 'true'


def resize_image(file_path, max_width=1920, max_height=1080):
    """Resize image to max dimensions while maintaining aspect ratio."""
    try:
        with Image.open(file_path) as img:
            # Only resize if image is larger than max dimensions
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
                return True
    except Exception as e:
        current_app.logger.error(f"Error resizing image {file_path}: {e}")
    return False


@mobile_bp.route('/main')
def main_form():
    """Single screen with everything - name, photo, wish, optional music. Supports edit mode for admin."""
    edit_id = request.args.get('edit_id')
    photo = None

    # Handle edit mode
    if edit_id:
        # Only allow if admin is authenticated
        if not is_admin_authenticated():
            flash('Admin access required to edit entries', 'error')
            return redirect(url_for('auth.admin_login'))

        photo = Photo.query.get_or_404(int(edit_id))
    else:
        # For regular mode, require guest authentication
        from app.services.auth import guest_required
        if not is_guest_authenticated():
            session['login_redirect'] = request.url
            flash('Please enter the party password to continue! 🎉', 'info')
            return redirect(url_for('auth.guest_login'))

    party_title = get_setting('party_title', 'Birthday Celebration')
    host_name = get_setting('host_name', 'Birthday Star')

    # Get counts for sidebar stats
    photo_count = Photo.query.count()
    music_count = MusicQueue.query.count()

    return render_template('mobile/main_form.html',
                         party_title=party_title,
                         host_name=host_name,
                         photo_count=photo_count,
                         music_count=music_count,
                         photo=photo,
                         edit_mode=bool(edit_id))


@mobile_bp.route('/enter', methods=['POST'])
def enter():
    """Handle guest name entry with HTMX support."""
    guest_name = request.form.get('guest_name', '').strip()
    
    if not guest_name:
        if is_htmx_request():
            flash('Please enter your name to continue! ✨', 'error')
            return render_template('mobile/welcome.html', 
                                 party_title=get_setting('party_title', 'Birthday Celebration'),
                                 host_name=get_setting('host_name', 'Birthday Star'))
        else:
            flash('Please enter your name', 'error')
            return redirect(url_for('mobile.welcome'))
    
    # Create or get guest (session-free)
    session_id = str(uuid.uuid4())
    guest = Guest.query.filter_by(name=guest_name).first()

    if not guest:
        guest = Guest(name=guest_name, session_id=session_id)
        db.session.add(guest)
        db.session.commit()
    
    # Always redirect to upload page (no HTMX needed for simple redirect)
    flash(f'Welcome to the party, {guest_name}! 🎉', 'success')
    return redirect(url_for('mobile.upload'))


@mobile_bp.route('/upload')
def upload():
    """Photo upload with wish form - supports edit mode for admin."""
    edit_id = request.args.get('edit_id')
    photo = None

    # Handle edit mode
    if edit_id:
        # Only allow if admin is authenticated
        if not is_admin_authenticated():
            flash('Admin access required to edit entries', 'error')
            return redirect(url_for('auth.admin_login'))

        photo = Photo.query.get_or_404(int(edit_id))

        return render_template('mobile/upload.html',
                             guest_name=photo.guest_name,
                             photo=photo,
                             edit_mode=True)

    # Regular upload mode
    if 'guest_name' not in session:
        return redirect(url_for('mobile.welcome'))

    return render_template('mobile/upload.html',
                         guest_name=session['guest_name'],
                         edit_mode=False)


@mobile_bp.route('/submit_memory', methods=['POST'])
def submit_memory():
    """Handle photo upload and wish submission - supports editing existing entries."""
    try:
        # Check if this is an edit operation
        edit_id = request.form.get('edit_id')
        is_edit_mode = bool(edit_id)
        existing_photo = None

        with open('submission_debug.log', 'a') as f:
            f.write(f"DEBUG: Starting submit_memory, edit_id={edit_id}, is_edit_mode={is_edit_mode}\n")

        if is_edit_mode:
            # Get the existing photo once at the beginning
            with open('submission_debug.log', 'a') as f:
                f.write(f"DEBUG: About to query photo with edit_id={edit_id}\n")
            existing_photo = Photo.query.get_or_404(int(edit_id))
            with open('submission_debug.log', 'a') as f:
                f.write(f"DEBUG: Photo found: {existing_photo.id}\n")
    except Exception as e:
        with open('submission_debug.log', 'a') as f:
            f.write(f"ERROR in submit_memory start: {str(e)}\n")
        raise

    # Check authentication based on mode
    if is_edit_mode:
        # For edit mode, require admin authentication
        if not is_admin_authenticated():
            flash('Admin access required to edit entries', 'error')
            return redirect(url_for('auth.admin_login'))
    else:
        # For regular mode, require guest authentication
        if not is_guest_authenticated():
            session['login_redirect'] = request.url
            flash('Please enter the party password to continue! 🎉', 'info')
            return redirect(url_for('auth.guest_login'))

    guest_name = request.form.get('guest_name', '').strip()

    # Log the submission attempt
    with open('submission_debug.log', 'a') as f:
        f.write(f"\n=== SUBMISSION ATTEMPT ===\n")
        f.write(f"Form keys: {list(request.form.keys())}\n")
        f.write(f"Files keys: {list(request.files.keys())}\n")
        f.write(f"guest_name: '{guest_name}'\n")

    # Validate guest name
    if not guest_name:
        with open('submission_debug.log', 'a') as f:
            f.write(f"FAIL: No guest name\n")
        flash('Please enter your name', 'error')
        return redirect(url_for('mobile.main_form'))

    # Validate UTF-8 encoding for guest name (emoji support)
    is_valid, guest_name = validate_utf8_text(guest_name)
    if not is_valid:
        with open('submission_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"FAIL: Invalid UTF-8 in guest name\n")
        flash('Invalid characters in your name. Please use standard text and emojis only.', 'error')
        return redirect(url_for('mobile.main_form'))

    with open('submission_debug.log', 'a') as f:
        f.write(f"PASS: Guest name validation\n")

    # Handle guest differently for edit vs new submissions
    if is_edit_mode:
        with open('submission_debug.log', 'a') as f:
            f.write(f"EDIT MODE: Getting guest for edit_id={edit_id}\n")
        # For edit mode, get the guest from the existing photo
        guest = existing_photo.guest or Guest.query.filter_by(name=guest_name).first()
        if not guest:
            with open('submission_debug.log', 'a') as f:
                f.write(f"EDIT MODE: Creating fallback guest\n")
            # Fallback: create guest if somehow missing
            session_id = str(uuid.uuid4())
            guest = Guest(name=guest_name, session_id=session_id)
            db.session.add(guest)
            db.session.commit()
        with open('submission_debug.log', 'a') as f:
            f.write(f"EDIT MODE: Guest found/created: {guest.name} (ID: {guest.id})\n")
    else:
        # For new submissions, create or get guest based on form name
        session_id = str(uuid.uuid4())
        guest = Guest.query.filter_by(name=guest_name).first()
        if not guest:
            guest = Guest(name=guest_name, session_id=session_id)
            db.session.add(guest)
            db.session.commit()
    
    # Get form data
    wish_message = request.form.get('wish_message', '').strip()
    file = request.files.get('photo')
    selected_song = request.form.get('selected_song', '').strip()
    
    # Enhanced debug logging
    print(f"🔍 FORM DEBUG:")
    print(f"   file={file}, filename={file.filename if file else 'None'}")
    print(f"   wish_message='{wish_message}'")
    print(f"   selected_song='{selected_song}'")
    print(f"   selected_song length: {len(selected_song) if selected_song else 0}")
    if selected_song:
        try:
            import json
            song_data = json.loads(selected_song)
            print(f"   📀 Parsed song: {song_data.get('title')} - {song_data.get('artist')}")
            print(f"   📁 File path: {song_data.get('file_path', 'MISSING')}")
        except Exception as e:
            print(f"   ❌ JSON parse error: {e}")
            print(f"   Raw selected_song: {repr(selected_song)}")
    
    # File validation - optional for both new uploads and edits
    if not file or file.filename == '':
        # No file uploaded - this is now allowed for both new and edit modes
        file = None
        with open('submission_debug.log', 'a') as f:
            f.write(f"INFO: No file uploaded - proceeding with wish-only submission\n")
    
    # Only check file if it's not None (for edit mode without new file)
    if file:
        with open('submission_debug.log', 'a') as f:
            f.write(f"PASS: File exists - {file.filename}\n")

        if not allowed_file(file.filename):
            with open('submission_debug.log', 'a') as f:
                f.write(f"FAIL: File type not allowed - {file.filename}\n")
            supported_formats = ', '.join(current_app.config['ALLOWED_EXTENSIONS'])
            error_msg = f'File type not supported. Please use: {supported_formats}'
            if is_htmx_request():
                return render_template('mobile/upload.html',
                                     guest_name=session['guest_name'],
                                     error=error_msg)
            else:
                flash(error_msg, 'error')
                return redirect(url_for('mobile.upload'))

        with open('submission_debug.log', 'a') as f:
            f.write(f"PASS: File type allowed\n")
    else:
        with open('submission_debug.log', 'a') as f:
            f.write(f"EDIT MODE: No new file uploaded, keeping existing\n")
    
    if not wish_message:
        error_msg = 'Please write a birthday wish to go with your photo! 💝'
        if is_htmx_request():
            return render_template('mobile/upload.html', 
                                 guest_name=session['guest_name'],
                                 error=error_msg)
        else:
            flash(error_msg, 'error')
            return redirect(url_for('mobile.upload'))
    
    # Validate UTF-8 encoding for wish message (emoji support)
    is_valid, wish_message = validate_utf8_text(wish_message)
    if not is_valid:
        error_msg = 'Invalid characters in your message. Please use standard text and emojis only.'
        if is_htmx_request():
            return render_template('mobile/upload.html',
                                 guest_name=session['guest_name'],
                                 error=error_msg)
        else:
            flash(error_msg, 'error')
            return redirect(url_for('mobile.upload'))

    # Limit wish message to 140 characters (with proper emoji handling)
    # Note: We count actual characters, not bytes, and allow full emoji support
    # Since we're using db.Text, we can be more generous with the limit
    if len(wish_message) > 140:
        # Truncate at character boundary, not byte boundary
        wish_message = wish_message[:140]

    try:
        # Initialize file variables with defaults for wish-only submissions
        unique_filename = None
        original_filename = None
        file_size = 0
        file_type = 'wish'  # Default to 'wish' for no-file submissions
        video_duration = None
        thumbnail_filename = None

        if file:  # Only process file if one was uploaded
            try:
                # Use FileHandler for proper file processing and validation
                from app.services.file_handler import file_handler
                import asyncio

                # Get file data
                file_data = file.read()
                original_filename = file.filename

                # Save file using FileHandler (handles both images and videos)
                def run_async_save():
                    return asyncio.run(file_handler.save_file(file_data, original_filename, guest.name))

                success, message, unique_filename = run_async_save()

                if not success:
                    error_msg = f'Upload failed: {message}'
                    if is_htmx_request():
                        return render_template('mobile/upload.html',
                                             guest_name=session.get('guest_name', ''),
                                             error=error_msg)
                    else:
                        flash(error_msg, 'error')
                        return redirect(url_for('mobile.main_form'))

                # Get file info
                file_info = file_handler.get_file_info(unique_filename)
                file_size = file_info.get('file_size', 0)
                file_type = file_info.get('file_type', 'image')

                # Get video duration and thumbnail if it's a video
                if file_type == 'video':
                    file_path = file_info.get('file_path')
                    if file_path:
                        _, _, duration = file_handler.validate_video_duration(file_path)
                        video_duration = duration
                        # Get thumbnail filename (generated during save_file)
                        video_name = os.path.splitext(unique_filename)[0]
                        thumbnail_filename = f"{video_name}_thumb.jpg"

            except Exception as e:
                current_app.logger.error(f"Error processing file: {e}")
                error_msg = f'File processing failed: {str(e)}'
                if is_htmx_request():
                    return render_template('mobile/upload.html',
                                         guest_name=session.get('guest_name', ''),
                                         error=error_msg)
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('mobile.upload'))

        # Create or update photo record (now supports wish-only submissions)
        if is_edit_mode:
            # Update existing photo (reuse the one we already fetched)
            photo = existing_photo
            photo.guest_name = guest.name
            photo.wish_message = wish_message
            # Update file info only if new file was uploaded
            if unique_filename:
                photo.filename = unique_filename
                photo.original_filename = original_filename
                photo.file_size = file_size
                photo.file_type = file_type
                photo.duration = video_duration
                photo.thumbnail = thumbnail_filename
        else:
            # Create new photo record (filename can be None for wish-only submissions)
            photo = Photo(
                guest_id=guest.id,
                guest_name=guest.name,
                filename=unique_filename,  # Can be None
                original_filename=original_filename,  # Can be None
                wish_message=wish_message,
                file_size=file_size,
                file_type=file_type or 'wish',  # Set type to 'wish' if no file
                duration=video_duration,
                thumbnail=thumbnail_filename
            )
            db.session.add(photo)

        # Flush to get photo.id before creating music request
        db.session.flush()
        
        # Handle selected song if provided
        if selected_song:
            try:
                import json
                song_data = json.loads(selected_song)
                
                # Copy music file from library to project music folder
                copied_filename = None
                youtube_download_needed = False

                if song_data.get('source') == 'local':
                    try:
                        import shutil
                        from pathlib import Path
                        
                        # Get file_path from song data (should be set by search)
                        file_path = song_data.get('file_path', '')
                        title = song_data.get('title', '')
                        artist = song_data.get('artist', '')
                        
                        if file_path:
                            # Handle both absolute and relative paths
                            if file_path.startswith('/mnt/media/MUSIC'):
                                # Translate old mounted path to current music location
                                relative_path = file_path.replace('/mnt/media/MUSIC/', '')
                                library_root = Path(current_app.config['MUSIC_LIBRARY_PATH'])
                                source_path = library_root / relative_path
                            elif file_path.startswith('/mnt/pixelparty/Music'):
                                # Current mounted path - use as is
                                source_path = Path(file_path)
                            elif file_path.startswith('/'):
                                # Already absolute path
                                source_path = Path(file_path)
                            else:
                                # Relative path to music library root
                                library_root = Path(current_app.config['MUSIC_LIBRARY_PATH'])
                                source_path = library_root / file_path
                            
                            current_app.logger.info(f"MUSIC DEBUG: Attempting to copy from {source_path}")
                            
                            if source_path.exists():
                                # Create safe filename for destination
                                original_ext = source_path.suffix
                                safe_filename = f"{title}_{artist}{original_ext}".replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and')
                                
                                # Create destination path using config
                                dest_dir = Path(current_app.config['MUSIC_COPY_FOLDER'])
                                dest_dir.mkdir(parents=True, exist_ok=True)
                                dest_path = dest_dir / safe_filename
                                
                                # Copy file
                                shutil.copy2(source_path, dest_path)
                                copied_filename = safe_filename
                                current_app.logger.info(f"SUCCESS: Copied {source_path.name} -> {dest_path.name}")
                            else:
                                current_app.logger.error(f"Source file not found: {source_path}")
                                # Don't fail the entire upload, just skip the music
                                current_app.logger.warning(f"Continuing without music due to missing file")
                        else:
                            current_app.logger.error(f"No file_path provided for local song: {title} by {artist}")
                            
                    except Exception as e:
                        current_app.logger.error(f"Music copy failed: {e}")
                        # Don't fail the entire upload, just skip the music
                        current_app.logger.warning(f"Continuing without music due to error: {e}")
                        
                elif song_data.get('source') == 'youtube':
                    # Prepare YouTube download data (will start after database entry)
                    video_url = song_data.get('url', '')
                    title = song_data.get('title', '')
                    artist = song_data.get('artist', '')

                    current_app.logger.info(f"🚀 Preparing YouTube download: {title} by {artist} from {video_url}")

                    if video_url and title:
                        youtube_download_needed = True
                        youtube_data = (video_url, title, artist)
                    else:
                        current_app.logger.error(f"Missing YouTube data - URL: {bool(video_url)}, Title: {bool(title)}")
                        youtube_download_needed = False
                
                # Only create music request if we have valid data
                if song_data.get('title'):
                    # Set initial status based on source and whether we have a file
                    if song_data.get('source') == 'local':
                        status = 'ready' if copied_filename else 'error'
                    else:
                        status = 'pending'  # YouTube will be set to downloading then ready/error

                    # In edit mode, check if there's already a music request for this guest
                    # to avoid duplicates
                    if is_edit_mode:
                        existing_music = MusicQueue.query.filter_by(
                            guest_id=guest.id,
                            song_title=song_data.get('title', ''),
                            artist=song_data.get('artist', '')
                        ).first()

                        if existing_music:
                            # Update existing entry
                            music_request = existing_music
                            music_request.photo_id = photo.id  # Link to current photo
                            music_request.album = song_data.get('album', '')
                            music_request.filename = copied_filename
                            music_request.source = song_data.get('source', 'request')
                            music_request.status = status
                            # Don't add to session since it's already there
                        else:
                            # Create new entry
                            music_request = MusicQueue(
                                guest_id=guest.id,
                                photo_id=photo.id,  # Link to photo
                                song_title=song_data.get('title', ''),
                                artist=song_data.get('artist', ''),
                                album=song_data.get('album', ''),
                                filename=copied_filename,
                                source=song_data.get('source', 'request'),
                                status=status
                            )
                            db.session.add(music_request)
                    else:
                        # Create new entry for non-edit mode
                        music_request = MusicQueue(
                            guest_id=guest.id,
                            photo_id=photo.id,  # Link to photo
                            song_title=song_data.get('title', ''),
                            artist=song_data.get('artist', ''),
                            album=song_data.get('album', ''),
                            filename=copied_filename,
                            source=song_data.get('source', 'request'),
                            status=status
                        )
                        db.session.add(music_request)

                    db.session.flush()  # Get the ID without committing
                    
                    # Start YouTube download if needed (after we have the ID)
                    if youtube_download_needed:
                        try:
                            current_app.logger.info(f"🎵 Starting download thread for: {youtube_data[1]} by {youtube_data[2]} (ID: {music_request.id})")
                            download_thread = threading.Thread(
                                target=download_youtube_async,
                                args=(youtube_data[0], youtube_data[1], youtube_data[2], current_app._get_current_object(), music_request.id),
                                name=f"YouTubeDownload-{music_request.id}"
                            )
                            download_thread.daemon = True
                            download_thread.start()
                            current_app.logger.info(f"✅ Download thread started successfully for ID {music_request.id}")
                        except Exception as e:
                            current_app.logger.error(f"❌ Failed to start download thread: {e}")
                            import traceback
                            current_app.logger.error(f"❌ Thread start traceback: {traceback.format_exc()}")
                            
            except Exception as e:
                current_app.logger.error(f"Error adding selected song: {e}")

        # Update guest submission count (only for new submissions, not edits)
        if not is_edit_mode:
            guest.total_submissions += 1

        # DEBUG: Log before commit
        with open('submission_debug.log', 'a') as f:
            f.write(f"DEBUG: About to commit to database\n")
            f.write(f"Photo ID: {photo.id if hasattr(photo, 'id') else 'NEW'}\n")
            f.write(f"Guest name: {photo.guest_name}\n")
            f.write(f"Wish: {photo.wish_message}\n")
            f.write(f"Filename: {photo.filename}\n")
            f.write(f"File type: {photo.file_type}\n")

        try:
            db.session.commit()
            with open('submission_debug.log', 'a') as f:
                f.write(f"SUCCESS: Database commit successful, Photo ID: {photo.id}\n")
        except Exception as commit_error:
            with open('submission_debug.log', 'a') as f:
                f.write(f"ERROR: Database commit failed: {commit_error}\n")
            db.session.rollback()

            # WORKAROUND: Use raw SQL insert since ORM is failing
            try:
                from sqlalchemy import text
                with open('submission_debug.log', 'a') as f:
                    f.write(f"WORKAROUND: Trying raw SQL insert...\n")

                sql = text('''INSERT INTO photos
                    (guest_id, guest_name, filename, original_filename, wish_message,
                     uploaded_at, display_duration, file_size, file_type)
                    VALUES (:guest_id, :guest_name, :filename, :original_filename, :wish_message,
                            :uploaded_at, :display_duration, :file_size, :file_type)''')

                result = db.session.execute(sql, {
                    'guest_id': guest.id,
                    'guest_name': guest.name,
                    'filename': None,
                    'original_filename': None,
                    'wish_message': wish_message,
                    'uploaded_at': datetime.datetime.now(),
                    'display_duration': 10,
                    'file_size': 0,
                    'file_type': 'wish'
                })
                db.session.commit()

                with open('submission_debug.log', 'a') as f:
                    f.write(f"SUCCESS: Raw SQL insert worked!\n")

            except Exception as sql_error:
                with open('submission_debug.log', 'a') as f:
                    f.write(f"ERROR: Raw SQL also failed: {sql_error}\n")
                db.session.rollback()
                raise commit_error
        
        # Handle success differently for edit vs. new submissions
        if is_edit_mode:
            # For edit mode with HTMX, return success page but with admin redirect
            if is_htmx_request():
                # Return HTMX response that triggers redirect to admin page
                return f'''
                <script>
                    window.location.href = "{url_for('admin.manage')}";
                </script>
                <div class="alert alert-success">
                    <span>Memory updated successfully! 🎉</span>
                </div>
                '''
            else:
                # Fallback for non-HTMX edit mode
                flash('Memory updated successfully! 🎉', 'success')
                return redirect(url_for('admin.manage'))
        elif is_htmx_request():
            # For HTMX, return the success page content directly
            return render_template("mobile/success.html",
                                 guest_name=guest.name,
                                 music_added=bool(selected_song))
        else:
            # For regular form submission, redirect to success page with guest info
            return redirect(url_for('mobile.success', guest_name=guest.name, music_added=bool(selected_song)))
            
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {e}")
        error_msg = 'Sorry, there was an error uploading your memory. Please try again! 🔧'
        flash(error_msg, 'error')
        return redirect(url_for('mobile.main_form'))


@mobile_bp.route('/music')
def music():
    """Music suggestion interface."""
    if 'guest_name' not in session:
        return redirect(url_for('mobile.welcome'))
    
    return render_template('mobile/music.html', guest_name=session['guest_name'])


@mobile_bp.route('/search_music', methods=['POST'])
@guest_required
def search_music():
    """HTMX endpoint for music search with progressive loading (local/YouTube first, AI later)."""
    # No authentication required - this is a party app!

    try:
        # Handle both HTMX form data and JSON
        if request.content_type == 'application/json':
            data = request.get_json()
            search_query = data.get('query', '').strip()
        else:
            search_query = request.form.get('query', '').strip()

        if not search_query:
            if is_htmx_request():
                return '''<div class="text-sm opacity-70 p-2 text-center">
                    <svg class="w-5 h-5 mx-auto mb-1 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                    Type to search music, moods, or artists...
                </div>'''
            return jsonify({'results': []})

        # Step 1: Search local library first (up to 25 results)
        from utils.music_library import music_search

        search_results = music_search.search_all(search_query, limit=25)

        # Format local results
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                'title': result['title'],
                'artist': result['artist'],
                'album': result['album'],
                'duration': result['duration_formatted'],
                'file_path': result['file_path'],
                'source': 'local'
            })

        # Step 2: Note we need more results but will load them progressively
        target_total = 25
        local_count = len(formatted_results)

        # Step 3: Generate HTML for local/YouTube results (immediate response)
        if is_htmx_request():
            html_results = ""

            # Add local/YouTube results
            for idx, song in enumerate(formatted_results):
                import html
                title_display = html.escape(song['title'])
                artist_display = html.escape(song['artist'])
                album_display = html.escape(song.get('album', ''))

                # Alternate background colors for better distinction
                bg_class = "bg-base-200" if idx % 2 == 0 else "bg-base-300 bg-opacity-50"

                html_results += f'''
                <div class="card {bg_class} shadow-sm border border-base-300 hover:shadow-md transition-all duration-200">
                    <div class="card-body p-2">
                        <div class="flex justify-between items-center">
                            <div class="flex-1">
                                <div class="text-sm font-medium text-base-content">{title_display}</div>
                                <div class="text-xs opacity-70 mt-1">{artist_display}{' • ' + album_display if album_display else ''}</div>
                                <div class="flex items-center gap-2 mt-2">
                                    <div class="badge badge-sm {'badge-info' if song['source'] == 'local' else 'badge-error text-white'}" style="border-radius: 4px;">{'local' if song['source'] == 'local' else 'youtube'}</div>
                                    <div class="text-xs opacity-60">{song['duration']}</div>
                                </div>
                            </div>
                            <button type="button"
                                    class="btn btn-success btn-sm btn-circle ml-3 select-song-btn"
                                    data-title="{html.escape(song['title'])}"
                                    data-artist="{html.escape(song['artist'])}"
                                    data-source="{song['source']}"
                                    data-file-path="{html.escape(song.get('file_path', ''))}"
                                    data-url="{html.escape(song.get('url', ''))}">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                '''

            # Step 3.5: Add YouTube loading indicator if we need to search YouTube
            if local_count < target_total:
                html_results += '''
                <div id="youtube-loading-indicator"
                     hx-get="/mobile/search_youtube_results"
                     hx-trigger="load delay:800ms"
                     hx-target="this"
                     hx-swap="outerHTML"
                     hx-include="[name='query']"
                     hx-vals='{"existing_count": ''' + str(local_count) + '''}'>
                    <div class="text-center py-3 bg-base-200 rounded-lg mt-2">
                        <span class="loading loading-spinner loading-sm"></span>
                        <span class="text-sm opacity-70 ml-2">Searching YouTube for more songs...</span>
                    </div>
                </div>
                '''

            # Step 4: Add AI suggestions container (only for mood queries when enabled)
            from app.models import get_setting
            ai_enabled = get_setting('enable_ai_suggestions', 'true') == 'true'

            # Check if this is a mood query with debug logging
            try:
                from utils.ollama_client import OllamaClient
                ollama = OllamaClient()
                is_mood = ollama.is_mood_query(search_query)
                current_app.logger.info(f"AI Mood Detection: query='{search_query}', is_mood={is_mood}, ai_enabled={ai_enabled}")
            except Exception as e:
                current_app.logger.error(f"Error in mood detection: {e}")
                is_mood = False

            if ai_enabled and is_mood:
                current_app.logger.info(f"🤖 Adding AI suggestions container for mood query: '{search_query}'")
                # Add AI suggestions section that will load async
                html_results += f'''
                <div id="ai-suggestions-container"
                     hx-get="/mobile/search_music_ai?query={html.escape(search_query)}"
                     hx-trigger="load delay:1000ms"
                     hx-target="this"
                     hx-swap="outerHTML">
                    <div class="divider flex items-center justify-center gap-2">
                        <svg class="w-4 h-4 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423L16.5 15.75l.394 1.183a2.25 2.25 0 001.423 1.423L19.5 18.75l-1.183.394a2.25 2.25 0 00-1.423 1.423z"></path>
                        </svg>
                        <span>Mood: {html.escape(search_query.title())}</span>
                    </div>
                    <div class="text-center py-4">
                        <span class="loading loading-spinner loading-sm"></span>
                        <span class="text-sm opacity-70 ml-2">Getting AI suggestions...</span>
                    </div>
                </div>
                '''
            else:
                current_app.logger.info(f"❌ NOT adding AI suggestions: ai_enabled={ai_enabled}, is_mood={is_mood} for query '{search_query}'")

            return html_results
        else:
            # For JSON API (non-HTMX), return just the local/YouTube results
            return jsonify({'results': formatted_results})

        # Fallback if no results found at all
        if not formatted_results:
            fallback_results = [{
                'title': f'"{search_query}"',
                'artist': 'User Request',
                'album': 'Manual Search',
                'duration': '0:00',
                'source': 'request'
            }]

            if is_htmx_request():
                title_escaped = fallback_results[0]['title'].replace("'", "\\'")
                artist_escaped = fallback_results[0]['artist'].replace("'", "\\'")

                html_result = f'''
                <div class="card bg-base-200 shadow-sm border border-base-300 hover:shadow-md transition-all duration-200">
                    <div class="card-body p-3">
                        <div class="flex justify-between items-start">
                            <div class="flex-1">
                                <div class="text-sm font-medium text-base-content">{fallback_results[0]['title']}</div>
                                <div class="text-xs opacity-70 mt-1">{fallback_results[0]['artist']}</div>
                                <div class="flex items-center gap-2 mt-2">
                                    <div class="badge badge-sm badge-secondary" style="border-radius: 4px;">Manual request</div>
                                    <div class="text-xs opacity-60">{fallback_results[0]['duration']}</div>
                                </div>
                            </div>
                            <button type="button"
                                    class="btn btn-success btn-sm btn-circle ml-3 select-song-btn"
                                    data-title="{html.escape(fallback_results[0]['title'])}"
                                    data-artist="{html.escape(fallback_results[0]['artist'])}"
                                    data-source="request"
                                    data-file-path=""
                                    data-url="">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                '''
                return html_result
            else:
                return jsonify({'results': fallback_results})

    except Exception as e:
        current_app.logger.error(f"Error in music search: {e}")
        return jsonify({'results': []})


@mobile_bp.route('/search_music_ai', methods=['GET'])
def search_music_ai():
    """Async endpoint for AI music suggestions (called after main search)."""
    try:
        search_query = request.args.get('query', '').strip()
        current_app.logger.info(f"🎯 AI endpoint called with query: '{search_query}'")

        if not search_query:
            current_app.logger.warning("❌ AI endpoint: No search query provided")
            # Return empty div that disappears gracefully
            return '<div id="ai-suggestions-container" style="display: none;"></div>'

        # Check if AI suggestions are enabled
        from app.models import get_setting
        ai_enabled = get_setting('enable_ai_suggestions', 'true') == 'true'
        current_app.logger.info(f"📊 AI endpoint: ai_enabled={ai_enabled}")

        if not ai_enabled:
            current_app.logger.warning("❌ AI endpoint: AI suggestions disabled")
            # Return empty div that disappears gracefully
            return '<div id="ai-suggestions-container" style="display: none;"></div>'

        # Try to get AI suggestions from Ollama
        try:
            from utils.ollama_client import OllamaClient
            ollama = OllamaClient()

            current_app.logger.info(f"Getting AI suggestions for: '{search_query}'")

            # First check if this is actually a mood query
            is_mood = ollama.is_mood_query(search_query)
            current_app.logger.info(f"Is mood query: {is_mood}")

            if not is_mood:
                current_app.logger.info(f"'{search_query}' not detected as mood query, skipping AI suggestions")
                return '<div id="ai-suggestions-container" style="display: none;"></div>'

            ai_suggestions = ollama.get_song_suggestions(search_query)
            current_app.logger.info(f"✨ AI suggestions received: {len(ai_suggestions) if ai_suggestions else 0} suggestions")

            if ai_suggestions:
                current_app.logger.info(f"🎵 First suggestion: {ai_suggestions[0].get('title', 'N/A')} by {ai_suggestions[0].get('artist', 'N/A')}")

            if not ai_suggestions:
                current_app.logger.warning("❌ No AI suggestions returned")
                # Return message with retry button for better UX
                return f'''
                <div id="ai-suggestions-container">
                    <div class="text-center py-3">
                        <div class="text-xs opacity-70 mb-2">L'IA n'a pas pu générer de suggestions pour "{search_query}"</div>
                        <button onclick="location.reload()" class="btn btn-xs btn-outline">Réessayer</button>
                    </div>
                </div>
                '''

            # Format AI suggestions as HTML with proper container
            import html
            html_results = '<div id="ai-suggestions-container">'
            html_results += f'''
            <div class="divider flex items-center justify-center gap-2">
                <svg class="w-4 h-4 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423L16.5 15.75l.394 1.183a2.25 2.25 0 001.423 1.423L19.5 18.75l-1.183.394a2.25 2.25 0 00-1.423 1.423z"></path>
                </svg>
                <span>Mood: {html.escape(search_query.title())}</span>
            </div>
            '''

            for idx, suggestion in enumerate(ai_suggestions[:5]):  # Max 5 AI suggestions
                title_display = html.escape(suggestion.get('title', 'Unknown'))
                artist_display = html.escape(suggestion.get('artist', 'Unknown'))
                album_display = html.escape(suggestion.get('album', ''))

                # Create search query for this suggestion
                search_term = f"{suggestion.get('title', '')} {suggestion.get('artist', '')}"

                # Clean AI suggestions with gradient design - clickable to trigger search
                html_results += f'''
                <div class="card bg-gradient-to-r from-rose-50 to-pink-50 hover:from-rose-100 hover:to-pink-100 shadow-sm border border-rose-200 hover:shadow-md hover:border-rose-300 transition-all duration-300 mb-2 cursor-pointer group"
                     onclick="document.querySelector('input[name=query]').value = '{html.escape(search_term)}'; document.querySelector('input[name=query]').dispatchEvent(new Event('input'));">
                    <div class="card-body p-3">
                        <div class="flex justify-between items-center">
                            <div class="flex-1">
                                <div class="text-sm font-medium text-gray-800 group-hover:text-rose-800 transition-colors">{title_display}</div>
                                <div class="text-xs opacity-70 mt-1 text-gray-600 group-hover:text-rose-600 transition-colors">{artist_display}{' • ' + album_display if album_display else ''}</div>
                            </div>
                            <div class="flex items-center gap-1 text-rose-600 opacity-70">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423L16.5 15.75l.394 1.183a2.25 2.25 0 001.423 1.423L19.5 18.75l-1.183.394a2.25 2.25 0 00-1.423 1.423z"></path>
                                </svg>
                                <span class="text-xs font-medium">AI suggestion</span>
                            </div>
                        </div>
                    </div>
                </div>
                '''

            html_results += '</div>'
            return html_results

        except ImportError:
            current_app.logger.warning("Ollama client not available")
            return '<div id="ai-suggestions-container" style="display: none;"></div>'

        except Exception as ollama_error:
            current_app.logger.error(f"Ollama error: {ollama_error}")
            # Try to return a subtle message
            return '''
            <div id="ai-suggestions-container">
                <div class="text-xs opacity-50 text-center py-2">
                    AI suggestions temporarily unavailable
                </div>
            </div>
            '''

    except Exception as e:
        current_app.logger.error(f"Unexpected error in AI music search: {e}")
        # Always return valid HTML that won't break the page
        return '<div id="ai-suggestions-container" style="display: none;"></div>'


@mobile_bp.route('/search_youtube_results', methods=['GET'])
def search_youtube_results():
    """Progressive loading endpoint for YouTube search results."""
    try:
        search_query = request.args.get('query', '').strip()
        existing_count = int(request.args.get('existing_count', '0'))

        current_app.logger.info(f"🔍 YouTube endpoint called: query='{search_query}', existing={existing_count}")

        if not search_query:
            return '<div id="youtube-loading-indicator" style="display: none;"></div>'

        target_total = 25
        youtube_needed = target_total - existing_count

        if youtube_needed <= 0:
            return '<div id="youtube-loading-indicator" style="display: none;"></div>'

        try:
            from app.services.youtube_service import get_youtube_service
            youtube_service = get_youtube_service()

            # Search YouTube
            youtube_results = youtube_service.search_youtube(search_query, max_results=youtube_needed + 3)
            current_app.logger.info(f"📺 YouTube search returned {len(youtube_results)} results")

            if not youtube_results:
                return '''
                <div id="youtube-loading-indicator">
                    <div class="text-center py-2">
                        <span class="text-xs opacity-50">No additional results from YouTube</span>
                    </div>
                </div>
                '''

            # Format YouTube results
            html_results = '<div id="youtube-loading-indicator">'

            for idx, result in enumerate(youtube_results[:youtube_needed]):
                import html
                title_display = html.escape(result['title'])
                artist_display = html.escape(result['artist'])

                html_results += f'''
                <div class="card bg-base-200 shadow-sm border border-base-300 hover:shadow-md transition-all duration-200 mb-1">
                    <div class="card-body p-2">
                        <div class="flex justify-between items-center">
                            <div class="flex-1">
                                <div class="text-sm font-medium text-base-content">{title_display}</div>
                                <div class="text-xs opacity-70 mt-1">{artist_display}</div>
                                <div class="flex items-center gap-2 mt-2">
                                    <div class="badge badge-sm badge-error text-white" style="border-radius: 4px;">youtube</div>
                                    <div class="text-xs opacity-60">{result['duration_formatted']}</div>
                                </div>
                            </div>
                            <button type="button"
                                    class="btn btn-success btn-sm btn-circle ml-3 select-song-btn"
                                    data-title="{html.escape(result['title'])}"
                                    data-artist="{html.escape(result['artist'])}"
                                    data-source="youtube"
                                    data-file-path=""
                                    data-url="{html.escape(result['url'])}">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                '''

            html_results += '</div>'
            return html_results

        except Exception as e:
            current_app.logger.error(f"YouTube search error: {e}")
            return '''
            <div id="youtube-loading-indicator">
                <div class="text-center py-2">
                    <span class="text-xs opacity-50">YouTube search temporarily unavailable</span>
                </div>
            </div>
            '''

    except Exception as e:
        current_app.logger.error(f"Unexpected error in YouTube search: {e}")
        return '<div id="youtube-loading-indicator" style="display: none;"></div>'


@mobile_bp.route('/suggest_music', methods=['POST'])
def suggest_music():
    """Handle music suggestion with HTMX support."""
    if 'guest_id' not in session:
        if is_htmx_request():
            flash('Please enter your name first! 👋', 'error')
            return render_template('mobile/welcome.html',
                                 party_title=get_setting('party_title', 'Birthday Celebration'),
                                 host_name=get_setting('host_name', 'Birthday Star'))
        else:
            return redirect(url_for('mobile.welcome'))
    
    # Get form data
    search_type = request.form.get('search_type', 'mood')
    search_query = request.form.get('search_query', '').strip()
    
    if not search_query:
        error_msg = 'Please enter a search term! 🔍'
        if is_htmx_request():
            return render_template('mobile/music.html', 
                                 guest_name=session['guest_name'],
                                 error=error_msg)
        else:
            flash(error_msg, 'error')
            return redirect(url_for('mobile.music'))
    
    try:
        # Search music library first
        from utils.music_library import music_search
        
        if search_type == 'title':
            search_results = music_search.search_by_title(search_query, limit=1)
        elif search_type == 'artist':
            search_results = music_search.search_by_artist(search_query, limit=1)
        elif search_type == 'album':
            search_results = music_search.search_by_album(search_query, limit=1)
        else:  # mood or general search
            search_results = music_search.search_all(search_query, limit=1)
        
        # Use first result if found, otherwise create generic request
        if search_results:
            result = search_results[0]
            
            # Copy file from source library to project folder
            copied_filename = None
            file_path = result.get('file_path', '')
            
            current_app.logger.info(f"=== MUSIC COPY ATTEMPT ===")
            current_app.logger.info(f"Song: {result['title']} by {result['artist']}")
            current_app.logger.info(f"Source path from DB: {file_path}")
            
            if file_path:
                import shutil
                from pathlib import Path
                
                # Construct full source path
                library_root = Path(current_app.config['MUSIC_LIBRARY_PATH'])
                source_full_path = library_root / file_path
                
                current_app.logger.info(f"Full source path: {source_full_path}")
                
                if source_full_path.exists():
                    # Create safe destination filename
                    original_ext = source_full_path.suffix
                    copied_filename = f"{result['title']}_{result['artist']}{original_ext}".replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and')
                    
                    # Create destination path
                    dest_dir = Path(current_app.config['MUSIC_COPY_FOLDER'])
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest_full_path = dest_dir / copied_filename
                    
                    current_app.logger.info(f"Copying to: {dest_full_path}")
                    
                    # Copy file
                    try:
                        shutil.copy2(source_full_path, dest_full_path)
                        current_app.logger.info(f"SUCCESS: File copied successfully")
                        current_app.logger.info(f"File size: {dest_full_path.stat().st_size} bytes")
                    except Exception as e:
                        current_app.logger.error(f"COPY FAILED: {e}")
                        copied_filename = None
                else:
                    current_app.logger.error(f"Source file does not exist: {source_full_path}")
                    copied_filename = None
            else:
                current_app.logger.error("No file_path provided in result")
            
            music_request = MusicQueue(
                guest_id=guest.id,  # Use the guest we found/created
                song_title=result['title'],
                artist=result['artist'],
                album=result['album'],
                filename=copied_filename,  # Store the copied filename
                source="local",
                status='ready' if copied_filename else 'error'
            )
        else:
            # Create generic request for manual review
            # Note: This route might not have guest context, so we'll handle it differently
            music_request = MusicQueue(
                guest_id=None,  # Will need to handle this case in suggest_music route
                song_title=f"Request: {search_query}",
                artist=f"Search by {search_type}",
                album="User Request",
                source="request",
                status="pending"
            )
        
        db.session.add(music_request)
        db.session.commit()
        
        success_msg = f'Music suggestion "{search_query}" added to the party playlist! 🎵'
        
        if is_htmx_request():
            return render_template('mobile/music.html', 
                                 guest_name=session['guest_name'],
                                 success=success_msg)
        else:
            flash(success_msg, 'success')
            return redirect(url_for('mobile.music'))
            
    except Exception as e:
        current_app.logger.error(f"Error adding music suggestion: {e}")
        error_msg = 'Sorry, there was an error adding your music suggestion. Please try again! 🔧'
        
        if is_htmx_request():
            return render_template('mobile/music.html', 
                                 guest_name=session['guest_name'],
                                 error=error_msg)
        else:
            flash(error_msg, 'error')
            return redirect(url_for('mobile.music'))


@mobile_bp.route('/ollama_status')
def ollama_status():
    """Check if Ollama server is available."""
    try:
        import asyncio
        from utils.ollama_client import OllamaClient
        
        async def check_ollama():
            ollama = OllamaClient()
            try:
                models = await ollama.list_models()
                return models
            finally:
                await ollama.close()
        
        # Run async function synchronously
        models = asyncio.run(check_ollama())
        connected = bool(models)
        
        if is_htmx_request():
            # Return HTML for HTMX
            if connected:
                return '''
                <div class="tooltip" data-tip="🤖 Suggestions musicales IA disponibles">
                    <div class="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                '''
            else:
                return '''
                <div class="tooltip" data-tip="❌ Suggestions musicales IA indisponibles">
                    <div class="w-3 h-3 rounded-full bg-gray-500"></div>
                </div>
                '''
        else:
            return jsonify({
                'connected': connected,
                'models': models if models else []
            })
    except Exception as e:
        if is_htmx_request():
            return '''
            <div class="tooltip" data-tip="❌ Erreur de connexion IA">
                <div class="w-3 h-3 rounded-full bg-red-500"></div>
            </div>
            '''
        else:
            return jsonify({
                'connected': False,
                'error': str(e)
            })


@mobile_bp.route('/status')
def status():
    """Get guest status for HTMX polling - now session-free."""
    # Since we're session-free, this endpoint is less useful but keep for compatibility
    # Could be enhanced to take guest_name as parameter if needed
    return jsonify({
        'message': 'Session-free mode active',
        'status': 'ready'
    })

@mobile_bp.route("/success")
@guest_required
def success():
    """Success page after submission."""
    # Get guest info from URL parameters (session-free)
    guest_name = request.args.get('guest_name', '')
    music_added = request.args.get('music_added', 'False') == 'True'

    # If no guest name provided, redirect to form
    if not guest_name:
        return redirect(url_for("mobile.main_form"))

    return render_template("mobile/success.html",
                         guest_name=guest_name,
                         music_added=music_added)
@mobile_bp.route('/select_song', methods=['POST'])
def select_song():
    """HTMX endpoint to select a song and hide search field."""
    title = request.form.get('title', '').strip()
    artist = request.form.get('artist', '').strip()
    source = request.form.get('source', '').strip()
    file_path = request.form.get('file_path', '').strip()
    url = request.form.get('url', '').strip()

    if not title or not artist:
        # Return search field if invalid selection
        return render_template('partials/music_selection.html', selected_song=None)

    # Create selected song object
    selected_song = {
        'title': title,
        'artist': artist,
        'source': source,
        'file_path': file_path,
        'url': url
    }

    # Create JSON for hidden form field
    import json
    selected_song_json = json.dumps(selected_song)

    return render_template('partials/music_selection.html',
                         selected_song=selected_song,
                         selected_song_json=selected_song_json)


@mobile_bp.route('/clear_song', methods=['POST'])
def clear_song():
    """HTMX endpoint to clear selected song and show search field again."""
    return render_template('partials/music_selection.html', selected_song=None)


# Force reload
