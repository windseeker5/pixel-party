#!/usr/bin/env python3
"""
Database migration script to add video support columns to photos table.
"""

import sqlite3
import sys
import os

def migrate_database(db_path):
    """Add video support columns to photos table if they don't exist."""

    print(f"🔄 Migrating database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(photos)")
        columns = [column[1] for column in cursor.fetchall()]

        migrations_needed = []

        if 'file_type' not in columns:
            migrations_needed.append("ALTER TABLE photos ADD COLUMN file_type VARCHAR(10) DEFAULT 'image'")

        if 'duration' not in columns:
            migrations_needed.append("ALTER TABLE photos ADD COLUMN duration FLOAT")

        if 'thumbnail' not in columns:
            migrations_needed.append("ALTER TABLE photos ADD COLUMN thumbnail VARCHAR(255)")

        if not migrations_needed:
            print("✅ Database already has video support columns")
            return True

        print(f"📝 Running {len(migrations_needed)} migration(s):")

        for migration in migrations_needed:
            print(f"   - {migration}")
            cursor.execute(migration)

        # Update existing records to have file_type = 'image' if NULL
        cursor.execute("UPDATE photos SET file_type = 'image' WHERE file_type IS NULL")

        conn.commit()
        print("✅ Migration completed successfully")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

    finally:
        if conn:
            conn.close()

def main():
    """Main migration function."""

    # Find database file
    possible_paths = [
        './app.db',
        './instance/app.db',
        '/app/app.db',
        '/app/instance/app.db'
    ]

    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("❌ Database file not found. Checked paths:")
        for path in possible_paths:
            print(f"   - {path}")
        sys.exit(1)

    success = migrate_database(db_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()