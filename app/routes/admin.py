"""Admin panel routes."""

import subprocess
import threading
import time
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from app import db
from app.models import Photo, MusicQueue, Guest, Settings, update_setting, MusicLibrary
from utils.music_library import music_search

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
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


@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings management."""
    if request.method == 'POST':
        # Update settings
        settings_to_update = [
            'party_title', 'host_name', 'slideshow_duration', 
            'max_submissions_per_guest', 'auto_play_music'
        ]
        
        for key in settings_to_update:
            value = request.form.get(key)
            if value is not None:
                update_setting(key, value)
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    # Get all settings
    all_settings = Settings.query.all()
    settings_dict = {s.key: s.value for s in all_settings}
    
    return render_template('admin/settings.html', settings=settings_dict)


# Global variable to track indexing status
indexing_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_file': '',
    'stats': {'indexed': 0, 'errors': 0, 'updated': 0}
}


@admin_bp.route('/music')
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