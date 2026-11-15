"""
Swagger schema definitions for widgets API.
Separates schema definitions from controller logic for cleaner code organization.
"""
from drf_yasg import openapi


class WidgetSwaggerSchemas:
    """Centralized Swagger schema definitions for widgets API."""
    
    # Common widget properties
    WIDGET_PROPERTIES = {
        "id": openapi.Schema(type=openapi.TYPE_STRING, description="Widget ID"),
        "title": openapi.Schema(type=openapi.TYPE_STRING, description="Widget title"),
        "type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Widget type",
            enum=["line_chart", "bar_chart", "pie_chart", "scatter_plot", "histogram", "heatmap", "table", "metric_card", "gauge"]
        ),
        "config": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Widget configuration (JSON object)",
            additional_properties=True
        ),
        "position_x": openapi.Schema(type=openapi.TYPE_INTEGER, description="X position"),
        "position_y": openapi.Schema(type=openapi.TYPE_INTEGER, description="Y position"),
        "width": openapi.Schema(type=openapi.TYPE_INTEGER, description="Widget width"),
        "height": openapi.Schema(type=openapi.TYPE_INTEGER, description="Widget height"),
        "chart_library": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Chart library to use",
            enum=["plotly", "matplotlib", "seaborn", "d3"]
        ),
        "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        "updated_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
    }
    
    # Request schemas
    CREATE_WIDGET_REQUEST = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["title", "type", "config"],
        properties={
            "title": WIDGET_PROPERTIES["title"],
            "type": WIDGET_PROPERTIES["type"],
            "config": WIDGET_PROPERTIES["config"],
            "position_x": WIDGET_PROPERTIES["position_x"],
            "position_y": WIDGET_PROPERTIES["position_y"],
            "width": WIDGET_PROPERTIES["width"],
            "height": WIDGET_PROPERTIES["height"],
            "chart_library": WIDGET_PROPERTIES["chart_library"]
        }
    )
    
    BULK_CREATE_REQUEST = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["widgets"],
        properties={
            "widgets": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=CREATE_WIDGET_REQUEST,
                description="Array of widget configurations"
            )
        }
    )
    
    UPDATE_WIDGET_REQUEST = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": WIDGET_PROPERTIES["title"],
            "config": WIDGET_PROPERTIES["config"],
            "position_x": WIDGET_PROPERTIES["position_x"],
            "position_y": WIDGET_PROPERTIES["position_y"],
            "width": WIDGET_PROPERTIES["width"],
            "height": WIDGET_PROPERTIES["height"],
            "chart_library": WIDGET_PROPERTIES["chart_library"]
        }
    )
    
    # Response schemas
    WIDGET_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=WIDGET_PROPERTIES
    )
    
    WIDGET_LIST_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
            "message": openapi.Schema(type=openapi.TYPE_STRING),
            "data": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=WIDGET_RESPONSE
            ),
            "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of widgets")
        }
    )
    
    CREATE_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
            "message": openapi.Schema(type=openapi.TYPE_STRING),
            "data": WIDGET_RESPONSE
        }
    )
    
    BULK_CREATE_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
            "message": openapi.Schema(type=openapi.TYPE_STRING),
            "data": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "created_widgets": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=WIDGET_RESPONSE
                    ),
                    "created_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "validation_errors": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        }
    )
    
    ERROR_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
            "message": openapi.Schema(type=openapi.TYPE_STRING),
            "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
        }
    )
    
    # Parameter definitions
    ANALYSIS_ID_PARAMETER = openapi.Parameter(
        "analysisID",
        openapi.IN_PATH,
        description="Analysis identifier",
        type=openapi.TYPE_STRING,
        required=True
    )
    
    WIDGET_ID_PARAMETER = openapi.Parameter(
        "widgetId",
        openapi.IN_PATH,
        description="Widget identifier",
        type=openapi.TYPE_STRING,
        required=True
    )
    
    # Response examples
    WIDGET_LIST_EXAMPLE = {
        "success": True,
        "message": "Widgets retrieved successfully",
        "data": [
            {
                "id": "widget_123",
                "title": "Sales Chart",
                "type": "line_chart",
                "config": {
                    "x_axis": "date",
                    "y_axis": "sales_amount",
                    "color": "blue"
                },
                "position_x": 0,
                "position_y": 0,
                "width": 6,
                "height": 4,
                "chart_library": "plotly",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ],
        "count": 1
    }
    
    CREATE_WIDGET_EXAMPLE = {
        "success": True,
        "message": "Widget created successfully",
        "data": {
            "id": "widget_124",
            "title": "New Sales Chart",
            "type": "bar_chart",
            "config": {
                "x_axis": "product",
                "y_axis": "revenue"
            },
            "position_x": 6,
            "position_y": 0,
            "width": 6,
            "height": 4,
            "chart_library": "plotly",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }
    
    ERROR_EXAMPLE = {
        "success": False,
        "message": "Widget not found",
        "data": None
    }
