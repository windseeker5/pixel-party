"""Admin panel routes."""

import subprocess
import threading
import time
import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from app import db
from app.models import Photo, MusicQueue, Guest, Settings, update_setting, MusicLibrary
from utils.music_library import music_search
from app.services.auth import admin_required
from app.services.file_handler import file_handler

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard."""
    stats = {
        'total_photos': Photo.query.count(),
        'total_guests': Guest.query.count(),
        'music_requests': MusicQueue.query.count(),
        'pending_photos': Photo.query.filter_by(displayed_at=None).count()
    }
    
    recent_photos = Photo.query.order_by(Photo.uploaded_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_photos=recent_photos)




# Global variable to track indexing status
indexing_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_file': '',
    'stats': {'indexed': 0, 'errors': 0, 'updated': 0}
}


@admin_bp.route('/music')
@admin_required
def music_dashboard():
    """Music library management dashboard."""
    # Get library statistics
    stats = music_search.get_library_stats()
    
    # Get recent tracks
    recent_tracks = MusicLibrary.query.order_by(MusicLibrary.indexed_at.desc()).limit(10).all()
    
    # Format tracks for display
    formatted_tracks = []
    for track in recent_tracks:
        duration_str = "0:00"
        if track.duration:
            minutes = track.duration // 60
            seconds = track.duration % 60
            duration_str = f"{minutes}:{seconds:02d}"
        
        formatted_tracks.append({
            'title': track.title or 'Unknown Title',
            'artist': track.artist or 'Unknown Artist',
            'album': track.album or '',
            'duration_formatted': duration_str,
            'indexed_at': track.indexed_at
        })
    
    return render_template('admin/music.html', 
                         stats=stats, 
                         recent_tracks=formatted_tracks,
                         indexing_status=indexing_status)


@admin_bp.route('/music/start-index', methods=['POST'])
def start_music_indexing():
    """Start music library indexing."""
    global indexing_status
    
    if indexing_status['running']:
        return jsonify({'error': 'Indexing already in progress'}), 400
    
    force = request.json.get('force', False) if request.is_json else request.form.get('force') == 'true'
    
    # Start indexing in background thread
    def run_indexing():
        global indexing_status
        try:
            indexing_status['running'] = True
            indexing_status['progress'] = 0
            indexing_status['current_file'] = 'Starting...'
            
            # Run the indexing script
            cmd = ['python', 'index_music.py']
            if force:
                cmd.append('--force')
            cmd.append('--verbose')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Parse output for progress
            for line in process.stdout:
                line = line.strip()
                if 'Found' in line and 'audio files' in line:
                    # Extract total files count
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            indexing_status['total'] = int(part)
                            break
                elif 'Processing' in line:
                    # Extract current file being processed
                    if 'Processing' in line:
                        filename = line.split('Processing ')[-1].split(']')[0]
                        indexing_status['current_file'] = filename
                elif 'New files indexed:' in line:
                    # Extract stats
                    parts = line.split(':')
                    if len(parts) > 1:
                        indexing_status['stats']['indexed'] = int(parts[1].strip())
                elif 'Files updated:' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        indexing_status['stats']['updated'] = int(parts[1].strip())
                elif 'Errors:' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        indexing_status['stats']['errors'] = int(parts[1].strip())
            
            process.wait()
            
        except Exception as e:
            indexing_status['current_file'] = f'Error: {str(e)}'
        finally:
            indexing_status['running'] = False
            indexing_status['current_file'] = 'Completed'
    
    # Start thread
    thread = threading.Thread(target=run_indexing)
    thread.daemon = True
    thread.start()
    
    flash('Music indexing started!', 'success')
    return redirect(url_for('admin.music_dashboard'))


@admin_bp.route('/music/status')
def music_indexing_status():
    """Get current indexing status."""
    return jsonify(indexing_status)


@admin_bp.route('/music/search-test', methods=['POST'])
def search_test():
    """Test music search functionality."""
    query = request.json.get('query', '') if request.is_json else request.form.get('query', '')
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    # Perform search
    results = music_search.search_all(query, limit=10)
    
    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })


@admin_bp.route('/music/clear-index', methods=['POST'])
def clear_music_index():
    """Clear the music library index."""
    try:
        # Delete all music library records
        MusicLibrary.query.delete()
        db.session.commit()
        
        flash('Music library index cleared successfully!', 'success')
    except Exception as e:
        flash(f'Error clearing index: {str(e)}', 'error')
    
    return redirect(url_for('admin.music_dashboard'))


@admin_bp.route('/export')
def memory_book():
    """Display the memory book with all photos, wishes, and music."""
    # Get all photos with their associated music
    photos = Photo.query.order_by(Photo.uploaded_at.asc()).all()
    
    # For each photo, find the associated music from the same guest at similar time
    memories = []
    for photo in photos:
        # Get music request from same guest (any time - support for edit mode)
        music = None
        if photo.guest_id:
            # Get the most recent music from this guest that's ready/completed
            music = MusicQueue.query.filter_by(guest_id=photo.guest_id)\
                .filter(MusicQueue.status.in_(['ready', 'completed']))\
                .order_by(MusicQueue.submitted_at.desc())\
                .first()

        # Get creation date from photo metadata
        photo_path = f'media/photos/{photo.filename}'
        creation_date = file_handler.get_media_creation_date(photo_path)

        memories.append({
            'photo': photo,
            'music': music,
            'creation_date': creation_date or photo.uploaded_at
        })
    
    return render_template('admin/memory_book.html', memories=memories)


@admin_bp.route('/manage')
@admin_required
def manage():
    """Admin management page to view and delete entries."""
    # Get all photos with guest info
    photos = Photo.query.order_by(Photo.uploaded_at.desc()).all()

    # Get all music queue entries with guest info
    music_entries = MusicQueue.query.order_by(MusicQueue.submitted_at.desc()).all()

    # Get all settings for the form
    all_settings = Settings.query.all()
    settings_dict = {s.key: s.value for s in all_settings}

    return render_template('admin/manage.html', photos=photos, music_entries=music_entries, settings=settings_dict)


@admin_bp.route('/manage/update_settings', methods=['POST'])
def update_settings():
    """Update settings from the manage page."""
    # Update settings
    settings_to_update = [
        'party_title', 'host_name', 'slideshow_duration',
        'max_submissions_per_guest', 'auto_play_music',
        'welcome_screen_interval_type', 'welcome_screen_interval_value',
        'welcome_screen_duration', 'enable_ai_suggestions',
        'guest_password', 'admin_password', 'external_url'
    ]

    for key in settings_to_update:
        value = request.form.get(key)
        if value is not None:
            update_setting(key, value)

    flash('Settings updated successfully!', 'success')
    return redirect(url_for('admin.manage'))


@admin_bp.route('/manage/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    """Delete a photo entry."""
    import os
    
    photo = Photo.query.get_or_404(photo_id)
    
    try:
        # Delete the physical file
        photo_path = f'media/photos/{photo.filename}'
        if os.path.exists(photo_path):
            os.remove(photo_path)
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting photo: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage'))


@admin_bp.route('/manage/delete_music/<int:music_id>', methods=['POST'])
def delete_music(music_id):
    """Delete a music entry."""
    import os
    
    music = MusicQueue.query.get_or_404(music_id)
    
    try:
        # Delete the physical file if it exists
        if music.filename:
            music_path = f'media/music/{music.filename}'
            if os.path.exists(music_path):
                os.remove(music_path)
        
        # Delete from database
        db.session.delete(music)
        db.session.commit()
        
        flash('Music entry deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting music: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage'))


@admin_bp.route('/music/retry/<int:music_id>', methods=['POST'])
@admin_required
def retry_music_download(music_id):
    """Retry downloading a failed YouTube song."""
    import threading
    from flask import current_app

    music = MusicQueue.query.get_or_404(music_id)

    if music.source != 'youtube':
        flash(f'Can only retry YouTube downloads. This is a {music.source} song.', 'error')
        return redirect(url_for('admin.manage'))

    if music.status != 'error':
        flash(f'Song is not in error state (current status: {music.status})', 'warning')
        return redirect(url_for('admin.manage'))

    try:
        # Reset status to pending and clear filename
        music.status = 'pending'
        music.filename = None
        db.session.commit()

        # Log the retry attempt
        current_app.logger.info(f"🔄 RETRY: Starting retry for music ID {music_id}: '{music.song_title}' by '{music.artist}'")
        print(f"🔄 RETRY: Starting retry for music ID {music_id}: '{music.song_title}' by '{music.artist}'")

        flash(f'Retry initiated for "{music.song_title}" by {music.artist}. Check status in a few moments.', 'info')

        # Create search query and start retry in background
        search_query = f"{music.artist} {music.song_title}"

        # Import and start the retry function immediately
        from app.services.youtube_service import get_youtube_service

        print(f"🔍 RETRY: Searching YouTube for: {search_query}")
        current_app.logger.info(f"🔍 RETRY: Searching YouTube for: {search_query}")

        # Do the search immediately to see if it works
        try:
            youtube_service = get_youtube_service()
            results = youtube_service.search_youtube(search_query, max_results=1)

            if results:
                video_url = results[0]['url']
                title = results[0]['title']
                artist = results[0]['artist']

                print(f"✅ RETRY: Found video: {video_url}")
                current_app.logger.info(f"✅ RETRY: Found video: {video_url}")

                # Now start the download thread
                from app.routes.mobile import download_youtube_async

                print(f"🚀 RETRY: Starting download thread for ID {music_id}")
                current_app.logger.info(f"🚀 RETRY: Starting download thread for ID {music_id}")

                # Start download in background thread
                retry_thread = threading.Thread(
                    target=download_youtube_async,
                    args=(video_url, title, artist, current_app._get_current_object(), music_id),
                    name=f"YouTubeRetry-{music_id}"
                )
                retry_thread.daemon = True
                retry_thread.start()

                print(f"✅ RETRY: Thread started successfully for ID {music_id}")
                current_app.logger.info(f"✅ RETRY: Thread started successfully for ID {music_id}")

            else:
                print(f"❌ RETRY: No YouTube results found for: {search_query}")
                current_app.logger.error(f"❌ RETRY: No YouTube results found for: {search_query}")
                music.status = 'error'
                db.session.commit()
                flash(f'No YouTube results found for "{music.song_title}" by {music.artist}', 'error')

        except Exception as search_error:
            print(f"❌ RETRY: Search failed: {search_error}")
            current_app.logger.error(f"❌ RETRY: Search failed: {search_error}")
            music.status = 'error'
            db.session.commit()
            flash(f'Search failed: {str(search_error)}', 'error')

    except Exception as e:
        flash(f'Error starting retry: {str(e)}', 'error')
        current_app.logger.error(f"Error in retry_music_download: {e}")

    return redirect(url_for('admin.manage'))


@admin_bp.route('/export/standalone')
def export_standalone():
    """Export standalone HTML memory book for USB."""
    import os
    import shutil
    from urllib.parse import quote
    
    # Get all photos with their associated music
    photos = Photo.query.order_by(Photo.uploaded_at.asc()).all()
    
    # Create export directory
    export_dir = 'export'
    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(f'{export_dir}/photos', exist_ok=True)
    os.makedirs(f'{export_dir}/thumbnails', exist_ok=True)
    os.makedirs(f'{export_dir}/music', exist_ok=True)
    
    # Prepare memories data and copy files
    memories = []
    for photo in photos:
        # Copy photo file
        photo_src = f'media/photos/{photo.filename}'
        photo_dest = f'{export_dir}/photos/{photo.filename}'
        if os.path.exists(photo_src):
            shutil.copy2(photo_src, photo_dest)

        # Copy video thumbnail if it exists
        if photo.file_type == 'video' and photo.thumbnail:
            thumb_src = f'media/thumbnails/{photo.thumbnail}'
            thumb_dest = f'{export_dir}/thumbnails/{photo.thumbnail}'
            if os.path.exists(thumb_src):
                shutil.copy2(thumb_src, thumb_dest)
        
        # Get associated music (any time - support for edit mode)
        music = None
        if photo.guest_id:
            # Get the most recent music from this guest that's ready/completed
            music = MusicQueue.query.filter_by(guest_id=photo.guest_id)\
                .filter(MusicQueue.status.in_(['ready', 'completed']))\
                .order_by(MusicQueue.submitted_at.desc())\
                .first()

            # Copy music file if exists, but include music info even if file is missing
            music_available = False
            if music and music.filename:
                music_src = f'media/music/{music.filename}'
                music_dest = f'{export_dir}/music/{music.filename}'
                if os.path.exists(music_src):
                    shutil.copy2(music_src, music_dest)
                    music_available = True

            # Add music availability info for template
            if music:
                music.file_available = music_available

        # Get creation date from photo metadata
        photo_path = f'media/photos/{photo.filename}'
        creation_date = file_handler.get_media_creation_date(photo_path)

        memories.append({
            'photo': photo,
            'music': music,  # Include music even if file is missing
            'creation_date': creation_date or photo.uploaded_at
        })
    
    # Generate standalone HTML
    current_date = datetime.datetime.now()
    html_content = render_template('admin/memory_book_standalone.html',
                                 memories=memories,
                                 current_date=current_date)
    
    # Save standalone HTML file
    with open(f'{export_dir}/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Copy database backup
    if os.path.exists('party.db'):
        shutil.copy2('party.db', f'{export_dir}/party_database.db')
    
    flash(f'Memory book exported to {export_dir}/ directory!', 'success')
    return redirect(url_for('admin.memory_book'))


@admin_bp.route('/reset-party', methods=['POST'])
def reset_party():
    """Reset party data using the reset_party.py script."""
    import os
    import sys

    try:
        # Get the project root directory (where the script is located)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        reset_script_path = os.path.join(project_root, 'utils', 'reset_party.py')

        # Check if the reset script exists
        if not os.path.exists(reset_script_path):
            flash('Reset script not found!', 'error')
            return redirect(url_for('admin.manage'))

        # Set up the environment to include the project root in Python path
        env = os.environ.copy()
        pythonpath = env.get('PYTHONPATH', '')
        if pythonpath:
            env['PYTHONPATH'] = f"{project_root}:{pythonpath}"
        else:
            env['PYTHONPATH'] = project_root

        # Run the reset script with --no-confirm flag
        result = subprocess.run(
            [sys.executable, reset_script_path, '--no-confirm'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            env=env
        )

        if result.returncode == 0:
            flash('Party data reset successfully! 🎉', 'success')
        else:
            error_msg = result.stderr or result.stdout or 'Unknown error occurred'
            flash(f'Reset failed: {error_msg}', 'error')

    except subprocess.TimeoutExpired:
        flash('Reset operation timed out. Please try again.', 'error')
    except Exception as e:
        flash(f'Error running reset script: {str(e)}', 'error')

    return redirect(url_for('admin.manage'))