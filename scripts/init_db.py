"""Database initialization script for BRI video agent."""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from storage import initialize_database, get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the BRI database with schema."""
    try:
        logger.info("Starting database initialization...")
        
        # Ensure directories exist
        Config.ensure_directories()
        logger.info(f"Database path: {Config.DATABASE_PATH}")
        
        # Initialize database schema
        initialize_database()
        logger.info("Database schema initialized successfully")
        
        # Verify tables were created
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Created tables: {', '.join(tables)}")
        
        logger.info("Database initialization complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
