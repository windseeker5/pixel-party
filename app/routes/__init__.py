"""Routes package."""

from flask import Blueprint, redirect, url_for, send_file, current_app, abort
from pathlib import Path
import mimetypes

# Main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Show big screen display."""
    return redirect(url_for('big_screen.big_screen'))


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
def serve_photo_file(filename):
    """Serve photo files from the uploads folder."""
    try:
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        file_path = upload_folder / filename
        
        if not file_path.exists():
            current_app.logger.error(f"Photo file not found: {file_path}")
            abort(404)
        
        # Set proper MIME type for images
        mimetype, _ = mimetypes.guess_type(str(file_path))
        if mimetype is None:
            mimetype = 'image/jpeg'  # Default to JPEG
            
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=False
        )
        
    except Exception as e:
        # Don't catch HTTP exceptions (like 404)
        if hasattr(e, 'code'):
            raise e
        current_app.logger.error(f"Error serving photo file {filename}: {e}")
        abort(500)