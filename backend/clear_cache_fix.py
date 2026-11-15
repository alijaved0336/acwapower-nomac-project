#!/usr/bin/env python3
"""
Cache Clearing Script for DateTime Filter Fix

This script helps clear the problematic cache entries that are causing
datetime range filter issues in the Column Data Source API.

Usage:
    python clear_cache_fix.py
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_file_based_cache():
    """Clear the file-based cache that's causing datetime filter issues."""
    try:
        cache_dir = "/tmp/swro_cache"
        cache_file = os.path.join(cache_dir, "fallback_cache.pkl")
        
        if os.path.exists(cache_file):
            # Backup the cache file before clearing
            backup_file = f"{cache_file}.backup"
            os.rename(cache_file, backup_file)
            logger.info(f"Backed up cache file to: {backup_file}")
            
            # Remove the cache file
            os.remove(backup_file)
            logger.info("Cleared file-based cache successfully")
        else:
            logger.info("No file-based cache found to clear")
            
        # Also clear any Redis cache if available
        try:
            from infrastructure.services.cache_service import CacheService
            cache_service = CacheService()
            
            if cache_service.is_cache_available():
                # Clear all column data cache entries
                cleared_count = cache_service.clear_prefix("column_data")
                logger.info(f"Cleared {cleared_count} Redis cache entries")
            else:
                logger.info("Redis cache not available")
                
        except Exception as e:
            logger.warning(f"Could not clear Redis cache: {e}")
            
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False
    
    return True

def main():
    """Main function to clear cache and provide instructions."""
    logger.info("Starting cache clearing process for DateTime filter fix...")
    
    success = clear_file_based_cache()
    
    if success:
        logger.info("✅ Cache clearing completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Restart your Django application")
        logger.info("2. Test the Column Data Source API with datetime filters")
        logger.info("3. The cache will now properly handle datetime range filtering")
        logger.info("")
        logger.info("If you still experience issues, you can use the new cache management endpoint:")
        logger.info("DELETE /columns/cache/?from_date=2025-01-01&to_date=2025-01-02")
    else:
        logger.error("❌ Cache clearing failed. Please check the logs above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
