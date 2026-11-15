"""
Analysis List Handler
Handles listing and creating analysis reports.
"""
import logging
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from infrastructure.services.analysis.analysis_base_service import AnalysisService
from infrastructure.applevel.responseBuilder import ResponseBuilder


class AnalysisListView(APIView):
    """Handles analysis listing and creation operations"""
    logger = logging.getLogger(__name__)
    # Rely on custom JWT middleware for auth; disable DRF auth to avoid 401 "Authentication credentials were not provided."
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_id="get_analysis",
        operation_summary="Get all active analysis reports (Super Admins see all)",
        operation_description="""
Retrieve analysis reports with role-based access control.

**Access Control**:
- **Super Admins** (role.type = "super_admin", is_active = true): Can view ALL analyses (public and private)
- **Regular Users**: Can view their own analyses + public analyses from others

**Filtering**: All query parameters work for both user types.
""",
        manual_parameters=[
            openapi.Parameter(
                "user_id",
                openapi.IN_QUERY,
                description="Filter by user ID",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Items per page",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "name",
                openapi.IN_QUERY,
                description="Search by analysis name",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Filter from date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="Filter to date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "visibility",
                openapi.IN_QUERY,
                description="Filter by visibility (private/public)",
                type=openapi.TYPE_STRING,
                enum=["private", "public"],
            ),
        ],
        responses={200: "List of analysis reports"},
    )
    def get(self, request):
        # Extract authenticated user from JWT middleware
        authenticated_user_id = None
        authenticated_user_email = None
        authenticated_user_name = None
        
        self.logger.debug(
            "Analysis GET auth context: has_jwt_user=%s has_jwt_payload=%s headers_auth=%s",
            hasattr(request, 'jwt_user') and bool(getattr(request, 'jwt_user', None)),
            hasattr(request, 'jwt_payload') and bool(getattr(request, 'jwt_payload', None)),
            bool(request.headers.get('Authorization')),
        )
        if hasattr(request, 'jwt_user') and request.jwt_user:
            authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
            authenticated_user_email = request.jwt_user.get('email')
            authenticated_user_name = request.jwt_user.get('name') 
        elif hasattr(request, 'jwt_payload') and request.jwt_payload:
            authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
            authenticated_user_email = request.jwt_payload.get('email')
            authenticated_user_name = request.jwt_payload.get('name') 

        if not authenticated_user_id:
            self.logger.warning("Analysis GET unauthorized: missing authenticated_user_id")
            return ResponseBuilder.error(message="Authentication required", status_code=401)

        # Extract query parameters
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        name = request.query_params.get("name")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        visibility = request.query_params.get("visibility")
        user_id = request.query_params.get("user_id")

        service = AnalysisService()
        return service.get_analysis(
            authenticated_user_id=authenticated_user_id,
            authenticated_user_email=authenticated_user_email,
            authenticated_user_name=authenticated_user_name,
            page=page,
            limit=limit,
            name=name,
            from_date=from_date,
            to_date=to_date,
            user_id=user_id,
            visibility=visibility,
        )

    @swagger_auto_schema(
        operation_id="create_or_update_analysis",
        operation_summary="Create a new analysis report or update existing one",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "asset_type", "type"],
            properties={
                "id": openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Analysis ID (if provided, will update existing analysis)"
                ),
                "user_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User ID"
                ),
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Name of the analysis"
                ),
                "asset_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Type of asset"
                ),
                "type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Analysis type"
                ),
                "visibility": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Visibility setting (default private)",
                    enum=["private", "public"],
                ),
            },
        ),
        responses={
            201: "Analysis created successfully",
            200: "Analysis updated successfully"
        },
    )
    def post(self, request):
        # Extract authenticated user from JWT middleware
        authenticated_user_id = None
        authenticated_user_email = None
        self.logger.debug(
            "Analysis POST auth context: has_jwt_user=%s has_jwt_payload=%s headers_auth=%s",
            hasattr(request, 'jwt_user') and bool(getattr(request, 'jwt_user', None)),
            hasattr(request, 'jwt_payload') and bool(getattr(request, 'jwt_payload', None)),
            bool(request.headers.get('Authorization')),
        )
        if hasattr(request, 'jwt_user') and request.jwt_user:
            authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
            authenticated_user_email = request.jwt_user.get('email')
        elif hasattr(request, 'jwt_payload') and request.jwt_payload:
            authenticated_user_id = request.jwt_payload.get('user_id') or request.jwt_payload.get('email')
            authenticated_user_email = request.jwt_payload.get('email')

        if not authenticated_user_id:
            self.logger.warning("Analysis POST unauthorized: missing authenticated_user_id")
            return ResponseBuilder.error(message="Authentication required", status_code=401)

        body = request.data
        analysis_id = body.get("id")

        # Create fresh service instance for thread safety
        service = AnalysisService()

        # Prepare analysis data dictionary - use authenticated user as owner
        analysis_data = {
            "user_id": authenticated_user_id,  # Use authenticated user, not from request body
            "name": body.get("name"),
            "asset_type": body.get("asset_type"),
            "type_value": body.get("type"),
            "visibility": body.get("visibility", "private"),
        }
        
        if analysis_id:
            # Add analysis_id for update operation
            analysis_data["analysis_id"] = analysis_id
            result = service.update_analysis(analysis_data)
            
            # Convert dictionary response to DRF Response object
            if result.get("success"):
                return ResponseBuilder.success(
                    data=result.get("data"),
                    message=result.get("message")
                )
            else:
                return ResponseBuilder.error(
                    message=result.get("message")
                )
        else:
            # Create new analysis
            result = service.create_analysis(analysis_data)
            
            # Convert dictionary response to DRF Response object
            if result.get("success"):
                return ResponseBuilder.created(
                    data=result.get("data"),
                    message=result.get("message")
                )
            else:
                return ResponseBuilder.error(
                    message=result.get("message")
                )

