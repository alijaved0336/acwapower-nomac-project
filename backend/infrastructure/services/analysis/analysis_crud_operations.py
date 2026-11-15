"""
Analysis CRUD Operations Module
Handles Create, Read, Update, Delete operations for analysis entities.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.orm.repositories.analysis import AnalysisRepo
from infrastructure.orm.repositories.user import UserRepo

logger = logging.getLogger(__name__)

# Role type constant for super admin authorization
SUPER_ADMIN_ROLE_TYPE = "super_admin"


class AnalysisCrudOperations:
    """Handles CRUD operations for analysis entities"""

    def __init__(self):
        pass

    def _get_repo(self) -> AnalysisRepo:
        """Get a fresh repository instance for each operation"""
        return AnalysisRepo()

    def _get_widgets_repo(self) -> "WidgetsRepository":
        """Get a fresh WidgetsRepository instance"""
        from infrastructure.orm.repositories.widgets import WidgetsRepository

        return WidgetsRepository()

    def _check_super_admin_status(
        self,
        authenticated_user_id: str,
        authenticated_user_email: str = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if authenticated user is an active super admin.

        Args:
            authenticated_user_id: User ID from JWT
            authenticated_user_email: User email from JWT (optional)

        Returns:
            Tuple of (is_super_admin: bool, role_type: str | None)

        Note:
            On error, safely defaults to (False, None) for fail-safe behavior.
        """
        user_repo = UserRepo()
        is_super_admin = False
        role_type = None

        try:
            # Try ID-based lookup first (JWT sub is authoritative)
            user_with_role = None
            if authenticated_user_id:
                user_with_role = user_repo.get_with_role(authenticated_user_id)

            # Fallback to email-based lookup
            if not user_with_role and authenticated_user_email:
                user_with_role = user_repo.find_by_email(authenticated_user_email)

            # Check if user has super_admin role AND is active
            if (
                user_with_role
                and user_with_role.get("role")
                and user_with_role.get("is_active")
            ):
                role_type = user_with_role["role"].get("type")
                is_super_admin = role_type == SUPER_ADMIN_ROLE_TYPE

                logger.debug(
                    f"Role check for user {authenticated_user_id}: "
                    f"role_type={role_type}, is_super_admin={is_super_admin}, is_active=True"
                )
            elif user_with_role and not user_with_role.get("is_active"):
                logger.warning(
                    f"SECURITY: Inactive user {authenticated_user_id} ({authenticated_user_email}) "
                    f"attempted privileged operation - treating as regular user"
                )

        except Exception as role_error:
            logger.error(
                f"CRITICAL: Role check failed for user {authenticated_user_id} ({authenticated_user_email}): "
                f"{type(role_error).__name__}: {str(role_error)}. "
                f"Treating user as regular user (fail-safe mode).",
                exc_info=True
            )

        return is_super_admin, role_type

    def get_analysis(
        self,
        user_id: str = None,
        page: int = 1,
        limit: int = 10,
        name: str = None,
        from_date: str = None,
        to_date: str = None,
        visibility: str = None,
    ):
        """Get analysis with filters and pagination"""
        try:
            # Convert date strings to datetime objects for database queries
            from_date_obj = None
            to_date_obj = None

            if from_date:
                try:
                    # Use native datetime parsing instead of pandas
                    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                except Exception:
                    from_date_obj = None

            if to_date:
                try:
                    # Use native datetime parsing instead of pandas
                    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
                except Exception:
                    to_date_obj = None

            # Use the filtered query method from repository
            repo = self._get_repo()
            analysisDf = repo.get_analysis_with_filters(
                user=user_id,
                name=name,
                from_date=from_date_obj,
                to_date=to_date_obj,
                visibility=visibility,
            )

            # Pagination - analysisDf is a List[Dict], not a pandas DataFrame
            total = len(analysisDf)
            pages = (total + limit - 1) // limit if limit > 0 else 1

            start = (page - 1) * limit
            end = start + limit
            items = analysisDf[start:end]  # Use native Python list slicing

            result_data = {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
            }

            return ResponseBuilder.success(data=result_data)
        except Exception as e:
            return ResponseBuilder.error(message=f"Failed to retrieve analysis: {str(e)}")

    def get_analysis_with_access_control(
        self,
        authenticated_user_id: str,
        authenticated_user_email: str = None,
        authenticated_user_name: str = None,
        user_id: str = None,
        page: int = 1,
        limit: int = 10,
        name: str = None,
        from_date: str = None,
        to_date: str = None,
        visibility: str = None,
    ):
        """Get analysis with access control.

        Access Control:
        - Super admins (role.type = "super_admin", is_active = true): Can view ALL analyses
        - Regular users: Can only see their own analyses + others' public analyses
        """
        try:
            if not authenticated_user_id:
                return ResponseBuilder.error(message="Authentication required", status_code=401)

            # STEP 1: Fetch user role to check if super admin
            is_super_admin, role_type = self._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            if is_super_admin:
                logger.info(
                    f"Super admin {authenticated_user_id} ({authenticated_user_email}) "
                    f"is viewing all analyses including private ones"
                )

            # Convert date strings to datetime objects for database queries
            from_date_obj = None
            to_date_obj = None

            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                except Exception:
                    from_date_obj = None

            if to_date:
                try:
                    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
                except Exception:
                    to_date_obj = None

            # Use the repository with access control
            repo = self._get_repo()
            analysisDf = repo.get_analysis_with_access_control(
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                user_id=user_id,
                name=name,
                from_date=from_date_obj,
                to_date=to_date_obj,
                visibility=visibility,
                is_super_admin=is_super_admin,
            )

            if analysisDf:

                user_repo = UserRepo()

                # Create a mapping to store user_id/email -> name
                user_name_map = {}

                # First, add authenticated user to the map
                if authenticated_user_id and authenticated_user_name:
                    user_name_map[authenticated_user_id] = authenticated_user_name
                if authenticated_user_email and authenticated_user_name:
                    user_name_map[authenticated_user_email] = authenticated_user_name

                # Collect unique user IDs that need name lookup (where user_name is null)
                user_ids_to_fetch = set()
                for item in analysisDf:
                    item_user_id = item.get("user_id")
                    # Only fetch if user_name is null and user_id exists and not already in map
                    if (
                        not item.get("user_name")
                        and item_user_id
                        and item_user_id not in user_name_map
                    ):
                        user_ids_to_fetch.add(item_user_id)

                # Fetch user names from database
                if user_ids_to_fetch:
                    logger.info(f"Fetching names for {len(user_ids_to_fetch)} users from database")
                    for user_identifier in user_ids_to_fetch:
                        try:
                            # Try to determine if it's an email or UUID
                            user_data = None

                            if "@" in str(user_identifier):
                                # It's an email
                                user_data = user_repo.find_by_email(user_identifier)
                            else:
                                # It's likely a UUID
                                user_data = user_repo.get_by_id(user_identifier)

                            if user_data and user_data.get("name"):
                                # Add both id and email to the map if available
                                if user_data.get("id"):
                                    user_name_map[user_data["id"]] = user_data["name"]
                                if user_data.get("email"):
                                    user_name_map[user_data["email"]] = user_data["name"]

                        except Exception as e:
                            logger.warning(f"Failed to fetch user data for {user_identifier}: {e}")
                            continue

                # Populate user_name for all items
                for item in analysisDf:
                    if not item.get("user_name") and item.get("user_id"):
                        item_user_id = item.get("user_id")
                        if item_user_id in user_name_map:
                            item["user_name"] = user_name_map[item_user_id]
                            logger.debug(
                                f"Populated user_name for analysis {item.get('id')}: {user_name_map[item_user_id]}"
                            )

            # Pagination - analysisDf is a List[Dict], not a pandas DataFrame
            total = len(analysisDf)
            pages = (total + limit - 1) // limit if limit > 0 else 1

            start = (page - 1) * limit
            end = start + limit
            items = analysisDf[start:end]

            result_data = {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
            }

            return ResponseBuilder.success(data=result_data)
        except Exception as e:
            return ResponseBuilder.error(message=f"Failed to retrieve analysis: {str(e)}")

    def get_analysis_by_id_with_access_control(
        self,
        analysis_id: int,
        authenticated_user_id: str,
        authenticated_user_email: str = None,
        authenticated_user_name: str = None,
    ):
        """Get single analysis by ID with access control.

        Access Control:
        - Super admins (role.type = "super_admin", is_active = true): Can view ANY analysis
        - Regular users: Can only view their own analyses + others' public analyses
        """
        try:
            if not authenticated_user_id:
                return ResponseBuilder.error(message="Authentication required", status_code=401)

            # STEP 1: Fetch user role to check if super admin
            is_super_admin, role_type = self._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            if is_super_admin:
                logger.info(
                    f"Super admin {authenticated_user_id} ({authenticated_user_email}) "
                    f"is viewing analysis {analysis_id}"
                )

            # Use the repository with access control
            repo = self._get_repo()
            analysis = repo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin,
            )

            if not analysis:
                return ResponseBuilder.error(
                    message="Analysis not found or access denied", status_code=403
                )

            # NEW: Populate user_name if null by fetching from User table
            if (
                isinstance(analysis, dict)
                and not analysis.get("user_name")
                and analysis.get("user_id")
            ):
                from infrastructure.orm.repositories.user import UserRepo

                user_repo = UserRepo()
                item_user_id = analysis.get("user_id")

                try:
                    user_data = None

                    # First check if this is the authenticated user
                    if (
                        item_user_id == authenticated_user_id
                        or item_user_id == authenticated_user_email
                    ):
                        if authenticated_user_name:
                            analysis["user_name"] = authenticated_user_name
                    else:
                        # Fetch from database
                        if "@" in str(item_user_id):
                            # It's an email
                            user_data = user_repo.find_by_email(item_user_id)
                        else:
                            # It's likely a UUID
                            user_data = user_repo.get_by_id(item_user_id)

                        if user_data and user_data.get("name"):
                            analysis["user_name"] = user_data["name"]

                except Exception as e:
                    logger.warning(f"Failed to fetch user name for analysis {analysis_id}: {e}")

            return ResponseBuilder.success(data=analysis)
        except Exception as e:
            return ResponseBuilder.error(message=f"Failed to retrieve analysis: {str(e)}")

    def create_analysis(self, analysis_data: Dict):
        """Create a new analysis"""
        try:
            # Extract values from analysis_data
            user_id = analysis_data.get("user_id")
            name = analysis_data.get("name")
            asset_type = analysis_data.get("asset_type")
            type_value = analysis_data.get("type_value")
            visibility = analysis_data.get("visibility", "private")

            # Prepare data for creation
            data = {
                "user_id": user_id,
                "name": name,
                "asset_type": asset_type,
                "type": type_value,  # Map type_value to type
                "visibility": visibility,
                "applied_date_filter": self._serialize_applied_date_filter(
                    analysis_data.get("applied_date_filter")
                ),
            }

            # Use provided ID or generate UUID as string
            data["id"] = analysis_data.get("id") or str(uuid.uuid4())

            # Ensure created_at is set
            data["created_at"] = data.get(
                "created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            )

            repo = self._get_repo()
            created_analysis = repo.create(data)

            return {
                "success": True,
                "message": "Analysis created successfully",
                "data": created_analysis,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to create analysis: {str(e)}"}

    def update_analysis(self, analysis_data: Dict):
        """Update an existing analysis"""
        try:
            # Extract analysis_id and other fields from analysis_data
            analysis_id = analysis_data.get("analysis_id")
            user_id = analysis_data.get("user_id")
            name = analysis_data.get("name")
            asset_type = analysis_data.get("asset_type")
            type_value = analysis_data.get("type_value")
            visibility = analysis_data.get("visibility")
            applied_date_filter = analysis_data.get("applied_date_filter")

            if not analysis_id:
                return {"success": False, "message": "Analysis ID is required for update"}

            repo = self._get_repo()

            # Check if analysis exists
            existing_analysis = repo.get_by_id(analysis_id)
            if not existing_analysis:
                return {"success": False, "message": "Analysis not found"}

            # Prepare update data (only include fields that are provided)
            update_data = {}

            if user_id is not None:
                update_data["user_id"] = user_id
            if name is not None:
                update_data["name"] = name
            if asset_type is not None:
                update_data["asset_type"] = asset_type
            if type_value is not None:
                update_data["type"] = type_value  # Map type_value to type
            if visibility is not None:
                update_data["visibility"] = visibility
            if applied_date_filter is not None:
                update_data["applied_date_filter"] = self._serialize_applied_date_filter(
                    applied_date_filter
                )

            # Set updated_at timestamp
            update_data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # Update the analysis
            updated_analysis = repo.update_by_id(analysis_id, update_data)

            return {
                "success": True,
                "message": "Analysis updated successfully",
                "data": updated_analysis,
            }

        except Exception as e:
            return {"success": False, "message": f"Failed to update analysis: {str(e)}"}

    def _serialize_applied_date_filter(self, applied_date_filter):
        """Helper method to serialize applied_date_filter to JSON string if it's a dict"""
        if applied_date_filter is None:
            return None
        if isinstance(applied_date_filter, dict):
            import json

            return json.dumps(applied_date_filter)
        return applied_date_filter

    def delete_analysis(
        self, analysis_id: str, authenticated_user_id: str, authenticated_user_email: str = None
    ):
        """
        Delete analysis and cascade delete all associated widgets.

        IMPORTANT CONSTRAINTS:
        - Databricks doesn't support transactions
        - Deletion order: Analysis FIRST, then widgets (minimizes data integrity risk)
        - Authorization enforced: Owner OR super admin can delete

        Authorization Rules:
        - Analysis owner can always delete their own analysis
        - Super admin (role.type = "super_admin") can delete ANY analysis
        - Regular users cannot delete analyses they don't own

        Args:
            analysis_id: Analysis ID to delete (UUID string)
            authenticated_user_id: ID of authenticated user (for authorization)
            authenticated_user_email: Email of authenticated user (optional fallback)

        Returns:
            Dict: {"success": bool, "message": str, "data": dict, "status_code": int}
        """
        try:
            repo = self._get_repo()

            # STEP 1: Fetch authenticated user's role to check for super admin permissions
            # IMPORTANT: Must check BEFORE fetching analysis to pass is_super_admin flag
            is_super_admin, role_type = self._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            # STEP 2: Verify analysis exists and user has permission to delete
            analysis = repo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not analysis:
                return {
                    "success": False,
                    "message": "Analysis not found or access denied",
                    "status_code": 404,
                }

            if is_super_admin:
                logger.debug(
                    f"User {authenticated_user_id} ({authenticated_user_email}) "
                    f"has super_admin role and is active - can delete any analysis"
                )

            # STEP 3: Verify user is the owner OR is a super admin
            user_id_match = analysis.get("user_id") == authenticated_user_id
            email_match = (
                authenticated_user_email and analysis.get("user_id") == authenticated_user_email
            )

            # Authorization: Allow if user is owner OR super admin
            if not (user_id_match or email_match or is_super_admin):
                logger.warning(
                    f"Unauthorized deletion attempt: user {authenticated_user_id} "
                    f"(role: {role_type if role_type else 'none'}) "
                    f"tried to delete analysis {analysis_id} owned by {analysis.get('user_id')}"
                )
                return {
                    "success": False,
                    "message": "You do not have permission to delete this analysis",
                    "status_code": 403,
                }

            # STEP 4: Audit logging for super admin deletions
            # Log when super admin deletes someone else's analysis (not their own)
            if is_super_admin and not (user_id_match or email_match):
                logger.info(
                    f"SUPER ADMIN DELETION: User {authenticated_user_id} "
                    f"({authenticated_user_email}) with super_admin role "
                    f"deleted analysis {analysis_id} owned by {analysis.get('user_id')} "
                    f"(analysis name: '{analysis.get('name', 'N/A')}')"
                )

            # STEP 5: Delete analysis record FIRST (safer for data integrity)
            # If this fails, no data is modified
            success = repo.delete_by_id(analysis_id)
            if not success:
                return {
                    "success": False,
                    "message": "Failed to delete analysis",
                    "status_code": 500,
                }

            logger.info(f"Successfully deleted analysis {analysis_id}")

            # STEP 6: Clean up widgets (best-effort)
            # If this fails, analysis is already deleted (acceptable state)
            try:
                widgets_repo = self._get_widgets_repo()
                widgets_repo.delete_all_widgets_for_analysis(analysis_id)
                logger.info(f"Successfully deleted widgets for analysis {analysis_id}")

                return {
                    "success": True,
                    "message": "Analysis and associated widgets deleted successfully",
                }

            except Exception as widget_error:
                # Analysis is deleted, but widgets remain (orphaned)
                # This is acceptable - orphaned widgets can be cleaned up later
                logger.error(
                    f"Failed to delete widgets for analysis {analysis_id}: {str(widget_error)}",
                    exc_info=True,
                )
                return {
                    "success": True,
                    "message": "Analysis deleted successfully, but some widgets may remain",
                    "data": {"orphaned_widgets_warning": True},
                }

        except Exception as e:
            logger.error(f"Failed to delete analysis {analysis_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to delete analysis: {str(e)}",
                "status_code": 500,
            }
