"""
Widget validation utilities for separating validation logic from controller.
Keeps individual files under 250 lines as per project requirements.
"""
import re
from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class WidgetValidator:
    """Handles all widget validation logic."""
    
    # Valid widget types
    VALID_WIDGET_TYPES = [
        "line_chart", "bar_chart", "pie_chart", "scatter_plot", 
        "histogram", "heatmap", "table", "metric_card", "gauge"
    ]
    
    # Valid chart libraries
    VALID_CHART_LIBRARIES = ["plotly", "matplotlib", "seaborn", "d3"]
    
    @staticmethod
    def validate_single_widget(widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single widget configuration.
        
        Args:
            widget_data: Widget configuration dictionary
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Required fields validation
            required_fields = ["type", "title", "config"]
            for field in required_fields:
                if field not in widget_data:
                    validation_result["errors"].append(f"Missing required field: {field}")
                    validation_result["is_valid"] = False
            
            # Widget type validation
            widget_type = widget_data.get("type")
            if widget_type and widget_type not in WidgetValidator.VALID_WIDGET_TYPES:
                validation_result["errors"].append(
                    f"Invalid widget type: {widget_type}. "
                    f"Valid types: {', '.join(WidgetValidator.VALID_WIDGET_TYPES)}"
                )
                validation_result["is_valid"] = False
            
            # Title validation
            title = widget_data.get("title", "")
            if len(title) > 100:
                validation_result["errors"].append("Widget title cannot exceed 100 characters")
                validation_result["is_valid"] = False
            elif len(title) < 3:
                validation_result["errors"].append("Widget title must be at least 3 characters")
                validation_result["is_valid"] = False
            
            # Config validation
            config = widget_data.get("config", {})
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except json.JSONDecodeError:
                    validation_result["errors"].append("Invalid JSON in config field")
                    validation_result["is_valid"] = False
            
            if isinstance(config, dict):
                config_validation = WidgetValidator._validate_widget_config(config, widget_type)
                validation_result["errors"].extend(config_validation["errors"])
                validation_result["warnings"].extend(config_validation["warnings"])
                if config_validation["errors"]:
                    validation_result["is_valid"] = False
            
            # Chart library validation
            chart_library = widget_data.get("chart_library")
            if chart_library and chart_library not in WidgetValidator.VALID_CHART_LIBRARIES:
                validation_result["warnings"].append(
                    f"Unsupported chart library: {chart_library}. "
                    f"Supported: {', '.join(WidgetValidator.VALID_CHART_LIBRARIES)}"
                )
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    @staticmethod
    def validate_bulk_widgets(widgets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple widgets at once.
        
        Args:
            widgets_data: List of widget configurations
            
        Returns:
            Dictionary with bulk validation results
        """
        bulk_validation = {
            "total_widgets": len(widgets_data),
            "valid_widgets": 0,
            "invalid_widgets": 0,
            "validation_results": [],
            "overall_valid": True
        }
        
        for i, widget_data in enumerate(widgets_data):
            result = WidgetValidator.validate_single_widget(widget_data)
            result["widget_index"] = i
            bulk_validation["validation_results"].append(result)
            
            if result["is_valid"]:
                bulk_validation["valid_widgets"] += 1
            else:
                bulk_validation["invalid_widgets"] += 1
                bulk_validation["overall_valid"] = False
        
        return bulk_validation
    
    @staticmethod
    def _validate_widget_config(config: Dict[str, Any], widget_type: str) -> Dict[str, Any]:
        """
        Validate widget-specific configuration.
        
        Args:
            config: Widget configuration
            widget_type: Type of widget
            
        Returns:
            Validation results for configuration
        """
        validation = {"errors": [], "warnings": []}
        
        try:
            # Common validations for all widget types
            if "x_axis" in config:
                if not isinstance(config["x_axis"], str) or len(config["x_axis"]) == 0:
                    validation["errors"].append("x_axis must be a non-empty string")
            
            if "y_axis" in config:
                if not isinstance(config["y_axis"], str) or len(config["y_axis"]) == 0:
                    validation["errors"].append("y_axis must be a non-empty string")
            
            # Widget-type specific validations
            if widget_type == "pie_chart":
                if "value_column" not in config:
                    validation["errors"].append("Pie chart requires value_column in config")
                if "label_column" not in config:
                    validation["errors"].append("Pie chart requires label_column in config")
            
            elif widget_type == "table":
                if "columns" in config:
                    if not isinstance(config["columns"], list):
                        validation["errors"].append("Table columns must be a list")
                    elif len(config["columns"]) == 0:
                        validation["warnings"].append("Table has no columns specified")
            
            elif widget_type in ["line_chart", "bar_chart", "scatter_plot"]:
                if "x_axis" not in config or "y_axis" not in config:
                    validation["errors"].append(f"{widget_type} requires both x_axis and y_axis")
            
            elif widget_type == "metric_card":
                if "metric_column" not in config:
                    validation["errors"].append("Metric card requires metric_column in config")
                if "aggregation" in config:
                    valid_aggs = ["sum", "avg", "count", "min", "max"]
                    if config["aggregation"] not in valid_aggs:
                        validation["errors"].append(
                            f"Invalid aggregation: {config['aggregation']}. "
                            f"Valid: {', '.join(valid_aggs)}"
                        )
        
        except Exception as e:
            validation["errors"].append(f"Config validation error: {str(e)}")
        
        return validation
    
    @staticmethod
    def validate_analysis_id(analysis_id: str) -> Dict[str, Any]:
        """
        Validate analysis ID format and security.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Validation results
        """
        validation = {"is_valid": True, "errors": []}
        
        try:
            # Check for required format (UUID-like or specific pattern)
            if not analysis_id or len(analysis_id.strip()) == 0:
                validation["errors"].append("Analysis ID cannot be empty")
                validation["is_valid"] = False
            
            # Length validation
            if len(analysis_id) > 50:
                validation["errors"].append("Analysis ID cannot exceed 50 characters")
                validation["is_valid"] = False
            
            # Security validation - prevent injection attacks
            if re.search(r'[<>"\';{}()\\]', analysis_id):
                validation["errors"].append("Analysis ID contains invalid characters")
                validation["is_valid"] = False
            
            # Path traversal prevention
            if '..' in analysis_id or '/' in analysis_id or '\\' in analysis_id:
                validation["errors"].append("Analysis ID cannot contain path traversal characters")
                validation["is_valid"] = False
        
        except Exception as e:
            validation["errors"].append(f"Analysis ID validation error: {str(e)}")
            validation["is_valid"] = False
        
        return validation
    
    @staticmethod
    def sanitize_widget_data(widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize widget data for security.
        
        Args:
            widget_data: Raw widget data
            
        Returns:
            Sanitized widget data
        """
        try:
            sanitized = {}
            
            # Sanitize string fields
            string_fields = ["title", "description", "type", "chart_library"]
            for field in string_fields:
                if field in widget_data:
                    value = str(widget_data[field]).strip()
                    # Remove potential XSS characters
                    value = re.sub(r'[<>"\']', '', value)
                    sanitized[field] = value
            
            # Sanitize config (ensure it's valid JSON)
            if "config" in widget_data:
                config = widget_data["config"]
                if isinstance(config, str):
                    try:
                        sanitized["config"] = json.loads(config)
                    except json.JSONDecodeError:
                        sanitized["config"] = {}
                elif isinstance(config, dict):
                    sanitized["config"] = config
                else:
                    sanitized["config"] = {}
            
            # Copy safe fields directly
            safe_fields = ["position_x", "position_y", "width", "height"]
            for field in safe_fields:
                if field in widget_data:
                    try:
                        sanitized[field] = int(widget_data[field])
                    except (ValueError, TypeError):
                        pass  # Skip invalid numeric values
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing widget data: {e}")
            return {}
