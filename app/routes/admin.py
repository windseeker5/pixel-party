"""Admin panel routes."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from app import db
from app.models import Photo, MusicQueue, Guest, Settings, update_setting

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