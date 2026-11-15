"""
Django app configuration for infrastructure module.
Initializes Spark singleton at application startup for optimal performance.
Initializes APScheduler for scheduled tasks (hourly migrations).
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class InfrastructureConfig(AppConfig):
    """
    Infrastructure app configuration.
    Initializes Spark singleton when Django starts up.
    Initializes APScheduler for scheduled tasks.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure'
    _spark_initialized = False
    _scheduler_initialized = False
    _scheduler = None
    
    def ready(self):
        """
        Called when Django application is ready.
        Use lazy initialization for production compatibility.
        """
        # Prevent multiple initializations during Django development server reloads
        if self._spark_initialized:
            logger.info("Spark already initialized, skipping...")
            return
            
        try:
            # Check if we're in production (Azure App Service)
            import os
            is_production = os.getenv('WEBSITE_SITE_NAME') is not None
            
            if is_production:
                logger.info("Production environment detected - using lazy Spark initialization")
                logger.info("Spark will be initialized on first request for faster container startup")
            else:
                logger.info("Development environment - initializing Spark singleton eagerly...")
                
                # Import here to avoid circular imports
                from infrastructure.services.spark_singleton import initialize_spark, get_spark_info
                
                # Initialize Spark singleton
                spark_singleton = initialize_spark()
                
                # Log Spark information
                spark_info = get_spark_info()
                logger.info(f"Spark initialized successfully: {spark_info}")
            
            # Mark as initialized to prevent duplicate calls
            self._spark_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Spark singleton: {e}")
            # Don't raise the exception - let Django continue without Spark
            # Spark will be initialized on first use if needed

        # Initialize APScheduler for scheduled tasks
        if not self._scheduler_initialized:
            try:
                # Only initialize scheduler in main process (not in management commands)
                import sys
                is_management_command = 'manage.py' in ' '.join(sys.argv)
                is_migration = 'migrate' in sys.argv or 'makemigrations' in sys.argv
                is_collectstatic = 'collectstatic' in sys.argv

                # Skip scheduler for management commands except runserver
                if is_management_command and ('runserver' not in sys.argv):
                    logger.info("Skipping scheduler initialization for management command")
                elif is_migration or is_collectstatic:
                    logger.info("Skipping scheduler initialization during migration/collectstatic")
                else:
                    # Import scheduler module
                    from infrastructure.utils.scheduler import start_scheduler

                    # Start the scheduler
                    self._scheduler = start_scheduler()

                    if self._scheduler:
                        logger.info("APScheduler initialized successfully")
                        self._scheduler_initialized = True
                    else:
                        logger.info("APScheduler not started (disabled or error)")

            except Exception as e:
                logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
                # Don't raise - let Django continue without scheduler
