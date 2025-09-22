"""Routes package."""

from flask import Blueprint, redirect, url_for, send_file, current_app, abort
from pathlib import Path
import mimetypes

# Main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to login page."""
    return redirect(url_for('auth.guest_login'))


@main_bp.route('/media/music/<filename>')
def serve_music_file(filename):
    """Serve music files from the copied music folder."""
    try:
        music_folder = Path(current_app.config['MUSIC_COPY_FOLDER'])
        file_path = music_folder / filename
        
        if not file_path.exists():
            current_app.logger.error(f"Music file not found: {file_path}")
            abort(404)
        
        # Set proper MIME type for audio streaming
        mimetype, _ = mimetypes.guess_type(str(file_path))
        if mimetype is None:
            mimetype = 'audio/mpeg'  # Default to MP3
            
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=False,
            conditional=True  # Enable range requests for streaming
        )
        
    except Exception as e:
        # Don't catch HTTP exceptions (like 404)
        if hasattr(e, 'code'):
            raise e
        current_app.logger.error(f"Error serving music file {filename}: {e}")
        abort(500)


@main_bp.route('/media/photos/<filename>')
def serve_media_file(filename):
    """Serve photo and video files from the uploads folder."""
    try:
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        file_path = upload_folder / filename

        if not file_path.exists():
            current_app.logger.error(f"Media file not found: {file_path}")
            abort(404)

        # Set proper MIME type for images and videos
        mimetype, _ = mimetypes.guess_type(str(file_path))

        # Set default MIME types based on file extension
        if mimetype is None:
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                mimetype = 'image/jpeg'
            elif ext in ['.png']:
                mimetype = 'image/png'
            elif ext in ['.gif']:
                mimetype = 'image/gif'
            elif ext in ['.webp']:
                mimetype = 'image/webp'
            elif ext in ['.mp4']:
                mimetype = 'video/mp4'
            elif ext in ['.mov']:
                mimetype = 'video/quicktime'
            elif ext in ['.avi']:
                mimetype = 'video/x-msvideo'
            elif ext in ['.mkv']:
                mimetype = 'video/x-matroska'
            elif ext in ['.webm']:
                mimetype = 'video/webm'
            else:
                mimetype = 'application/octet-stream'

        # Enable range requests for video streaming
        is_video = mimetype.startswith('video/')

        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=False,
            conditional=is_video  # Enable range requests for videos
        )

    except Exception as e:
        # Don't catch HTTP exceptions (like 404)
        if hasattr(e, 'code'):
            raise e
        current_app.logger.error(f"Error serving media file {filename}: {e}")
        abort(500)