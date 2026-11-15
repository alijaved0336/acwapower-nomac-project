"""
Widget bulk operations - focused on bulk and list operations.
Split from operations.py to keep files under 250 lines.
"""
import logging
from typing import Dict, List, Any

from infrastructure.services.widgets import WidgetsService
from infrastructure.controllers.widgets.validation import WidgetValidator

logger = logging.getLogger(__name__)


class WidgetBulkOperations:
    """Handles bulk widget operations and listings."""
    
    def __init__(self):
        self.widgets_service = WidgetsService()
        self.validator = WidgetValidator()
    
    def get_widgets_for_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get all widgets for a specific analysis with validation.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Validate analysis ID
            validation = self.validator.validate_analysis_id(analysis_id)
            if not validation["is_valid"]:
                return {
                    "success": False,
                    "message": f"Invalid analysis ID: {'; '.join(validation['errors'])}",
                    "data": None
                }
            
            # Get widgets from service
            widgets = self.widgets_service.get_widgets_by_analysis(analysis_id)
            
            return {
                "success": True,
                "message": f"Retrieved {len(widgets)} widgets for analysis {analysis_id}",
                "data": widgets,
                "count": len(widgets)
            }
            
        except Exception as e:
            logger.error(f"Error getting widgets for analysis {analysis_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to retrieve widgets: {str(e)}",
                "data": None
            }
    
    def create_bulk_widgets(self, analysis_id: str, widgets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple widgets with bulk validation and processing.
        
        Args:
            analysis_id: Analysis identifier
            widgets_data: List of widget configurations
            
        Returns:
            Dictionary with bulk creation results
        """
        try:
            # Validate analysis ID
            analysis_validation = self.validator.validate_analysis_id(analysis_id)
            if not analysis_validation["is_valid"]:
                return {
                    "success": False,
                    "message": f"Invalid analysis ID: {'; '.join(analysis_validation['errors'])}",
                    "data": None
                }
            
            # Validate all widgets
            bulk_validation = self.validator.validate_bulk_widgets(widgets_data)
            
            if not bulk_validation["overall_valid"]:
                return {
                    "success": False,
                    "message": f"Bulk validation failed: {bulk_validation['invalid_widgets']} invalid widgets",
                    "data": {
                        "validation_summary": bulk_validation,
                        "created_widgets": [],
                        "created_count": 0
                    }
                }
            
            # Create valid widgets
            created_widgets = []
            creation_errors = []
            
            for i, widget_data in enumerate(widgets_data):
                try:
                    sanitized_data = self.validator.sanitize_widget_data(widget_data)
                    created_widget = self.widgets_service.create_widget(analysis_id, sanitized_data)
                    created_widgets.append(created_widget)
                except Exception as e:
                    creation_errors.append({
                        "widget_index": i,
                        "error": str(e)
                    })
            
            success = len(creation_errors) == 0
            message = f"Created {len(created_widgets)} widgets successfully"
            if creation_errors:
                message += f" with {len(creation_errors)} errors"
            
            return {
                "success": success,
                "message": message,
                "data": {
                    "created_widgets": created_widgets,
                    "created_count": len(created_widgets),
                    "creation_errors": creation_errors,
                    "validation_summary": bulk_validation
                }
            }
            
        except Exception as e:
            logger.error(f"Error in bulk widget creation for analysis {analysis_id}: {e}")
            return {
                "success": False,
                "message": f"Bulk creation failed: {str(e)}",
                "data": None
            }
