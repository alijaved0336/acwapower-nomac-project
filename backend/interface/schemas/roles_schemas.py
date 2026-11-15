"""
OpenAPI schemas for roles endpoints.
Defines reusable schema components for roles API documentation.
"""

from drf_yasg import openapi


# Role object schema
role_object_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role unique identifier"
        ),
        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Role name"),
        "type": openapi.Schema(type=openapi.TYPE_STRING, description="Role type"),
        "description": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role description"
        ),
        "is_active": openapi.Schema(
            type=openapi.TYPE_BOOLEAN, description="Active status"
        ),
        "created_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Creation timestamp",
        ),
        "updated_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Last update timestamp",
        ),
        "clusters": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="Associated cluster IDs",
        ),
    },
)

# Role object schema
role_object_schema_ur = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role unique identifier"
        ),
        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Role name"),
        "type": openapi.Schema(type=openapi.TYPE_STRING, description="Role type"),
        "description": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role description"
        ),
        "is_active": openapi.Schema(
            type=openapi.TYPE_BOOLEAN, description="Active status"
        ),
        "created_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Creation timestamp",
        ),
        "updated_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Last update timestamp",
        ),
        "clusters": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Associated clusters (list of objects)",
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Cluster unique identifier"
                    ),
                    "name": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Cluster name"
                    ),
                },
            ),
        ),
    },
)

# Query parameter schemas
search_param = openapi.Parameter(
    "search",
    openapi.IN_QUERY,
    description="Search term to filter by role name or description",
    type=openapi.TYPE_STRING,
    required=False,
)

role_type_param = openapi.Parameter(
    "type",
    openapi.IN_QUERY,
    description="Filter by role type (e.g., admin, operator, viewer)",
    type=openapi.TYPE_STRING,
    required=False,
)

is_active_param = openapi.Parameter(
    "is_active",
    openapi.IN_QUERY,
    description="Filter by active status (true/false)",
    type=openapi.TYPE_BOOLEAN,
    required=False,
)

cluster_param = openapi.Parameter(
    "cluster",
    openapi.IN_QUERY,
    description="Filter by cluster association",
    type=openapi.TYPE_STRING,
    required=False,
)

page_param = openapi.Parameter(
    "page",
    openapi.IN_QUERY,
    description="Page number for pagination",
    type=openapi.TYPE_INTEGER,
    default=1,
)

limit_param = openapi.Parameter(
    "limit",
    openapi.IN_QUERY,
    description="Number of items per page (max: 100)",
    type=openapi.TYPE_INTEGER,
    default=10,
)



# Pagination metadata schema
pagination_meta_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "total": openapi.Schema(
            type=openapi.TYPE_INTEGER, description="Total number of roles"
        ),
        "page": openapi.Schema(
            type=openapi.TYPE_INTEGER, description="Current page number"
        ),
        "limit": openapi.Schema(
            type=openapi.TYPE_INTEGER, description="Items per page"
        ),
        "pages": openapi.Schema(
            type=openapi.TYPE_INTEGER, description="Total number of pages"
        ),
    },
)

# Success response data schema
roles_data_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "items": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=role_object_schema_ur,
            description="List of role objects",
        ),
        **pagination_meta_schema.properties,
    },
)

# Complete success response schema
roles_success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "success": openapi.Schema(
            type=openapi.TYPE_BOOLEAN, description="Operation success status"
        ),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING, description="Response message"
        ),
        "data": roles_data_schema,
    },
)

# Error response schema
roles_error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING, description="Error message"
        ),
        "data": openapi.Schema(
            type=openapi.TYPE_OBJECT, description="Empty object for consistency"
        ),
    },
)

# Response definitions for different HTTP status codes
roles_responses = {
    200: openapi.Response(
        description="List of roles fetched successfully",
        schema=roles_success_response_schema,
    ),
    400: openapi.Response(
        description="Bad request - Invalid parameters",
        schema=roles_error_response_schema,
    ),
    401: openapi.Response(
        description="Unauthorized - Invalid or missing JWT token",
        schema=roles_error_response_schema,
    ),
    500: openapi.Response(
        description="Internal server error", schema=roles_error_response_schema
    ),
}



# Manual parameters list for convenience
roles_query_params = [
    page_param,
    limit_param,
    search_param,
    role_type_param,
    is_active_param,
    cluster_param,
]


create_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "name": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role name"
        ),
        "type": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role type (free text)"
        ),
        "description": openapi.Schema(
            type=openapi.TYPE_STRING, description="Role description"
        ),
        "clusters": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="List of cluster objects with sites",
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "name": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Cluster name"
                    ),
                    "sites": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        description="List of site names under this cluster"
                    ),
                },
                required=["name", "sites"],
            ),
        ),
        "is_active": openapi.Schema(
            type=openapi.TYPE_BOOLEAN, description="Is the role active?"
        ),
    },
    required=["name", "type"],
)


update_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "name": openapi.Schema(
            type=openapi.TYPE_STRING, description="Update Role name"
        ),
        "type": openapi.Schema(
            type=openapi.TYPE_STRING, description="Update Role type (free text)"
        ),
        "description": openapi.Schema(
            type=openapi.TYPE_STRING, description=" Update Role description"
        ),
        "clusters": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Update List of cluster objects with sites",
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "name": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Cluster name"
                    ),
                    "sites": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        description="List of site names under this cluster"
                    ),
                },
                required=["name", "sites"],
            ),
        ),
        "is_active": openapi.Schema(
            type=openapi.TYPE_BOOLEAN, description="Is the role active?"
        ),
    },
    required=["name", "type"],
)
