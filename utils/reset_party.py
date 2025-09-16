#!/usr/bin/env python3
"""
PixelParty Party Reset Script

Cleans database and media files for party reset while preserving:
- Music library index 
- App settings
- Directory structure

Usage:
    python reset_party.py                  # Interactive mode with confirmation
    python reset_party.py --dry-run        # Show what would be deleted
    python reset_party.py --no-confirm     # Skip confirmation prompt
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

def setup_app_context():
    """Set up Flask app context for database operations."""
    try:
        from app import create_app, db
        from app.models import Guest, Photo, MusicQueue, MusicLibrary, Settings
        
        app = create_app()
        app.app_context().push()
        
        return app, db, {
            'Guest': Guest,
            'Photo': Photo, 
            'MusicQueue': MusicQueue,
            'MusicLibrary': MusicLibrary,
            'Settings': Settings
        }
    except ImportError as e:
        print(f"❌ Error importing Flask app: {e}")
        print("Make sure you're running this script from the PixelParty directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error setting up app context: {e}")
        sys.exit(1)

def get_current_state(db, models):
    """Get current database and file counts."""
    try:
        state = {
            'database': {
                'guests': models['Guest'].query.count(),
                'photos': models['Photo'].query.count(),
                'music_queue': models['MusicQueue'].query.count(),
                'music_library': models['MusicLibrary'].query.count(),
                'settings': models['Settings'].query.count()
            },
            'files': {}
        }
        
        # Count files in media directories
        media_dirs = ['media/photos', 'media/videos', 'media/music']
        for dir_path in media_dirs:
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                state['files'][dir_path] = len(files)
            else:
                state['files'][dir_path] = 0
                
        return state
    except Exception as e:
        print(f"❌ Error getting current state: {e}")
        return None

def clean_database_tables(db, models, dry_run=False):
    """Clean specified database tables."""
    results = {}
    tables_to_clean = ['Guest', 'Photo', 'MusicQueue']
    
    for table_name in tables_to_clean:
        try:
            model = models[table_name]
            count = model.query.count()
            
            if dry_run:
                results[table_name] = {'count': count, 'status': 'would_delete', 'error': None}
            else:
                if count > 0:
                    model.query.delete()
                    db.session.commit()
                    print(f"✅ Deleted {count} records from {table_name.lower()} table")
                else:
                    print(f"ℹ️  {table_name.lower()} table was already empty")
                results[table_name] = {'count': count, 'status': 'deleted', 'error': None}
                
        except Exception as e:
            error_msg = f"Error cleaning {table_name.lower()} table: {e}"
            print(f"❌ {error_msg}")
            results[table_name] = {'count': 0, 'status': 'error', 'error': error_msg}
            if not dry_run:
                db.session.rollback()
    
    return results

def clean_media_directories(dry_run=False):
    """Clean files from media directories."""
    results = {}
    directories = ['media/photos', 'media/videos', 'media/music']
    
    for dir_path in directories:
        try:
            if not os.path.exists(dir_path):
                print(f"ℹ️  Directory {dir_path} doesn't exist, creating it...")
                if not dry_run:
                    os.makedirs(dir_path, exist_ok=True)
                results[dir_path] = {'count': 0, 'status': 'created', 'error': None}
                continue
            
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
            file_count = len(files)
            
            if dry_run:
                if file_count > 0:
                    print(f"🔍 Would delete {file_count} files from {dir_path}/")
                    for file in files[:5]:  # Show first 5 files
                        print(f"    - {file}")
                    if file_count > 5:
                        print(f"    ... and {file_count - 5} more files")
                else:
                    print(f"ℹ️  {dir_path}/ is already empty")
                results[dir_path] = {'count': file_count, 'status': 'would_delete', 'error': None}
            else:
                if file_count > 0:
                    for file in files:
                        file_path = os.path.join(dir_path, file)
                        os.remove(file_path)
                    print(f"✅ Deleted {file_count} files from {dir_path}/")
                else:
                    print(f"ℹ️  {dir_path}/ was already empty")
                results[dir_path] = {'count': file_count, 'status': 'deleted', 'error': None}
                
        except Exception as e:
            error_msg = f"Error cleaning {dir_path}: {e}"
            print(f"❌ {error_msg}")
            results[dir_path] = {'count': 0, 'status': 'error', 'error': error_msg}
    
    return results

def print_current_state(state):
    """Print current state of database and files."""
    print("\n📊 Current State:")
    print("="*50)
    
    print("\n🗄️  Database Tables:")
    for table, count in state['database'].items():
        status = "📝" if count > 0 else "🔄"
        action = "CLEAN" if table in ['guests', 'photos', 'music_queue'] else "KEEP"
        print(f"  {status} {table}: {count} records ({action})")
    
    print("\n📁 Media Directories:")
    for dir_path, count in state['files'].items():
        status = "📝" if count > 0 else "🔄"
        print(f"  {status} {dir_path}: {count} files (CLEAN)")

def print_summary(db_results, media_results, dry_run=False):
    """Print summary of operations."""
    action = "Would be cleaned" if dry_run else "Cleaned"
    print(f"\n📋 Summary - {action}:")
    print("="*50)
    
    total_db_records = 0
    total_files = 0
    
    print("\n🗄️  Database:")
    for table, result in db_results.items():
        if result['status'] in ['deleted', 'would_delete'] and result['count'] > 0:
            print(f"  ✅ {table.lower()}: {result['count']} records")
            total_db_records += result['count']
        elif result['status'] == 'error':
            print(f"  ❌ {table.lower()}: {result['error']}")
    
    print("\n📁 Media Files:")
    for dir_path, result in media_results.items():
        if result['status'] in ['deleted', 'would_delete'] and result['count'] > 0:
            print(f"  ✅ {dir_path}: {result['count']} files")
            total_files += result['count']
        elif result['status'] == 'error':
            print(f"  ❌ {dir_path}: {result['error']}")
    
    verb = "would be" if dry_run else "were"
    print(f"\n🎯 Total: {total_db_records} database records and {total_files} files {verb} cleaned")
    
    if not dry_run:
        print("\n✨ Party reset complete! Your PixelParty is ready for the next celebration! 🎉")

def main():
    parser = argparse.ArgumentParser(description='Reset PixelParty for new celebration')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be cleaned without making changes')
    parser.add_argument('--no-confirm', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🎉 PixelParty Reset Script")
    print("="*50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    # Set up Flask app context
    print("\n🚀 Setting up application context...")
    app, db, models = setup_app_context()
    
    # Get current state
    print("📊 Analyzing current state...")
    state = get_current_state(db, models)
    if state is None:
        sys.exit(1)
    
    print_current_state(state)
    
    # Confirmation prompt
    if not args.no_confirm and not args.dry_run:
        print("\n⚠️  WARNING: This will permanently delete:")
        print("   • All guest records and their photo submissions")
        print("   • All photos and wish messages") 
        print("   • All music queue entries")
        print("   • All files in media/photos/, media/videos/, and media/music/")
        print("\n✅ This will PRESERVE:")
        print("   • Music library index (your valuable music catalog)")
        print("   • App settings and configuration")
        print("   • Directory structure")
        
        response = input("\n🤔 Are you sure you want to proceed? (type 'yes' to continue): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled.")
            sys.exit(0)
    
    # Perform cleanup
    print(f"\n🧹 {'Simulating' if args.dry_run else 'Starting'} cleanup operations...")
    
    print("\n🗄️  Cleaning database tables...")
    db_results = clean_database_tables(db, models, dry_run=args.dry_run)
    
    print(f"\n📁 {'Simulating' if args.dry_run else 'Cleaning'} media directories...")
    media_results = clean_media_directories(dry_run=args.dry_run)
    
    # Print summary
    print_summary(db_results, media_results, dry_run=args.dry_run)
    
    if args.dry_run:
        print("\n💡 To actually perform the cleanup, run: python reset_party.py")

if __name__ == '__main__':
    main()