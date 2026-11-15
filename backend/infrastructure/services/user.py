"""
Service module for handling user business logic with enhanced role management.
Supports users with roles JOIN operations and additional filtering capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

from infrastructure.orm.repositories.roles import RoleRepository
from infrastructure.orm.repositories.user import UserRepo
from infrastructure.utils.datetime_utils import DateTimeParser

logger = logging.getLogger(__name__)


class UserService:
    """
    Service class for handling user-related business logic.
    Manages users with role information and supports enhanced filtering.
    """

    def __init__(self):
        self.repo = UserRepo()
        self.role_repo = RoleRepository()

    def get_users(
        self,
        page: int = 1,
        limit: int = 10,
        search: str = None,
        is_active: bool = None,
        role_id: str = None,
        role_type: str = None,
    ) -> Dict[str, Any]:
        """
        Retrieve users with optional filtering and pagination.
        Includes nested role information via LEFT JOIN.

        Args:
            page: Page number for pagination (default: 1)
            limit: Number of items per page (default: 10, max: 100)
            search: Search term for name/email filtering
            is_active: Filter by user active status
            role_id: Filter by specific role ID
            role_type: Filter by role type

        Returns:
            Dictionary containing paginated user data with role information:
            {
                "items": List of user dictionaries with nested role objects,
                "total": Total count of users matching filters,
                "page": Current page number,
                "limit": Items per page,
                "pages": Total number of pages
            }

        Raises:
            Exception: If database operations fail
        """
        try:
            # Validate and sanitize input parameters
            page = max(1, page) if page else 1
            limit = max(1, min(100, limit)) if limit else 10

            # Calculate offset for pagination
            offset = (page - 1) * limit

            # Get total count with filters
            total = self.repo.get_users_count(
                search=search, is_active=is_active, role_id=role_id, role_type=role_type
            )

            # Calculate total pages
            pages = (total + limit - 1) // limit if limit > 0 else 1

            # Get users with filters and pagination
            users = self.repo.get_users_with_filters(
                search=search,
                is_active=is_active,
                role_id=role_id,
                role_type=role_type,
                offset=offset,
                limit=limit,
            )

            # Process and format user data if needed
            processed_users = self._process_user_data(users)

            logger.info(
                f"Retrieved {len(processed_users)} users (page {page} of {pages}, total: {total})"
            )

            return {
                "items": processed_users,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
            }

        except Exception as e:
            logger.error(f"Error in get_users service method: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve users: {str(e)}")

    def _process_user_data(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process user data for additional formatting or business logic.
        Currently handles datetime serialization and data cleanup.

        Args:
            users: List of user dictionaries from repository

        Returns:
            List of processed user dictionaries
        """
        processed_users = []

        for user in users:
            try:
                # Create a copy to avoid modifying original data
                processed_user = dict(user)

                # Format datetime fields if they exist and are not None
                if processed_user.get("created_at"):
                    processed_user["created_at"] = self._format_datetime(
                        processed_user["created_at"]
                    )

                if processed_user.get("updated_at"):
                    processed_user["updated_at"] = self._format_datetime(
                        processed_user["updated_at"]
                    )

                # Process nested role object datetime fields
                role = processed_user.get("role")
                if role and isinstance(role, dict):
                    if role.get("created_at"):
                        role["created_at"] = self._format_datetime(role["created_at"])
                    if role.get("updated_at"):
                        role["updated_at"] = self._format_datetime(role["updated_at"])

                processed_users.append(processed_user)

            except Exception as e:
                logger.warning(f"Error processing user data: {str(e)}")
                # If processing fails, include the original user data
                processed_users.append(user)

        return processed_users

    def _format_datetime(self, dt) -> str:
        """
        Format datetime objects to ISO string format without timezone.

        Args:
            dt: Datetime object or string

        Returns:
            Formatted datetime string (YYYY-MM-DDTHH:MM:SS) without timezone
        """
        try:
            if dt is None:
                return None

            # If already a string, try to parse and reformat to ensure no timezone
            if isinstance(dt, str):
                # Parse and reformat to ensure consistent format without timezone
                parsed_dt = DateTimeParser.parse_datetime(dt)
                if parsed_dt:
                    return DateTimeParser.format_datetime_without_timezone(parsed_dt)
                # If parsing fails, return as-is
                return dt

            # If datetime object, convert to ISO format without timezone
            if hasattr(dt, "isoformat"):
                return DateTimeParser.format_datetime_without_timezone(dt)

            # Fallback to string conversion
            return str(dt)

        except Exception as e:
            logger.warning(f"Error formatting datetime {dt}: {str(e)}")
            return str(dt) if dt else None

    def assign_role(
        self, user_id: str, role_id: Optional[str], requesting_user: dict
    ) -> Dict[str, Any]:
        """
        Assign or update role for a user with comprehensive validation and audit trail.

        Args:
            user_id: ID of the user to update
            role_id: New role ID to assign (None to remove role)
            requesting_user: The user making the request (from JWT middleware)

        Returns:
            Dictionary containing updated user with audit information:
            {
                "user": Updated user dictionary with nested role information,
                "previous_role_id": Previous role ID (for audit trail),
                "updated_fields": List of fields that were updated
            }

        Raises:
            Exception: If validation fails or database operation fails
        """
        try:
            logger.info(
                f"Starting role assignment for user {user_id} by user {requesting_user.get('id', 'unknown')}"
            )

            # 1. Validate requesting user has admin permissions
            self._validate_admin_permissions(requesting_user)

            # 2. Validate target user exists and is active
            current_user = self._validate_target_user(user_id)

            # 3. Validate role if provided
            target_role = None
            if role_id:
                target_role = self._validate_target_role(role_id)

            # 4. Store previous role for audit trail
            previous_role_id = current_user.get("role_id")

            # 5. Update user's role
            update_success = self.repo.update_role(user_id, role_id)
            if not update_success:
                raise Exception(f"Failed to update role for user {user_id}")

            # 6. Get updated user with role information
            updated_user = self.repo.get_with_role(user_id)
            if not updated_user:
                raise Exception(f"Failed to retrieve updated user {user_id}")

            # 7. Process user data for response formatting
            processed_user = self._process_user_data([updated_user])[0]

            # 8. Build audit response
            audit_info = {
                "user": processed_user,
                "previous_role_id": previous_role_id,
                "updated_fields": ["role_id", "updated_at"],
            }

            logger.info(
                f"Successfully assigned role {role_id} to user {user_id} (previous: {previous_role_id})"
            )
            return audit_info

        except Exception as e:
            logger.error(
                f"Error assigning role to user {user_id}: {str(e)}", exc_info=True
            )
            raise Exception(f"Failed to assign role: {str(e)}")

    def _validate_admin_permissions(self, requesting_user: dict) -> None:
        """
        Validate that the requesting user has admin permissions.

        Args:
            requesting_user: User object from JWT middleware

        Raises:
            Exception: If user doesn't have admin permissions
        """
        if not requesting_user:
            raise Exception("Requesting user information not found")

        # Check if user is active
        if not requesting_user.get("is_active", False):
            raise Exception("Requesting user is not active")

        # Get user's role information if not already available
        if not hasattr(requesting_user, "role") or not requesting_user.role:
            # Fetch user with role information
            user_with_role = self.repo.get_with_role(requesting_user["id"])
            if not user_with_role or not user_with_role.get("role"):
                raise Exception("Requesting user does not have a role assigned")
            requesting_user_role = user_with_role.get("role")
        else:
            requesting_user_role = requesting_user.role

        # Check if user has admin role type
        role_type = requesting_user_role["type"] if requesting_user_role else None
        if role_type != "super_admin":
            raise Exception("Insufficient permissions to assign roles")

        logger.debug(f"Admin permission validated for user {requesting_user.get('id')}")

    def _validate_target_user(self, user_id: str) -> Dict[str, Any]:
        """
        Validate that the target user exists and is active.

        Args:
            user_id: ID of the user to validate

        Returns:
            User dictionary if valid

        Raises:
            Exception: If user doesn't exist or is inactive
        """
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("User not found")

        if not user.get("is_active", False):
            raise Exception("User is not active")

        logger.debug(f"Target user validated: {user_id}")
        return user

    def _validate_target_role(self, role_id: str) -> Dict[str, Any]:
        """
        Validate that the target role exists and is active.

        Args:
            role_id: ID of the role to validate

        Returns:
            Role dictionary if valid

        Raises:
            Exception: If role doesn't exist or is inactive
        """
        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise Exception("Role not found or inactive")

        if not role.get("is_active", False):
            raise Exception("Role not found or inactive")

        logger.debug(f"Target role validated: {role_id}")
        return role
