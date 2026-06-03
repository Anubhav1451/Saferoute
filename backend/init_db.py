"""
Database initialization script for SafeRoute AI

This script creates the database tables and optionally generates mock data.

Usage:
    python init_db.py              # Create tables only
    python init_db.py --mock-data  # Create tables and generate mock data
"""

import sys
import argparse
from sqlalchemy import create_engine
from app.db.models import Base
from app.db.session import engine


def init_database():
    """Initialize database with all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def generate_mock_data():
    """Generate mock data for testing"""
    print("Generating mock data...")
    from app.utils.generate_mock_data import generate_mock_data as generate
    generate()


def main():
    parser = argparse.ArgumentParser(description="Initialize SafeRoute AI database")
    parser.add_argument(
        "--mock-data",
        action="store_true",
        help="Generate mock data after creating tables"
    )
    
    args = parser.parse_args()
    
    try:
        init_database()
        
        if args.mock_data:
            generate_mock_data()
        else:
            print("\nTo generate mock data, run:")
            print("  python init_db.py --mock-data")
            print("  or")
            print("  python -m app.utils.generate_mock_data")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
