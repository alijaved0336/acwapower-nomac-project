"""
Roles service module for handling business logic related to roles management.
"""

import datetime
import logging
import math
import uuid
from typing import Any, Dict, List, Optional

from infrastructure.orm.repositories.roles import RoleRepository
from .user import UserRepo

logger = logging.getLogger(__name__)


class RoleService:
    """
    Service class for managing role-related business logic.
    Handles data processing, pagination, and coordination between controller and repository layers.
    """

    def __init__(self):
        """Initialize the RoleService with a repository instance."""
        self.user_repo = UserRepo()
        self.repo = RoleRepository()
        pass  # Repository will be created per operation

    def _get_repo(self) -> RoleRepository:
        """
        Get a fresh repository instance for each operation.
        This follows the pattern established in the codebase for connection management.

        Returns:
            RoleRepository: A new repository instance
        """
        return RoleRepository()

    def get_roles(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        cluster: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve roles with filtering, searching, and pagination.

        Args:
            page: Page number for pagination (1-indexed)
            limit: Number of items per page
            search: Search term for filtering by name or description
            role_type: Filter by role type
            is_active: Filter by active status
            cluster: Filter by cluster association

        Returns:
            Dict containing:
                - items: List of role dictionaries
                - total: Total number of roles matching filters
                - page: Current page number
                - limit: Items per page
                - pages: Total number of pages

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info(
                f"Service: Fetching roles with filters - page: {page}, limit: {limit}, "
                f"search: {search}, type: {role_type}, is_active: {is_active}, cluster: {cluster}"
            )

            # Validate pagination parameters
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10
            elif limit > 100:
                limit = 100

            # Calculate offset for pagination
            offset = (page - 1) * limit

            # Get repository instance
            repo = self._get_repo()

            # Fetch roles from repository with filters
            roles_data = repo.get_roles_with_filters(
                search=search,
                role_type=role_type,
                is_active=is_active,
                cluster=cluster,
                offset=offset,
                limit=limit,
            )

            # Get total count for pagination metadata
            total_count = repo.get_roles_count(
                search=search, role_type=role_type, is_active=is_active, cluster=cluster
            )
            
            # Process the roles data
            processed_roles = self._process_roles_data(roles_data)

            # Calculate pagination metadata
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

            # Build response structure
            response = {
                "items": processed_roles,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": total_pages,
            }

            logger.info(
                f"Service: Successfully fetched {len(processed_roles)} roles out of {total_count} total"
            )

            return response

        except Exception as e:
            logger.error(f"Service: Error fetching roles - {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch roles: {str(e)}")


    def _format_timestamp(self, timestamp) -> str:
        """
        Format timestamp to ISO 8601 string format.

        Args:
            timestamp: Timestamp value (string, datetime, or None)

        Returns:
            Formatted timestamp string or original value if formatting fails
        """
        if not timestamp:
            return None

        try:
            # If it's already a string in the correct format, return as is
            if isinstance(timestamp, str):
                return timestamp

            # If it's a datetime object, format it
            from datetime import datetime

            if hasattr(timestamp, "isoformat"):
                return timestamp.isoformat() + "Z"

            # Try to parse and reformat if it's a string in different format
            if isinstance(timestamp, str):
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return dt.isoformat() + "Z"

            return str(timestamp)

        except Exception as e:
            logger.debug(f"Service: Could not format timestamp {timestamp}: {str(e)}")
            return str(timestamp) if timestamp else None

    def get_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_by_id(role_id)

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_by_name(name)

    # ---------- DELETE ----------

    # Protected system roles that cannot be deleted
    PROTECTED_ROLES = ["User", "Super Admin"]

    def delete_role(self, role_id: str) -> bool:
        """
        Delete a role. If any users are assigned this role,
        reassign them to the default 'user' role before deletion.
        
        Protected system roles (User, Admin, Super Admin) cannot be deleted.
        """

        # Step 1: Verify the role exists
        role = self.repo.get_by_id(role_id)
        if not role:
            logger.warning(f"Role with ID {role_id} not found.")
            return False
        
        # Step 2: Check if role is protected
        role_name = role.get("name", "")
        if role_name in self.PROTECTED_ROLES:
            raise ValueError(
                f"Cannot delete protected system role '{role_name}'. "
                f"Protected roles: {', '.join(self.PROTECTED_ROLES)}"
            )
        
        # Step 3: Get the default role (e.g., 'user') for reassignment
        default_role = self.repo.get_by_name("User")
        if not default_role:
            raise ValueError("Default role not found. Cannot reassign users.")

        # Step 4: Find users who currently have this role and reassign them
        users_with_role = self.user_repo.get_users_by_role_id(role_id)
        if users_with_role:
            logger.info(
                f"Found {len(users_with_role)} user(s) with role '{role['name']}'. "
                f"Reassigning to default role '{default_role['name']}'."
            )

            failed_reassignments = []
            for user in users_with_role:
                try:
                    self.user_repo.update_role(user["id"], default_role["id"])
                except Exception as e:
                    logger.error(f"Failed to update role for user {user['id']}: {str(e)}")
                    failed_reassignments.append({
                        "user_id": user["id"],
                        "email": user.get("email", "unknown"),
                        "error": str(e)
                    })
            
            # If any reassignments failed, abort deletion to prevent orphaned users
            if failed_reassignments:
                failed_emails = [f["email"] for f in failed_reassignments]
                raise ValueError(
                    f"Cannot delete role '{role['name']}': Failed to reassign {len(failed_reassignments)} user(s). "
                    f"Users: {', '.join(failed_emails)}. Please resolve these issues before retrying."
                )

        # Step 5: Delete the role itself (only after all reassignments succeed)
        self.repo.delete_row(role_id)
        logger.info(f"Deleted role '{role['name']}' (ID: {role_id}) successfully.")

        return True



   
    # ---------- Updated requirements ----------

    # ---------- CREATE----------
    def create_role(self, payload: Dict[str, Any]) -> str:
        # Required fields
        for f in ("name", "type"):
            if not payload.get(f):
                raise ValueError(f"Field '{f}' is required.")

        # Name uniqueness
        existing = self.get_by_name(payload["name"])
        if existing:
            raise ValueError(f"Role with name '{payload['name']}' already exists.")

        # Normalize clusters (new format: [{"name": "KSA", "sites": [...]}, ...])
        row = dict(payload)
        row["clusters"] = self._normalize_clusters(row.get("clusters"))

        # Set defaults
        row.setdefault("id", str(uuid.uuid4()))
        now = datetime.datetime.now(datetime.timezone.utc)
        row.setdefault("created_at", now)
        row["updated_at"] = now
        row.setdefault("is_active", True)

        # Persist
        self.repo.insert_row(row)
        return row["id"]
    

    # ---------- UPDATE ----------
    def update_role(
        self, role_id: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        # If changing name, enforce uniqueness
        if "name" in payload and payload["name"]:
            existing = self.get_by_name(payload["name"])
            if existing and existing["id"] != role_id:
                raise ValueError(f"Role with name '{payload['name']}' already exists.")

        updates = dict(payload)

        # Normalize clusters if provided
        if "clusters" in updates:
            updates["clusters"] = self._normalize_clusters(updates.get("clusters"))

        # Always bump updated_at
        updates["updated_at"] = datetime.datetime.now(datetime.timezone.utc)

        return self.repo.update_row(role_id, updates)
    

    # ---------- HELPERS ----------
    def _normalize_clusters(self, clusters: Any) -> List[Dict[str, Any]]:
        """
        Ensure clusters are stored in the format:
        [
            {"name": "KSA", "sites": ["Rabigh3", "Jubail-Jazlah", "STPC"]},
            {"name": "MEASEA", "sites": ["UAQ"]}
        ]
        """

        if not clusters:
            return []

        # Define default mapping (for migration / fallback)
        cluster_sites_map = {
            "KSA": ["Rabigh3", "Jubail-Jazlah", "STPC"],
            "MEASEA": ["UAQ"]
        }

        normalized = []
        for c in clusters:
            # Case 1: Already in new format
            if isinstance(c, dict) and "name" in c and "sites" in c:
                normalized.append({"name": c["name"], "sites": c.get("sites", [])})

            # Case 2: Old format (string cluster)
            elif isinstance(c, str):
                normalized.append({
                    "name": c,
                    "sites": cluster_sites_map.get(c, [])
                })

            else:
                raise ValueError(f"Invalid cluster format: {c}")

        return normalized
    

    def _process_roles_data(
        self, roles_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process and transform raw role data from the repository.

        Args:
            roles_data: List of role dictionaries from repository

        Returns:
            List of processed role dictionaries with normalized clusters
        """

        processed_roles = []

        for role in roles_data:
            try:
                clusters = []
                clusters_raw = role.get("clusters", [])

                if clusters_raw is not None:
                    for c in clusters_raw:
                        if not c:
                            continue

                        c = str(c).strip()

                        # Case 1: "{KSA, [Rabigh3, Jubail-Jazlah]}"
                        if c.startswith("{") and c.endswith("}"):
                            try:
                                inner = c.strip("{}")
                                parts = [p.strip() for p in inner.split(",", 1)]
                                cluster_name = parts[0]
                                sites = []
                                if len(parts) > 1 and "[" in parts[1]:
                                    sites_str = parts[1].strip(" []")
                                    sites = [s.strip() for s in sites_str.split(",") if s.strip()]
                                clusters.append({"name": cluster_name, "sites": sites})
                            except Exception:
                                clusters.append({"name": c, "sites": []})

                        # Case 2: "Cluster: KSA" → remove prefix
                        elif c.startswith("Cluster: "):
                            clusters.append({"name": c.replace("Cluster: ", "").strip(), "sites": []})

                        # Case 3: Plain cluster string
                        else:
                            clusters.append({"name": c, "sites": []})

                # Format timestamps
                created_at = role.get("created_at")
                updated_at = role.get("updated_at")
                if created_at:
                    created_at = self._format_timestamp(created_at)
                if updated_at:
                    updated_at = self._format_timestamp(updated_at)

                processed_roles.append(
                    {
                        "id": role.get("id"),
                        "name": role.get("name"),
                        "type": role.get("type"),
                        "description": role.get("description", ""),
                        "is_active": bool(role.get("is_active", True)),
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "clusters": clusters,
                    }
                )

            except Exception as e:
                logger.warning(
                    f"Service: Error processing role {role.get('id', 'unknown')}: {str(e)}",
                    exc_info=True,
                )
                processed_roles.append({
                    "id": role.get("id"),
                    "name": role.get("name"),
                    "clusters": [],
                    "error": "Failed to process role fully"
                })

        return processed_roles
