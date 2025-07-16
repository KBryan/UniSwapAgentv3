#!/usr/bin/env python3
"""
Database initialization script for NFT Trading Bot.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env file in project root
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        # Try loading from current directory
        load_dotenv()

except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("Trying to use system environment variables...")

from core.database import engine, Base, create_tables
from core.models import *  # Import all models
from sqlalchemy import text  # Add this import


def run_alembic_upgrade():
    """Run Alembic migrations to upgrade database to latest version."""
    try:
        print("Running Alembic migrations...")
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            print(result.stdout)
        else:
            print("❌ Database migration failed:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

    return True


def create_tables_directly():
    """Create tables directly using SQLAlchemy (fallback method)."""
    try:
        print("Creating tables directly with SQLAlchemy...")
        create_tables()
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def check_database_connection():
    """Check if database connection is working."""
    try:
        print("Checking database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))  # Fixed: wrapped with text()
            result.fetchone()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False


def main():
    """Main initialization function."""
    print("🚀 Initializing NFT Trading Bot Database")
    print("=" * 50)

    # Check environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)

    print(f"Database URL: {database_url}")

    # Check database connection
    if not check_database_connection():
        sys.exit(1)

    # Try Alembic migrations first
    if run_alembic_upgrade():
        print("✅ Database initialization completed with Alembic")
    else:
        print("⚠️  Alembic failed, trying direct table creation...")
        if create_tables_directly():
            print("✅ Database initialization completed with direct creation")
        else:
            print("❌ Database initialization failed")
            sys.exit(1)

    print("\n🎉 Database is ready!")
    print("You can now start the application with:")
    print("  docker-compose up")
    print("  or")
    print("  uvicorn api.main:app --reload")


if __name__ == "__main__":
    main()