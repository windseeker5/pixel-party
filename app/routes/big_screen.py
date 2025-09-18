"""Big screen display routes for photo slideshow and music management."""

import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, current_app
from app.models import Photo, MusicQueue, MusicLibrary, get_setting, update_setting
from utils.music_library import music_search

big_screen_bp = Blueprint('big_screen', __name__)


@big_screen_bp.route('/')
def big_screen():
    """Main big screen display interface."""
    return render_template('big_screen/display.html')


@big_screen_bp.route('/slideshow')
def slideshow():
    """Full screen slideshow with TikTok-style text animations."""
    party_title = get_setting('party_title', 'Birthday Celebration')
    host_name = get_setting('host_name', 'Birthday Star')
    slideshow_duration = int(get_setting('slideshow_duration', 8))
    
    return render_template('big_screen/slideshow.html', 
                         party_title=party_title,
                         host_name=host_name,
                         slideshow_duration=slideshow_duration)


@big_screen_bp.route('/api/photos')
def get_photos():
    """API endpoint to get photos for slideshow with HTMX support."""
    # Get photos that haven't been displayed recently (last 30 minutes)
    recent_cutoff = datetime.utcnow() - timedelta(minutes=30)
    
    photos = Photo.query.filter(
        (Photo.displayed_at.is_(None)) | 
        (Photo.displayed_at < recent_cutoff)
    ).order_by(Photo.uploaded_at.desc()).limit(20).all()
    
    photo_data = []
    for photo in photos:
        photo_data.append({
            'id': photo.id,
            'filename': photo.filename,
            'guest_name': photo.guest_name,
            'wish_message': photo.wish_message,
            'uploaded_at': photo.uploaded_at.isoformat(),
            'url': f"/media/photos/{photo.filename}"
        })
    
    # If HTMX request, return partial template
    if request.headers.get('HX-Request') == 'true':
        return render_template('big_screen/photo_slide.html', photos=photo_data)
    
    return jsonify({'photos': photo_data})


@big_screen_bp.route('/api/photos/<int:photo_id>/displayed', methods=['POST'])
def mark_photo_displayed(photo_id):
    """Mark a photo as displayed."""
    photo = Photo.query.get_or_404(photo_id)
    photo.displayed_at = datetime.utcnow()
    
    from app import db
    db.session.commit()
    
    return jsonify({'success': True})


@big_screen_bp.route('/api/music/search')
def search_music():
    """Search music library for big screen music selection."""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    limit = int(request.args.get('limit', 20))
    
    if not query:
        # Return random tracks if no query
        results = music_search.get_random_tracks(limit)
    else:
        if search_type == 'title':
            results = music_search.search_by_title(query, limit)
        elif search_type == 'artist':
            results = music_search.search_by_artist(query, limit)
        elif search_type == 'album':
            results = music_search.search_by_album(query, limit)
        else:
            results = music_search.search_all(query, limit)
    
    return jsonify({'results': results})


@big_screen_bp.route('/api/music/queue')
def get_music_queue():
    """Get current music queue."""
    queue = MusicQueue.query.filter(
        MusicQueue.played_at.is_(None),
        MusicQueue.status == 'ready'
    ).order_by(MusicQueue.submitted_at.asc()).limit(10).all()
    
    queue_data = []
    for item in queue:
        queue_data.append({
            'id': item.id,
            'song_title': item.song_title,
            'artist': item.artist,
            'album': item.album,
            'source': item.source,
            'submitted_at': item.submitted_at.isoformat() if item.submitted_at else None
        })
    
    return jsonify({'queue': queue_data})


@big_screen_bp.route('/api/music/queue/<int:queue_id>/played', methods=['POST'])
def mark_music_played(queue_id):
    """Mark a music item as played."""
    queue_item = MusicQueue.query.get_or_404(queue_id)
    queue_item.played_at = datetime.utcnow()
    
    from app import db
    db.session.commit()
    
    return jsonify({'success': True})


@big_screen_bp.route('/api/settings')
def get_settings():
    """Get display settings for big screen."""
    settings = {
        'slideshow_duration': int(get_setting('slideshow_duration', 8)),
        'auto_play_music': get_setting('auto_play_music', 'true') == 'true',
        'party_title': get_setting('party_title', '50th Birthday Celebration'),
        'host_name': get_setting('host_name', 'Birthday Star')
    }
    
    return jsonify(settings)


@big_screen_bp.route('/api/settings', methods=['POST'])
def update_settings():
    """Update display settings."""
    data = request.get_json()
    
    if 'slideshow_duration' in data:
        update_setting('slideshow_duration', str(data['slideshow_duration']))
    
    if 'auto_play_music' in data:
        update_setting('auto_play_music', 'true' if data['auto_play_music'] else 'false')
    
    return jsonify({'success': True})


@big_screen_bp.route('/api/stats')
def get_stats():
    """Get party statistics for big screen."""
    from app.models import Guest
    
    total_photos = Photo.query.count()
    total_music_requests = MusicQueue.query.count()
    total_guests = Guest.query.count()
    
    # Get music library stats
    music_stats = music_search.get_library_stats()
    
    return jsonify({
        'photos': total_photos,
        'music_requests': total_music_requests,
        'guests': total_guests,
        'music_library': music_stats
    })