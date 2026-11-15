import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.user import UserService
from infrastructure.utils.validators import validate_user_id


class UserListView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()

    @swagger_auto_schema(
        operation_id="get_users",
        operation_summary="Get all users with optional filters and role information",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search by name/email",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "isActive",
                openapi.IN_QUERY,
                description="Filter by active status",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "role_id",
                openapi.IN_QUERY,
                description="Filter by specific role ID",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "role_type",
                openapi.IN_QUERY,
                description="Filter by role type",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number (default: 1)",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Items per page (default: 10, max: 100)",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={200: "List of users with nested role information"},
        tags=["Users"],
    )
    def get(self, request):
        try:
            # Extract query parameters with defaults
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))
            search = request.GET.get("search")
            is_active = request.GET.get("isActive")
            role_id = request.GET.get("roleId")
            role_type = request.GET.get("role_type")

            # Convert isActive string to boolean if provided
            if is_active is not None:
                is_active = str(is_active).lower() == "true"

            # Initialize service and get users with enhanced filtering
            service = UserService()
            result = service.get_users(
                page=page,
                limit=limit,
                search=search,
                is_active=is_active,
                role_id=role_id,
                role_type=role_type,
            )

            return ResponseBuilder.success(
                data=result, message="Users fetched successfully"
            )

        except ValueError as e:
            return ResponseBuilder.error(message=f"Invalid parameter value: {str(e)}")
        except Exception as e:
            return ResponseBuilder.error(message=f"Failed to fetch users: {str(e)}")


class AssignRoleView(APIView):
    """
    Controller for assigning roles to users.
    Requires admin permissions - only users with role.type == 'admin' can assign roles.
    """

    # Note: No permission_classes = [AllowAny] - this endpoint requires JWT authentication

    def __init__(self):
        super().__init__()
        self.service = UserService()

    @swagger_auto_schema(
        operation_id="assign_role_to_user",
        operation_summary="Assign or update role for a user",
        operation_description=(
            "Assigns a role to a user or removes their current role. "
            "Only admin users can perform this operation. "
            "Provide role_id to assign a role, or null to remove the current role."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "role_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Role ID to assign (null to remove role)",
                    nullable=True,
                    example="role-123-uuid",
                )
            },
            required=["role_id"],
        ),
        responses={
            200: openapi.Response(
                description="Role assigned successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=True
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Role assigned successfully",
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Updated user with role information",
                                ),
                                "previous_role_id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    nullable=True,
                                    description="Previous role ID for audit trail",
                                ),
                                "updated_fields": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    example=["role_id", "updated_at"],
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid role or validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Role not found or inactive",
                        ),
                    },
                ),
            ),
            403: openapi.Response(
                description="Insufficient permissions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Insufficient permissions to assign roles",
                        ),
                    },
                ),
            ),
            404: openapi.Response(
                description="User not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING, example="User not found"
                        ),
                    },
                ),
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Failed to assign role: Database error",
                        ),
                    },
                ),
            ),
        },
        tags=["Users"],
    )
    def patch(self, request, user_id):
        """
        Assign or update role for a specific user.

        Args:
            request: HTTP request containing role_id in body
            user_id: URL parameter - ID of user to update

        Returns:
            HTTP response with updated user and audit information
        """
        try:
            # Get JWT user from middleware
            requesting_user = getattr(request, "jwt_user", None)
            if not requesting_user:
                return ResponseBuilder.error(
                    message="Authentication required", status_code=401
                )

            # Parse request body
            try:
                body = json.loads(request.body.decode("utf-8"))
                role_id = body.get("role_id")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return ResponseBuilder.error(
                    message="Invalid JSON in request body", status_code=400
                )

            # Validate required field presence (role_id can be null)
            if "role_id" not in body:
                return ResponseBuilder.error(
                    message="role_id field is required (can be null to remove role)",
                    status_code=400,
                )

            # Note: user_id validation is now handled at URL routing level
            # via custom UUID converter in urls.py

            # Call service layer
            result = self.service.assign_role(
                user_id=user_id.strip(),
                role_id=role_id.strip() if role_id else None,
                requesting_user=requesting_user,
            )

            return ResponseBuilder.success(
                data=result, message="Role assigned successfully"
            )

        except Exception as e:
            error_message = str(e)

            # Map specific exceptions to appropriate HTTP status codes
            if "not found" in error_message.lower():
                status = 404
            elif "insufficient permissions" in error_message.lower():
                status = 403
            elif "not active" in error_message.lower():
                status = 400
            elif "invalid" in error_message.lower():
                status = 400
            else:
                status = 500

            return ResponseBuilder.error(message=error_message, status_code=status)


class AssignRoleController(APIView):
    """
    Controller for assigning roles to users.
    Requires admin permissions - only users with role.type == 'admin' can assign roles.
    """

    # Note: No permission_classes = [AllowAny] - this endpoint requires JWT authentication

    def __init__(self):
        super().__init__()
        self.service = UserService()

    permission_classes = []  # using middleware-only check below

    @swagger_auto_schema(
        operation_id="assign_user_role",
        operation_summary="Assign role to a user",
        operation_description=(
            "Assigns a role to a user or removes their current role. "
            "Only admin users can perform this operation. "
            "Provide roleId to assign a role, or null to remove the current role."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "roleId": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Role ID to assign (null to remove role)",
                    nullable=True,
                    example="role-123-uuid",
                ),
                "userId": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User ID to assign role to",
                    example="user-123-uuid",
                )
            },
            required=["roleId", "userId"],
        ),
        responses={
            200: openapi.Response(
                description="Role assigned successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=True
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Role assigned successfully",
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Updated user with role information",
                                ),
                                "previous_role_id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    nullable=True,
                                    description="Previous role ID for audit trail",
                                ),
                                "updated_fields": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    example=["role_id", "updated_at"],
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid role or validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Role not found or inactive",
                        ),
                    },
                ),
            ),
            403: openapi.Response(
                description="Insufficient permissions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Insufficient permissions to assign roles",
                        ),
                    },
                ),
            ),
            404: openapi.Response(
                description="User not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING, example="User not found"
                        ),
                    },
                ),
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, example=False
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Failed to assign role: Database error",
                        ),
                    },
                ),
            ),
        },
        tags=["Users"],
    )
    def post(self, request):
        requesting_user = getattr(request, "jwt_user", None)
        if not requesting_user:
            return ResponseBuilder.error(
                message="Authentication required", status_code=401
            )

        try:
            # Parse request body
            body = json.loads(request.body.decode("utf-8"))
            role_id = body.get("roleId")
            user_id = body.get("userId")

            # Validate required field presence (role_id can be null)
            if "roleId" not in body:
                return ResponseBuilder.error(
                    message="roleId field is required (can be null to remove role)",
                    status_code=400,
                )

            if "userId" not in body:
                return ResponseBuilder.error(
                    message="userId field is required (can be null to remove role)",
                    status_code=400,
                )

            # Note: user_id validation is now handled at URL routing level
            # via custom UUID converter in urls.py

            # Call service layer
            result = self.service.assign_role(
                user_id=user_id.strip(),
                role_id=role_id.strip() if role_id else None,
                requesting_user=requesting_user,
            )

            return ResponseBuilder.success(
                data=result, message="Role assigned successfully"
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            return ResponseBuilder.error(
                message="Invalid JSON in request body", status_code=400
            )

        except Exception as e:
            error_message = str(e)

            # Map specific exceptions to appropriate HTTP status codes
            if "not found" in error_message.lower():
                status = 404
            elif "insufficient permissions" in error_message.lower():
                status = 403
            elif "not active" in error_message.lower():
                status = 400
            elif "invalid" in error_message.lower():
                status = 400
            else:
                status = 500

            return ResponseBuilder.error(message=error_message, status_code=status)
