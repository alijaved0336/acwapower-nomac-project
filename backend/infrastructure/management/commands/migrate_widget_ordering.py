"""
Django management command to migrate widget ordering feature.

This command adds the display_order column to the widget table and initializes
display_order values for existing widgets based on their creation timestamps.

Usage:
    python manage.py migrate_widget_ordering [--dry-run] [--validate-only]

Options:
    --dry-run: Show what would be done without making changes
    --validate-only: Only validate the current state without migration

Example:
    python manage.py migrate_widget_ordering
    python manage.py migrate_widget_ordering --dry-run
    python manage.py migrate_widget_ordering --validate-only
"""
import logging
from typing import Dict

from django.core.management.base import BaseCommand, CommandError
from infrastructure.services.widgets import WidgetsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate widget ordering feature: add display_order column and initialize values"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Only validate the current migration state",
        )

    def handle(self, *args, **options):
        """Main command handler"""
        try:
            dry_run = options.get("dry_run", False)
            validate_only = options.get("validate_only", False)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING("DRY RUN MODE: No changes will be made")
                )

            if validate_only:
                self.stdout.write(
                    self.style.HTTP_INFO("VALIDATION MODE: Only checking current state")
                )
                return self._validate_migration()

            # Initialize service
            widgets_service = WidgetsService()

            self.stdout.write(
                self.style.HTTP_INFO("Starting widget ordering migration...")
            )

            if dry_run:
                return self._dry_run_migration(widgets_service)
            else:
                return self._execute_migration(widgets_service)

        except Exception as e:
            logger.error(f"Widget ordering migration failed: {str(e)}")
            raise CommandError(f"Migration failed: {str(e)}")

    def _dry_run_migration(self, widgets_service: WidgetsService):
        """Simulate migration without making changes"""
        self.stdout.write("DRY RUN: Widget ordering migration simulation")
        self.stdout.write("=" * 60)

        # Simulate column addition
        self.stdout.write("1. Would add display_order column to widget table")
        self.stdout.write("   - Column: display_order INT DEFAULT 0")
        self.stdout.write("   - Action: ALTER TABLE widget ADD COLUMN IF NOT EXISTS")

        # Simulate initialization
        self.stdout.write("2. Would initialize display_order for existing widgets")
        self.stdout.write("   - Logic: ROW_NUMBER() based on created_at per analysis")
        self.stdout.write("   - Scope: All widgets with display_order = 0 or NULL")

        # Simulate validation
        self.stdout.write("3. Would validate migration results")
        self.stdout.write("   - Check: All widgets have valid display_order values")
        self.stdout.write("   - Check: No duplicate orders within same analysis")

        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS("DRY RUN COMPLETE: No actual changes made")
        )
        self.stdout.write(
            "Run without --dry-run to execute the migration"
        )

    def _execute_migration(self, widgets_service: WidgetsService) -> Dict:
        """Execute the actual migration"""
        self.stdout.write("Executing widget ordering migration...")
        self.stdout.write("=" * 60)

        try:
            # Execute migration
            result = widgets_service.migrate_widget_ordering()

            # Display results
            self._display_migration_results(result)

            if result.get("success", False):
                self.stdout.write(
                    self.style.SUCCESS("Widget ordering migration completed successfully!")
                )

                # Suggest next steps
                self.stdout.write("\nNext steps:")
                self.stdout.write("1. Test widget ordering endpoints")
                self.stdout.write("2. Verify display_order values in database")
                self.stdout.write("3. Update frontend to use display_order field")

            else:
                self.stdout.write(
                    self.style.ERROR("Widget ordering migration encountered issues")
                )
                return self._handle_migration_issues(result)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Migration execution failed: {str(e)}")
            )
            raise

    def _validate_migration(self) -> Dict:
        """Validate current migration state"""
        self.stdout.write("Validating widget ordering migration state...")
        self.stdout.write("=" * 60)

        try:
            widgets_service = WidgetsService()
            repository = widgets_service._get_repository()

            # Validate migration state
            validation_result = repository.validate_display_order_migration()

            self._display_validation_results(validation_result)

            if validation_result.get("success", False):
                self.stdout.write(
                    self.style.SUCCESS("Widget ordering migration validation PASSED")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("Widget ordering migration validation found ISSUES")
                )

                issues = validation_result.get("issues", [])
                if issues:
                    self.stdout.write(f"\nFound {len(issues)} analyses with ordering issues:")
                    for issue in issues[:5]:  # Show first 5 issues
                        self.stdout.write(f"  - Analysis {issue['analysis_id']}: "
                                       f"{issue['total_widgets']} widgets, "
                                       f"{issue['unique_orders']} unique orders")

                    if len(issues) > 5:
                        self.stdout.write(f"  ... and {len(issues) - 5} more")

                    self.stdout.write("\nRun migration to fix these issues:")
                    self.stdout.write("  python manage.py migrate_widget_ordering")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Validation failed: {str(e)}")
            )
            raise

    def _display_migration_results(self, result: Dict):
        """Display formatted migration results"""
        self.stdout.write("Migration Results:")
        self.stdout.write("-" * 40)

        # Column addition results
        column_result = result.get("column_addition", {})
        if column_result.get("success"):
            self.stdout.write(
                self.style.SUCCESS("✓ Display order column added successfully")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ Failed to add display order column")
            )

        # Initialization results
        init_result = result.get("initialization", {})
        if init_result.get("success"):
            widgets_updated = init_result.get("widgets_updated", 0)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Initialized display_order for {widgets_updated} widgets")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ Failed to initialize display_order values")
            )

        # Validation results
        validation_result = result.get("validation", {})
        self._display_validation_results(validation_result)

    def _display_validation_results(self, validation_result: Dict):
        """Display formatted validation results"""
        if validation_result.get("success"):
            self.stdout.write(
                self.style.SUCCESS("✓ Migration validation passed")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠ Migration validation found issues")
            )

            issues = validation_result.get("issues", [])
            if issues:
                self.stdout.write(f"Issues found in {len(issues)} analyses")

    def _handle_migration_issues(self, result: Dict):
        """Handle migration issues and provide guidance"""
        self.stdout.write("\nMigration Issues:")
        self.stdout.write("-" * 40)

        # Check individual components
        column_result = result.get("column_addition", {})
        if not column_result.get("success"):
            self.stdout.write(
                self.style.ERROR("Column addition failed:")
            )
            self.stdout.write(f"  {column_result.get('message', 'Unknown error')}")

        init_result = result.get("initialization", {})
        if not init_result.get("success"):
            self.stdout.write(
                self.style.ERROR("Initialization failed:")
            )
            self.stdout.write(f"  {init_result.get('message', 'Unknown error')}")

        validation_result = result.get("validation", {})
        if not validation_result.get("success"):
            self.stdout.write(
                self.style.WARNING("Validation issues:")
            )
            self.stdout.write(f"  {validation_result.get('message', 'Unknown validation issues')}")

        # Provide troubleshooting guidance
        self.stdout.write("\nTroubleshooting:")
        self.stdout.write("1. Check database connectivity")
        self.stdout.write("2. Ensure proper permissions on widget table")
        self.stdout.write("3. Verify Databricks connection settings")
        self.stdout.write("4. Check logs for detailed error information")

        raise CommandError("Migration completed with issues - see details above")