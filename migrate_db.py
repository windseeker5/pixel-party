#!/usr/bin/env python3
"""
Database migration script to add video support fields to existing photos table.
Run this once to update your database schema.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add file_type and duration columns to photos table if they don't exist."""

    # Database path
    db_path = Path(__file__).parent / 'birthday_party.db'

    if not db_path.exists():
        print("Database not found. Will be created when app starts.")
        return

    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if file_type column exists
        cursor.execute("PRAGMA table_info(photos)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'file_type' not in columns:
            print("Adding file_type column...")
            cursor.execute("ALTER TABLE photos ADD COLUMN file_type VARCHAR(10) DEFAULT 'image'")
        else:
            print("file_type column already exists")

        if 'duration' not in columns:
            print("Adding duration column...")
            cursor.execute("ALTER TABLE photos ADD COLUMN duration REAL")
        else:
            print("duration column already exists")

        if 'thumbnail' not in columns:
            print("Adding thumbnail column...")
            cursor.execute("ALTER TABLE photos ADD COLUMN thumbnail VARCHAR(255)")
        else:
            print("thumbnail column already exists")

        # Update existing records to have file_type='image' if null
        cursor.execute("UPDATE photos SET file_type = 'image' WHERE file_type IS NULL")

        conn.commit()
        print("Database migration completed successfully!")

        # Show current schema
        cursor.execute("PRAGMA table_info(photos)")
        print("\nCurrent photos table schema:")
        for col in cursor.fetchall():
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")

    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()