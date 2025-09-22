"""Simple authentication service for PixelParty.

Provides basic password authentication for:
- Guests (mobile and big screen access)
- Admin (admin panel access)

Uses Flask sessions for authentication state.
"""

from functools import wraps
from flask import session, request, redirect, url_for, flash
from app.models import get_setting


def check_guest_password(password):
    """Check if provided password matches guest password."""
    if not password:
        return False

    guest_password = get_setting('guest_password', 'party2025')
    return password.strip() == guest_password


def check_admin_password(password):
    """Check if provided password matches admin password."""
    if not password:
        return False

    admin_password = get_setting('admin_password', 'admin2025')
    return password.strip() == admin_password


def is_guest_authenticated():
    """Check if current session has guest authentication."""
    return session.get('guest_authenticated', False)


def is_admin_authenticated():
    """Check if current session has admin authentication."""
    return session.get('admin_authenticated', False)


def login_guest():
    """Mark current session as guest authenticated."""
    session['guest_authenticated'] = True
    session.permanent = True


def login_admin():
    """Mark current session as admin authenticated."""
    session['admin_authenticated'] = True
    session.permanent = True


def logout_guest():
    """Remove guest authentication from session."""
    session.pop('guest_authenticated', None)


def logout_admin():
    """Remove admin authentication from session."""
    session.pop('admin_authenticated', None)


def logout_all():
    """Remove all authentication from session."""
    logout_guest()
    logout_admin()


def guest_required(f):
    """Decorator to require guest authentication for route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_guest_authenticated():
            # Store the intended destination
            session['login_redirect'] = request.url
            flash('Please enter the party password to continue! 🎉', 'info')
            return redirect(url_for('auth.guest_login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin authentication for route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_authenticated():
            # Store the intended destination
            session['admin_login_redirect'] = request.url
            flash('Please enter the admin password to continue! 🔐', 'info')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function