import logging
from typing import Any

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.roles import RoleService
from interface.schemas.roles_schemas import roles_query_params, roles_responses , create_request_body , update_request_body
from interface.serializers.roles import RoleSerializer, RoleUpdateSerializer

logger = logging.getLogger(__name__)


class RoleListView(APIView):
    """
    API view for listing roles with filtering, searching, and pagination capabilities.
    JWT authentication is applied via middleware.
    """

    def __init__(self):
        super().__init__()
        self.service = RoleService()

    @swagger_auto_schema(
        operation_id="get_roles",
        operation_summary="Get all roles with optional filters",
        operation_description="Retrieve a paginated list of roles from the Databricks SQL Warehouse roles table with optional filtering by type, active status, cluster, and search capabilities.",
        manual_parameters=roles_query_params,
        responses=roles_responses,
        tags=["Roles"],
    )
    def get(self, request):
        """
        Handle GET request to retrieve roles with filtering and pagination.

        Args:
            request: HTTP request object containing query parameters

        Returns:
            Response: Standardized API response with role data or error message
        """
        try:
            # Extract and validate query parameters
            try:
                page = int(request.GET.get("page", 1))
                if page < 1:
                    page = 1
            except (ValueError, TypeError):
                page = 1

            try:
                limit = int(request.GET.get("limit", 10))
                # Enforce maximum limit of 100
                if limit > 100:
                    limit = 100
                elif limit < 1:
                    limit = 10
            except (ValueError, TypeError):
                limit = 10

            # Extract and sanitize filter parameters
            search = self._sanitize_search_param(request.GET.get("search"))
            role_type = self._sanitize_string_param(request.GET.get("type"))
            cluster = self._sanitize_string_param(request.GET.get("cluster"))

            # Handle boolean parameter
            is_active = request.GET.get("is_active")
            if is_active is not None:
                is_active_str = str(is_active).lower()
                if is_active_str in ["true", "1", "yes"]:
                    is_active = True
                elif is_active_str in ["false", "0", "no"]:
                    is_active = False
                else:
                    is_active = None

            logger.info(
                f"Fetching roles with params: page={page}, limit={limit}, search={search}, "
                f"type={role_type}, is_active={is_active}, cluster={cluster}"
            )

            # Call service layer to fetch roles
            result = self.service.get_roles(
                page=page,
                limit=limit,
                search=search,
                role_type=role_type,
                is_active=is_active,
                cluster=cluster,
            )

            return ResponseBuilder.success(
                data=result, message="Roles fetched successfully"
            )

        except ValueError as ve:
            logger.error(f"Validation error in get_roles: {str(ve)}")
            return ResponseBuilder.error(
                message=f"Invalid parameters: {str(ve)}", status_code=400
            )
        except Exception as e:
            logger.error(f"Error fetching roles: {str(e)}", exc_info=True)
            return ResponseBuilder.server_error(
                message=f"Failed to fetch roles: {str(e)}"
            )

    def _sanitize_search_param(self, search: str) -> str:
        """
        Sanitize search parameter input for security.

        Args:
            search: Raw search parameter from request

        Returns:
            Sanitized search string or None
        """
        if not search or not search.strip():
            return None

        # Basic length validation
        if len(search) > 100:
            return None

        # Remove potentially dangerous characters while keeping search functionality
        import re

        # Allow alphanumeric, spaces, hyphens, underscores, and dots for search
        sanitized = re.sub(r"[^a-zA-Z0-9\s\-_.]", "", search.strip())

        # Remove common SQL injection patterns
        dangerous_patterns = [
            "--",
            "/*",
            "*/",
            ";",
            "union",
            "select",
            "drop",
            "insert",
            "update",
            "delete",
        ]
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern.lower(), "")
            sanitized = sanitized.replace(pattern.upper(), "")

        return sanitized.strip() if sanitized.strip() else None

    def _sanitize_string_param(self, value: str) -> str:
        """
        Sanitize general string parameters for security.

        Args:
            value: Raw string parameter from request

        Returns:
            Sanitized string or None
        """
        if not value or not value.strip():
            return None

        # Basic length validation
        if len(value) > 50:
            return None

        # Allow only alphanumeric characters, hyphens, and underscores
        import re

        sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "", value.strip())

        return sanitized if sanitized else None


class RoleCreateView(APIView):
    """
    POST /roles/post
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="create_role",
        operation_summary="Create a new role",
        request_body=create_request_body,
        responses={
            201: "Role created successfully",
            400: "Invalid data",
            409: "Name already exists",
        },
        tags=["Roles"],
    )
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseBuilder.error(
                message="Invalid data",
                data={"details": serializer.errors},
                status_code=400,
            )
        service = RoleService()
        try:
            role_id = service.create_role(serializer.validated_data)
            created = service.get_by_id(role_id)
            return ResponseBuilder.success(
                data=created, message="Role created successfully", status_code=201
            )
        except ValueError as ve:
            return ResponseBuilder.error(
                message=str(ve), status_code=409 if "exists" in str(ve) else 400
            )
        except Exception as e:
            return ResponseBuilder.error(
                message="Failed to create role",
                data={"details": str(e)},
                status_code=500,
            )


class RoleUpdateView(APIView):
    """
    PUT /roles/update/<role_id>
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="update_role",
        operation_summary="Update an existing role",
        request_body=update_request_body,
        responses={
            200: "Role updated successfully",
            404: "Role not found",
            400: "Invalid data",
            409: "Name exists",
        },
        tags=["Roles"],
    )
    def put(self, request, role_id: str):
        serializer = RoleUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return ResponseBuilder.error(
                message="Invalid data",
                data={"details": serializer.errors},
                status_code=400,
            )
        service = RoleService()
        try:
            updated = service.update_role(role_id, serializer.validated_data)
            if not updated:
                return ResponseBuilder.error(message="Role not found", status_code=404)
            return ResponseBuilder.success(
                data=updated, message="Role updated successfully", status_code=200
            )
        except ValueError as ve:
            # e.g., name uniqueness violation
            return ResponseBuilder.error(
                message=str(ve), status_code=409 if "exists" in str(ve) else 400
            )
        except Exception as e:
            return ResponseBuilder.error(
                message="Failed to update role",
                data={"details": str(e)},
                status_code=500,
            )


class RoleDeleteView(APIView):
    """
    DELETE /roles/delete/<role_id>
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="delete_role",
        operation_summary="Delete an existing role",
        responses={
            200: "Role deleted successfully",
            403: "Cannot delete protected system role",
            404: "Role not found",
        },
        tags=["Roles"],
    )
    def delete(self, request, role_id: str):
        service = RoleService()
        try:
            ok = service.delete_role(role_id)
            if not ok:
                return ResponseBuilder.error(message="Role not found", status_code=404)
            return ResponseBuilder.success(message="Role deleted successfully")
        except ValueError as ve:
            # Protected role deletion attempt
            return ResponseBuilder.error(
                message=str(ve),
                status_code=403,
            )
        except Exception as e:
            return ResponseBuilder.error(
                message="Failed to delete role",
                data={"details": str(e)},
                status_code=500,
            )
