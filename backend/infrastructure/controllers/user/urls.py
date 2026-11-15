import logging
import re
import uuid

from django.http import JsonResponse
from django.urls import path, re_path
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.controllers.user.controller import (AssignRoleController,
                                                        AssignRoleView,
                                                        UserListView)

# Set up logging
logger = logging.getLogger(__name__)


class SecurityBlockView(APIView):
    """
    Security view to detect and block path traversal attacks and malicious patterns.
    This view handles requests that contain suspicious patterns that could be used
    for security exploits like path traversal, XSS attempts, or injection attacks.
    """

    permission_classes = [AllowAny]
    # Hide from Swagger documentation
    swagger_schema = None

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle all HTTP methods and log security violations.
        """
        # Get the path parameter from the URL (first positional argument)
        path_param = args[0] if args else ""

        # Log security violation for monitoring
        logger.warning(
            f"Security violation detected: {request.method} {request.path} "
            f"- Suspicious pattern in parameter: '{path_param}'"
        )

        return ResponseBuilder.error(
            message=f"SECURITY BLOCK TRIGGERED for parameter: '{path_param}'",
            status_code=400,
        )

    def get(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)


class UUIDValidationView(APIView):
    """
    Enhanced view to handle invalid UUID formats including empty strings.
    This view provides proper validation errors before JWT authentication
    and is marked as public to bypass the JWT middleware.
    """

    permission_classes = [AllowAny]
    # Hide from Swagger documentation
    swagger_schema = None

    def _handle_invalid_uuid(self, user_id_param):
        """
        Centralized method to handle invalid UUID validation with specific error messages.
        """
        if not user_id_param or user_id_param.strip() == "":
            message = "user_id parameter cannot be empty"
        else:
            message = f"UUID VALIDATION REACHED - Invalid user_id format: '{user_id_param}'. Must be a valid UUID."

        return ResponseBuilder.error(message=message, status_code=400)

    def patch(self, request, *args, **kwargs):
        """Handle PATCH requests with invalid UUIDs."""
        user_id_param = args[0] if args else ""
        return self._handle_invalid_uuid(user_id_param)

    def get(self, request, *args, **kwargs):
        """Handle GET requests with invalid UUIDs."""
        user_id_param = args[0] if args else ""
        return self._handle_invalid_uuid(user_id_param)

    def post(self, request, *args, **kwargs):
        """Handle POST requests with invalid UUIDs."""
        user_id_param = args[0] if args else ""
        return self._handle_invalid_uuid(user_id_param)

    def put(self, request, *args, **kwargs):
        """Handle PUT requests with invalid UUIDs."""
        user_id_param = args[0] if args else ""
        return self._handle_invalid_uuid(user_id_param)

    def delete(self, request, *args, **kwargs):
        """Handle DELETE requests with invalid UUIDs."""
        user_id_param = args[0] if args else ""
        return self._handle_invalid_uuid(user_id_param)


def is_valid_uuid(uuid_string):
    """Check if string is valid UUID format"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


urlpatterns = [
    path("users/", UserListView.as_view(), name="user_list"),
    path(
        "users/assign-user-role/",
        AssignRoleController.as_view(),
        name="assign-user-role",
    ),
    # SECURITY PRIORITY 1: Block path traversal attacks and malicious patterns
    # This pattern catches dangerous characters and patterns before they can be processed
    re_path(
        r"^users/(BLOCKED)/role/$",
        SecurityBlockView.as_view(),
        name="security_block_test",
    ),
    re_path(
        r"^users/(.*\.\..*|.*\/\/.*|.*[<>'\"%;)(\\&+].*|.*%2e.*|.*%2f.*)/role/$",
        SecurityBlockView.as_view(),
        name="security_block",
    ),
    # PRIORITY 2: Valid UUID pattern - routes to actual controller
    re_path(
        r"^users/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/role/$",
        AssignRoleView.as_view(),
        name="assign_role",
    ),
    # PRIORITY 3: Catch-all pattern for invalid UUIDs and empty strings
    # This catches any /users/.../role/ that doesn't match valid UUID pattern
    # Uses (.*) to catch empty strings and invalid formats
    re_path(
        r"^users/(.*)/role/$",
        UUIDValidationView.as_view(),
        name="invalid_uuid_validation",
    ),
]
