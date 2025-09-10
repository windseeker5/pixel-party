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


def download_youtube_async(video_url, title, artist, app):
    """Download YouTube audio in background thread."""
    with app.app_context():
        try:
            from app.services.youtube_service import get_youtube_service
            youtube_service = get_youtube_service()
            
            current_app.logger.info(f"🎵 Background downloading: {title} by {artist}")
            copied_filename = youtube_service.download_audio(video_url, title, artist)
            
            if copied_filename:
                current_app.logger.info(f"✅ Background download complete: {copied_filename}")
                # TODO: Add to music queue database here if needed
            else:
                current_app.logger.error(f"❌ Background download failed: {video_url}")
                
        except Exception as e:
            current_app.logger.error(f"❌ Background YouTube download error: {e}")


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
    # Get existing guest name if available
    guest_name = session.get('guest_name', '')
    
    party_title = get_setting('party_title', 'Birthday Celebration')
    host_name = get_setting('host_name', 'Birthday Star')
    return render_template('mobile/main_form.html', 
                         guest_name=guest_name,
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
    
    # Create or get guest
    session_id = str(uuid.uuid4())
    guest = Guest.query.filter_by(name=guest_name).first()
    
    if not guest:
        guest = Guest(name=guest_name, session_id=session_id)
        db.session.add(guest)
        db.session.commit()
    
    # Store in session
    session['guest_id'] = guest.id
    session['guest_name'] = guest.name
    session['session_id'] = guest.session_id
    
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
    """Handle photo upload and wish submission - creates guest if needed."""
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
    
    # Create or get guest if not in session
    if 'guest_id' not in session:
        session_id = str(uuid.uuid4())
        guest = Guest.query.filter_by(name=guest_name).first()
        
        if not guest:
            guest = Guest(name=guest_name, session_id=session_id)
            db.session.add(guest)
            db.session.commit()
        
        # Store in session
        session['guest_id'] = guest.id
        session['guest_name'] = guest.name
        session['session_id'] = guest.session_id
    
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
                        else:
                            current_app.logger.error(f"No file_path provided for local song: {title} by {artist}")
                            
                    except Exception as e:
                        current_app.logger.error(f"Music copy failed: {e}")
                        
                elif song_data.get('source') == 'youtube':
                    # Start YouTube download in background
                    try:
                        video_url = song_data.get('url', '')
                        title = song_data.get('title', '')
                        artist = song_data.get('artist', '')
                        
                        current_app.logger.info(f"🚀 Starting background YouTube download: {title} by {artist}")
                        
                        if video_url and title:
                            # Start download in background thread
                            download_thread = threading.Thread(
                                target=download_youtube_async,
                                args=(video_url, title, artist, current_app._get_current_object())
                            )
                            download_thread.daemon = True
                            download_thread.start()
                            
                            current_app.logger.info(f"✅ Background download started for: {title} by {artist}")
                        else:
                            current_app.logger.error(f"Missing YouTube URL or title for download")
                            
                    except Exception as e:
                        current_app.logger.error(f"Failed to start YouTube download: {e}")
                
                music_request = MusicQueue(
                    guest_id=guest.id,
                    song_title=song_data.get('title', ''),
                    artist=song_data.get('artist', ''),
                    album=song_data.get('album', ''),
                    filename=copied_filename,  # Store copied filename
                    source=song_data.get('source', 'request')
                )
                db.session.add(music_request)
            except Exception as e:
                current_app.logger.error(f"Error adding selected song: {e}")
        
        # Update guest submission count
        guest.total_submissions += 1
        
        db.session.commit()
        
        # Store success info in session for redirect
        session['last_submission_success'] = True
        session['last_submission_music_added'] = bool(selected_song)
        
        # Handle HTMX requests differently than regular form submissions
        if is_htmx_request():
            # For HTMX, return the success page content directly
            return render_template("mobile/success.html", 
                                 guest_name=guest.name,
                                 music_added=bool(selected_song))
        else:
            # For regular form submission, redirect to success page
            return redirect(url_for('mobile.success'))
            
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
    """HTMX endpoint for music search."""
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
        
        # Search music library first
        from utils.music_library import music_search
        
        # Try different search types - search for "Bob Dylan" should find Bob Dylan songs!
        search_results = music_search.search_all(search_query, limit=10)
        
        # Format results properly
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
        
        # Always try to reach 10 total suggestions by adding YouTube results
        target_total = 10
        local_count = len(formatted_results)
        
        if local_count < target_total:
            try:
                from app.services.youtube_service import get_youtube_service
                youtube_service = get_youtube_service()
                
                # Calculate how many more results we need
                youtube_needed = target_total - local_count
                
                # Search YouTube for music (get more than needed in case of duplicates)
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
        
        # Return results (local or YouTube)
        if formatted_results:
            if is_htmx_request():
                # Return HTML for HTMX
                html_results = ""
                for song in formatted_results:
                    # Use HTML escaping for display
                    import html
                    title_display = html.escape(song['title'])
                    artist_display = html.escape(song['artist'])
                    album_display = html.escape(song.get('album', ''))
                    
                    html_results += f'''
                    <div class="card bg-base-200 shadow-sm border border-base-300 hover:shadow-md transition-all duration-200">
                        <div class="card-body p-3">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <div class="text-sm font-medium text-base-content">{title_display}</div>
                                    <div class="text-xs opacity-70 mt-1">{artist_display}{' • ' + album_display if album_display else ''}</div>
                                    <div class="flex items-center gap-2 mt-2">
                                        <div class="badge badge-xs {'badge-success' if song['source'] == 'local' else 'badge-info'}">{song['source']}</div>
                                        <div class="text-xs opacity-60">{song['duration']}</div>
                                    </div>
                                </div>
                                <button type="button" 
                                        class="btn btn-primary btn-sm ml-3 select-song-btn"
                                        data-title="{html.escape(song['title'])}"
                                        data-artist="{html.escape(song['artist'])}"
                                        data-source="{song['source']}"
                                        data-file-path="{html.escape(song.get('file_path', ''))}"
                                        data-url="{html.escape(song.get('url', ''))}">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                                    </svg>
                                    Select
                                </button>
                            </div>
                        </div>
                    </div>
                    '''
                return html_results
            else:
                return jsonify({'results': formatted_results})
            
        # If no local results, use Ollama for mood-based suggestions
        try:
            from utils.ollama_client import OllamaClient
            ollama = OllamaClient()
            
            # Get AI suggestions
            ai_suggestions = ollama.get_song_suggestions(search_query)
            ollama_results = [
                {
                    'title': suggestion.get('title', search_query),
                    'artist': suggestion.get('artist', 'Various Artists'),
                    'album': suggestion.get('album', ''),
                    'duration': '0:00',
                    'source': 'ai_suggestion'
                }
                for suggestion in ai_suggestions[:3]
            ]
            
            if ollama_results:
                if is_htmx_request():
                    # Return HTML for HTMX
                    html_results = ""
                    for song in ollama_results:
                        title_escaped = song['title'].replace("'", "\\'")
                        artist_escaped = song['artist'].replace("'", "\\'")
                        
                        html_results += f'''
                        <div class="card bg-base-200 shadow-sm border border-base-300 hover:shadow-md transition-all duration-200">
                            <div class="card-body p-3">
                                <div class="flex justify-between items-start">
                                    <div class="flex-1">
                                        <div class="text-sm font-medium text-base-content">{song['title']}</div>
                                        <div class="text-xs opacity-70 mt-1">{song['artist']}{' • ' + song['album'] if song['album'] else ''}</div>
                                        <div class="flex items-center gap-2 mt-2">
                                            <div class="badge badge-xs badge-warning">AI suggestion</div>
                                            <div class="text-xs opacity-60">{song['duration']}</div>
                                        </div>
                                    </div>
                                    <button type="button" 
                                            class="btn btn-primary btn-sm ml-3"
                                            onclick="selectSong('{title_escaped}', '{artist_escaped}', '{song['source']}', '')">
                                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                                        </svg>
                                        Select
                                    </button>
                                </div>
                            </div>
                        </div>
                        '''
                    return html_results
                else:
                    return jsonify({'results': ollama_results})
                
        except Exception as e:
            current_app.logger.error(f"Ollama search error: {e}")
        
        # Fallback to generic suggestion
        fallback_results = [{
            'title': f'"{search_query}"',
            'artist': 'User Request', 
            'album': 'Manual Search',
            'duration': '0:00',
            'source': 'request'
        }]
        
        if is_htmx_request():
            # Return HTML for fallback
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
                                <div class="badge badge-xs badge-secondary">Manual request</div>
                                <div class="text-xs opacity-60">{fallback_results[0]['duration']}</div>
                            </div>
                        </div>
                        <button type="button" 
                                class="btn btn-primary btn-sm ml-3"
                                onclick="selectSong('{title_escaped}', '{artist_escaped}', 'request', '')">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                            </svg>
                            Select
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
                guest_id=session['guest_id'],
                song_title=result['title'],
                artist=result['artist'],
                album=result['album'],
                filename=copied_filename,  # Store the copied filename
                source="local"
            )
        else:
            # Create generic request for manual review
            music_request = MusicQueue(
                guest_id=session['guest_id'],
                song_title=f"Request: {search_query}",
                artist=f"Search by {search_type}",
                album="User Request",
                source="request"
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
    """Get guest status for HTMX polling."""
    if 'guest_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    guest = Guest.query.get(session['guest_id'])
    if not guest:
        return jsonify({'error': 'Guest not found'})
    
    # Get recent submissions
    recent_photos = Photo.query.filter_by(guest_id=guest.id).order_by(Photo.uploaded_at.desc()).limit(3).all()
    recent_music = MusicQueue.query.filter_by(guest_id=guest.id).order_by(MusicQueue.submitted_at.desc()).limit(3).all()
    
    return jsonify({
        'guest_name': guest.name,
        'total_submissions': guest.total_submissions,
        'recent_photos': len(recent_photos),
        'recent_music': len(recent_music)
    })

@mobile_bp.route("/success")
def success():
    """Success page after submission."""
    if "guest_name" not in session:
        return redirect(url_for("mobile.main_form"))
    
    # Get success info from session (default to False if not set)
    music_added = session.pop('last_submission_music_added', False)
    submission_success = session.pop('last_submission_success', False)
    
    # If no recent successful submission, redirect to form
    if not submission_success:
        return redirect(url_for("mobile.main_form"))
    
    return render_template("mobile/success.html", 
                         guest_name=session["guest_name"],
                         music_added=music_added)
