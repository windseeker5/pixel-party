"""API routes for HTMX interactions."""

from flask import Blueprint, render_template, jsonify, request, current_app
from app.models import Photo, MusicQueue, get_setting
from app import db
from datetime import datetime
from pathlib import Path
from app.utils.network_utils import get_network_ip, get_server_url

api_bp = Blueprint('api', __name__)


@api_bp.route('/current_photo')
def current_photo():
    """Get current photo for slideshow with cycling."""
    import time
    
    photos = Photo.query.order_by(Photo.uploaded_at.asc()).all()
    
    if not photos:
        return render_template('components/no_photos.html')
    
    # Simple cycling: use timestamp to cycle through photos every 8 seconds
    current_time = int(time.time())
    slideshow_duration = 8  # seconds per photo
    photo_index = (current_time // slideshow_duration) % len(photos)
    photo = photos[photo_index]
    
    return render_template('components/photo_display.html', photo=photo)


@api_bp.route('/photos')
def photos():
    """Get photos for slideshow."""
    photos = Photo.query.order_by(Photo.uploaded_at.desc()).limit(20).all()
    
    if photos:
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
        return jsonify({'photos': photo_data})
    
    return jsonify({'photos': []})


@api_bp.route('/photo_queue')
@api_bp.route('/photos/queue')
def photo_queue():
    """Get photo queue for sidebar with currently displaying photo first."""
    import time
    
    # Get all photos in the same order as slideshow (oldest first)
    all_photos = Photo.query.order_by(Photo.uploaded_at.asc()).all()
    
    if not all_photos:
        return render_template('components/photo_queue.html', photos=[])
    
    # Calculate which photo is currently being displayed (same logic as current_photo)
    current_time = int(time.time())
    slideshow_duration = 8  # seconds per photo
    current_index = (current_time // slideshow_duration) % len(all_photos)
    
    # Reorder photos so current photo is first, then the next ones in sequence
    reordered_photos = []
    for i in range(min(6, len(all_photos))):  # Show up to 6 photos
        photo_index = (current_index + i) % len(all_photos)
        reordered_photos.append(all_photos[photo_index])
    
    return render_template('components/photo_queue.html', photos=reordered_photos)


@api_bp.route('/music_queue')
@api_bp.route('/music/queue')
def music_queue():
    """Get music queue for sidebar (excluding currently playing song)."""
    from app.models import Guest
    
    # Get all unplayed songs in order
    all_songs = MusicQueue.query.filter_by(played_at=None).order_by(MusicQueue.submitted_at.asc()).all()
    
    # Exclude the currently playing song (first ready song with filename)
    queue = []
    found_current = False
    for song in all_songs:
        # Skip the first ready song with filename (this is the currently playing one)
        if not found_current and song.status == 'ready' and song.filename:
            found_current = True
            continue
        queue.append(song)
        # Limit to 3 songs as requested
        if len(queue) >= 3:
            break
    
    # Get guest names for each song
    for song in queue:
        if song.guest_id:
            guest = Guest.query.get(song.guest_id)
            if guest:
                song.guest_name = guest.name
            else:
                song.guest_name = "Unknown Guest"
        else:
            song.guest_name = "Anonymous"
    
    return render_template('components/music_queue.html', music_queue=queue)


@api_bp.route('/stats')
def stats():
    """Get party statistics."""
    from app.models import Guest
    
    stats = {
        'photos': Photo.query.count(),
        'guests': Guest.query.count(),
        'music_requests': MusicQueue.query.count(),
        'party_title': get_setting('party_title', 'Birthday Celebration')
    }
    
    return jsonify(stats)


@api_bp.route('/network_info')
def network_info():
    """Get network information for QR code generation."""
    port = request.environ.get('SERVER_PORT', 5000)
    network_ip = get_network_ip()
    mobile_url = f"http://{network_ip}:{port}/mobile"
    
    return jsonify({
        'network_ip': network_ip,
        'mobile_url': mobile_url,
        'port': port
    })


@api_bp.route('/reset_test_data', methods=['POST'])
def reset_test_data():
    """Reset test data - clear photos and music queue."""
    try:
        from app import db
        from app.models import Guest
        
        # Delete all photos
        Photo.query.delete()
        
        # Delete all music queue entries
        MusicQueue.query.delete()
        
        # Reset guest submission counts but keep guests
        guests = Guest.query.all()
        for guest in guests:
            guest.total_submissions = 0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Test data cleared - photos and music queue reset'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@api_bp.route('/music/current')
def get_current_song():
    """Get currently playing song (only ready songs with files)."""
    from app.models import Guest
    
    # Get the first ready song that hasn't been played yet
    current_song = MusicQueue.query.filter_by(
        played_at=None, 
        status='ready'
    ).filter(
        MusicQueue.filename.isnot(None)
    ).order_by(MusicQueue.submitted_at.asc()).first()
    
    if current_song and current_song.filename:
        # Get guest information
        guest_name = "Anonymous"
        if current_song.guest_id:
            guest = Guest.query.get(current_song.guest_id)
            if guest:
                guest_name = guest.name
        
        # Construct file URL
        file_url = f"/media/music/{current_song.filename}"
        
        return jsonify({
            'id': current_song.id,
            'title': current_song.song_title,
            'artist': current_song.artist,
            'album': current_song.album,
            'file_url': file_url,
            'source': current_song.source,
            'status': current_song.status,
            'guest_name': guest_name,
            'submitted_at': current_song.submitted_at.isoformat() if current_song.submitted_at else None
        })
    
    return jsonify({'error': 'No ready song available'})


@api_bp.route('/music/next', methods=['POST'])
def next_song():
    """Mark current song as played and get next ready song."""
    from app.models import Guest
    
    # Mark current ready song as played
    current_song = MusicQueue.query.filter_by(
        played_at=None, 
        status='ready'
    ).filter(
        MusicQueue.filename.isnot(None)
    ).order_by(MusicQueue.submitted_at.asc()).first()
    
    if current_song:
        current_song.played_at = datetime.utcnow()
        db.session.commit()
    
    # Get next ready song
    next_song = MusicQueue.query.filter_by(
        played_at=None, 
        status='ready'
    ).filter(
        MusicQueue.filename.isnot(None)
    ).order_by(MusicQueue.submitted_at.asc()).first()
    
    if next_song and next_song.filename:
        # Get guest information
        guest_name = "Anonymous"
        if next_song.guest_id:
            guest = Guest.query.get(next_song.guest_id)
            if guest:
                guest_name = guest.name
        
        file_url = f"/media/music/{next_song.filename}"
        
        return jsonify({
            'id': next_song.id,
            'title': next_song.song_title,
            'artist': next_song.artist,
            'album': next_song.album,
            'file_url': file_url,
            'source': next_song.source,
            'status': next_song.status,
            'guest_name': guest_name,
            'submitted_at': next_song.submitted_at.isoformat() if next_song.submitted_at else None
        })
    
    return jsonify({'error': 'No next ready song available'})


@api_bp.route('/music/previous', methods=['POST'])  
def previous_song():
    """Get previous song (last played ready song)."""
    from app.models import Guest
    
    # Get the most recently played ready song with a file
    previous_song = MusicQueue.query.filter(
        MusicQueue.played_at.is_not(None),
        MusicQueue.status == 'ready'
    ).filter(
        MusicQueue.filename.isnot(None)
    ).order_by(MusicQueue.played_at.desc()).first()
    
    if previous_song and previous_song.filename:
        # Mark it as unplayed so it can be played again
        previous_song.played_at = None
        db.session.commit()
        
        # Get guest information
        guest_name = "Anonymous"
        if previous_song.guest_id:
            guest = Guest.query.get(previous_song.guest_id)
            if guest:
                guest_name = guest.name
        
        file_url = f"/media/music/{previous_song.filename}"
        
        return jsonify({
            'id': previous_song.id,
            'title': previous_song.song_title,
            'artist': previous_song.artist,
            'album': previous_song.album,
            'file_url': file_url,
            'source': previous_song.source,
            'status': previous_song.status,
            'guest_name': guest_name,
            'submitted_at': previous_song.submitted_at.isoformat() if previous_song.submitted_at else None
        })
    
    return jsonify({'error': 'No previous ready song available'})


@api_bp.route('/music/play/<int:song_id>', methods=['POST'])
def play_song(song_id):
    """Play a specific song by ID (only if ready)."""
    song = MusicQueue.query.get_or_404(song_id)
    
    if song.filename and song.status == 'ready':
        file_url = f"/media/music/{song.filename}"
        
        return jsonify({
            'id': song.id,
            'title': song.song_title,
            'artist': song.artist,
            'album': song.album,
            'file_url': file_url,
            'source': song.source,
            'status': song.status,
            'submitted_at': song.submitted_at.isoformat() if song.submitted_at else None
        })
    
    return jsonify({'error': 'Song file not ready or not available'})