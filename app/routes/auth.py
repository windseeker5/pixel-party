"""Authentication routes for guest and admin login."""

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.services.auth import (
    check_guest_password, check_admin_password,
    login_guest, login_admin, logout_all
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def guest_login():
    """Guest login page."""
    return render_template('auth/guest_login.html')


@auth_bp.route('/login', methods=['POST'])
def guest_login_post():
    """Handle guest login form submission."""
    password = request.form.get('password', '').strip()

    if not password:
        flash('Please enter the party password! 🎉', 'error')
        return render_template('auth/guest_login.html')

    if check_guest_password(password):
        login_guest()
        flash('Welcome to the party! 🎉', 'success')

        # Redirect to intended destination or mobile form
        redirect_url = session.pop('login_redirect', None)
        if redirect_url:
            return redirect(redirect_url)
        return redirect(url_for('mobile.main_form'))
    else:
        flash('Incorrect password. Please try again! 🔒', 'error')
        return render_template('auth/guest_login.html')


@auth_bp.route('/admin/login')
def admin_login():
    """Admin login page."""
    return render_template('auth/admin_login.html')


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login form submission."""
    password = request.form.get('password', '').strip()

    if not password:
        flash('Please enter the admin password! 🔐', 'error')
        return render_template('auth/admin_login.html')

    if check_admin_password(password):
        login_admin()
        flash('Admin access granted! ⚙️', 'success')

        # Redirect to intended destination or admin dashboard
        redirect_url = session.pop('admin_login_redirect', None)
        if redirect_url:
            return redirect(redirect_url)
        return redirect(url_for('admin.dashboard'))
    else:
        flash('Incorrect admin password. Please try again! 🔒', 'error')
        return render_template('auth/admin_login.html')


@auth_bp.route('/logout')
def logout():
    """Logout from all sessions."""
    logout_all()
    flash('You have been logged out. Thanks for celebrating! 👋', 'info')
    return redirect(url_for('auth.guest_login'))