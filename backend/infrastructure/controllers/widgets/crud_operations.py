"""
Widget CRUD operations - focused on individual widget operations.
Split from operations.py to keep files under 250 lines.
"""
import logging
from typing import Dict, Any

from infrastructure.services.widgets import WidgetsService
from infrastructure.controllers.widgets.validation import WidgetValidator

logger = logging.getLogger(__name__)


class WidgetCrudOperations:
    """Handles individual widget CRUD operations."""
    
    def __init__(self):
        self.widgets_service = WidgetsService()
        self.validator = WidgetValidator()
    
    def create_single_widget(self, analysis_id: str, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a single widget with full validation.
        
        Args:
            analysis_id: Analysis identifier
            widget_data: Widget configuration
            
        Returns:
            Dictionary with creation results
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
            
            # Sanitize and validate widget data
            sanitized_data = self.validator.sanitize_widget_data(widget_data)
            widget_validation = self.validator.validate_single_widget(sanitized_data)
            
            if not widget_validation["is_valid"]:
                return {
                    "success": False,
                    "message": f"Widget validation failed: {'; '.join(widget_validation['errors'])}",
                    "data": None,
                    "validation_errors": widget_validation["errors"]
                }
            
            # Add warnings to response if any
            response_data = {"warnings": widget_validation["warnings"]} if widget_validation["warnings"] else {}
            
            # Create widget
            created_widget = self.widgets_service.create_widget(analysis_id, sanitized_data)
            
            return {
                "success": True,
                "message": "Widget created successfully",
                "data": {**created_widget, **response_data}
            }
            
        except Exception as e:
            logger.error(f"Error creating widget for analysis {analysis_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to create widget: {str(e)}",
                "data": None
            }
    
    def update_widget(self, analysis_id: str, widget_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a widget with validation.
        
        Args:
            analysis_id: Analysis identifier
            widget_id: Widget identifier
            update_data: Fields to update
            
        Returns:
            Dictionary with update results
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
            
            # Sanitize update data
            sanitized_data = self.validator.sanitize_widget_data(update_data)
            
            # Validate partial widget data (for updates, not all fields are required)
            if sanitized_data:  # Only validate if there's data to update
                # Create a mock complete widget for validation by merging with minimal required fields
                mock_widget = {
                    "type": "line_chart",  # Default type for validation
                    "title": "Mock Title",  # Default title for validation
                    "config": {},  # Default config for validation
                    **sanitized_data  # Override with actual update data
                }
                
                widget_validation = self.validator.validate_single_widget(mock_widget)
                if not widget_validation["is_valid"]:
                    return {
                        "success": False,
                        "message": f"Update validation failed: {'; '.join(widget_validation['errors'])}",
                        "data": None
                    }
            
            # Update widget
            updated_widget = self.widgets_service.update_widget(analysis_id, widget_id, sanitized_data)
            
            return {
                "success": True,
                "message": "Widget updated successfully",
                "data": updated_widget
            }
            
        except Exception as e:
            logger.error(f"Error updating widget {widget_id} for analysis {analysis_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update widget: {str(e)}",
                "data": None
            }
    
    def delete_widget(self, analysis_id: str, widget_id: str) -> Dict[str, Any]:
        """
        Delete a widget with validation.
        
        Args:
            analysis_id: Analysis identifier
            widget_id: Widget identifier
            
        Returns:
            Dictionary with deletion results
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
            
            # Delete widget
            deleted = self.widgets_service.delete_widget(analysis_id, widget_id)
            
            if deleted:
                return {
                    "success": True,
                    "message": "Widget deleted successfully",
                    "data": {"deleted_widget_id": widget_id}
                }
            else:
                return {
                    "success": False,
                    "message": "Widget not found or could not be deleted",
                    "data": None
                }
            
        except Exception as e:
            logger.error(f"Error deleting widget {widget_id} for analysis {analysis_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete widget: {str(e)}",
                "data": None
            }
    
    def get_widget_by_id(self, analysis_id: str, widget_id: str) -> Dict[str, Any]:
        """
        Get a specific widget by ID with validation.
        
        Args:
            analysis_id: Analysis identifier
            widget_id: Widget identifier
            
        Returns:
            Dictionary with widget data
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
            
            # Get widget
            widget = self.widgets_service.get_widget_by_id(analysis_id, widget_id)
            
            if widget:
                return {
                    "success": True,
                    "message": "Widget retrieved successfully",
                    "data": widget
                }
            else:
                return {
                    "success": False,
                    "message": "Widget not found",
                    "data": None
                }
            
        except Exception as e:
            logger.error(f"Error getting widget {widget_id} for analysis {analysis_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to retrieve widget: {str(e)}",
                "data": None
            }
