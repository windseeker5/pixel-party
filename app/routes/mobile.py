"""Mobile interface routes for guests with HTMX support."""

import os
import uuid
import threading
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from app import db
from app.models import Guest, Photo, MusicQueue, get_setting

mobile_bp = Blueprint('mobile', __name__)


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
    """Single screen with everything - name, photo, wish, optional music."""
    party_title = get_setting('party_title', 'Birthday Celebration')
    host_name = get_setting('host_name', 'Birthday Star')
    return render_template('mobile/main_form.html',
                         party_title=party_title,
                         host_name=host_name)


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
    """Photo upload with wish form."""
    if 'guest_name' not in session:
        return redirect(url_for('mobile.welcome'))
    
    return render_template('mobile/upload.html', 
                         guest_name=session['guest_name'])


@mobile_bp.route('/submit_memory', methods=['POST'])
def submit_memory():
    """Handle photo upload and wish submission - session-free form-based submission."""
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

    with open('submission_debug.log', 'a') as f:
        f.write(f"PASS: Guest name validation\n")

    # Always create or get guest based on form name (no session dependencies)
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
    
    if not file or file.filename == '':
        with open('submission_debug.log', 'a') as f:
            f.write(f"FAIL: File validation - file={file}, filename={file.filename if file else 'None'}\n")
        error_msg = 'Please select a photo or video to share! 📸'
        if is_htmx_request():
            return render_template('mobile/upload.html', 
                                 guest_name=session['guest_name'],
                                 error=error_msg)
        else:
            flash(error_msg, 'error')
            return redirect(url_for('mobile.upload'))
    
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
    
    if not wish_message:
        error_msg = 'Please write a birthday wish to go with your photo! 💝'
        if is_htmx_request():
            return render_template('mobile/upload.html', 
                                 guest_name=session['guest_name'],
                                 error=error_msg)
        else:
            flash(error_msg, 'error')
            return redirect(url_for('mobile.upload'))
    
    # Limit wish message to 180 characters
    if len(wish_message) > 180:
        wish_message = wish_message[:180]
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ensure upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Resize image if it's too large (for better big screen performance)
        if file.content_type and file.content_type.startswith('image/'):
            resize_image(file_path)
            # Update file size after resize
            file_size = os.path.getsize(file_path)
        
        # Create photo record
        photo = Photo(
            guest_id=guest.id,
            guest_name=guest.name,
            filename=unique_filename,
            original_filename=filename,
            wish_message=wish_message,
            file_size=file_size
        )
        
        db.session.add(photo)
        
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
                    
                    music_request = MusicQueue(
                        guest_id=guest.id,
                        song_title=song_data.get('title', ''),
                        artist=song_data.get('artist', ''),
                        album=song_data.get('album', ''),
                        filename=copied_filename,  # Store copied filename (may be None)
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
        
        # Update guest submission count
        guest.total_submissions += 1
        
        db.session.commit()
        
        # Handle HTMX requests differently than regular form submissions
        if is_htmx_request():
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
                return '<div class="text-sm opacity-70 p-2">Type to search...</div>'
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

        # Step 2: Fill remaining spots with YouTube results (if less than 25 local)
        target_total = 25
        local_count = len(formatted_results)

        if local_count < target_total:
            try:
                from app.services.youtube_service import get_youtube_service
                youtube_service = get_youtube_service()

                # Calculate how many more results we need
                youtube_needed = target_total - local_count

                # Search YouTube for music
                youtube_results = youtube_service.search_youtube(search_query, max_results=youtube_needed + 3)

                # Format YouTube results and avoid duplicates with local results
                local_song_keys = set()
                for local_result in formatted_results:
                    key = f"{local_result['title'].lower()}|||{local_result['artist'].lower()}"
                    local_song_keys.add(key)

                youtube_added = 0
                for result in youtube_results:
                    # Check if this YouTube song is already in local results
                    youtube_key = f"{result['title'].lower()}|||{result['artist'].lower()}"

                    if youtube_key not in local_song_keys and youtube_added < youtube_needed:
                        formatted_results.append({
                            'title': result['title'],
                            'artist': result['artist'],
                            'album': result.get('album', ''),
                            'duration': result['duration_formatted'],
                            'url': result['url'],  # Store YouTube URL for download
                            'source': 'youtube'
                        })
                        local_song_keys.add(youtube_key)  # Track to avoid future duplicates
                        youtube_added += 1

            except Exception as e:
                current_app.logger.error(f"YouTube search error: {e}")

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

            # Step 4: Add AI suggestions container (only for mood queries when enabled)
            from app.models import get_setting
            ai_enabled = get_setting('enable_ai_suggestions', 'true') == 'true'

            # Check if this is a mood query
            try:
                from utils.ollama_client import OllamaClient
                ollama = OllamaClient()
                is_mood = ollama.is_mood_query(search_query)
            except Exception:
                is_mood = False

            if ai_enabled and is_mood:
                # Add AI suggestions section that will load async
                html_results += f'''
                <div id="ai-suggestions-container"
                     hx-get="/mobile/search_music_ai?query={html.escape(search_query)}"
                     hx-trigger="load delay:500ms"
                     hx-target="this"
                     hx-swap="outerHTML">
                    <div class="divider">🎵 Mood detected: {html.escape(search_query.title())}</div>
                    <div class="text-center py-4">
                        <span class="loading loading-spinner loading-sm"></span>
                        <span class="text-sm opacity-70 ml-2">Getting AI suggestions...</span>
                    </div>
                </div>
                '''

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

        if not search_query:
            # Return empty div that disappears gracefully
            return '<div id="ai-suggestions-container" style="display: none;"></div>'

        # Check if AI suggestions are enabled
        from app.models import get_setting
        ai_enabled = get_setting('enable_ai_suggestions', 'true') == 'true'

        if not ai_enabled:
            # Return empty div that disappears gracefully
            return '<div id="ai-suggestions-container" style="display: none;"></div>'

        # Try to get AI suggestions from Ollama
        try:
            from utils.ollama_client import OllamaClient
            ollama = OllamaClient()

            current_app.logger.info(f"Getting AI suggestions for: {search_query}")
            ai_suggestions = ollama.get_song_suggestions(search_query)
            current_app.logger.info(f"Got {len(ai_suggestions) if ai_suggestions else 0} AI suggestions")

            if not ai_suggestions:
                # Return empty div that disappears gracefully
                return '<div id="ai-suggestions-container" style="display: none;"></div>'

            # Format AI suggestions as HTML with proper container
            html_results = '<div id="ai-suggestions-container">'
            html_results += f'<div class="divider">🎵 Mood detected: {html.escape(search_query.title())} - Click to search</div>'

            for idx, suggestion in enumerate(ai_suggestions[:5]):  # Max 5 AI suggestions
                import html
                title_display = html.escape(suggestion.get('title', 'Unknown'))
                artist_display = html.escape(suggestion.get('artist', 'Unknown'))
                album_display = html.escape(suggestion.get('album', ''))

                # Create search query for this suggestion
                search_term = f"{suggestion.get('title', '')} {suggestion.get('artist', '')}"

                # Special styling for AI suggestions - clickable to trigger search
                html_results += f'''
                <div class="card bg-purple-50 shadow-sm border border-purple-200 hover:shadow-md transition-all duration-200 mb-2 cursor-pointer"
                     onclick="document.querySelector('input[name=query]').value = '{html.escape(search_term)}'; document.querySelector('input[name=query]').dispatchEvent(new Event('input'));">
                    <div class="card-body p-3">
                        <div class="flex justify-between items-center">
                            <div class="flex-1">
                                <div class="text-sm font-medium text-purple-800">{title_display}</div>
                                <div class="text-xs opacity-70 mt-1 text-purple-600">{artist_display}{' • ' + album_display if album_display else ''}</div>
                                <div class="flex items-center gap-2 mt-2">
                                    <div class="badge badge-sm bg-purple-500 text-white" style="border-radius: 4px;">🤖 AI</div>
                                    <div class="text-xs opacity-60">Click to search</div>
                                </div>
                            </div>
                            <div class="text-purple-400">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                </svg>
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
                <div class="tooltip" data-tip="🤖 AI music suggestions available">
                    <div class="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                '''
            else:
                return '''
                <div class="tooltip" data-tip="❌ AI music suggestions unavailable">
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
            <div class="tooltip" data-tip="❌ AI connection error">
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
