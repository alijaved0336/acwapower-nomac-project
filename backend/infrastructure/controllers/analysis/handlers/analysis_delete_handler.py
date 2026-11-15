"""
Analysis Delete Handler
Handles analysis deletion operations.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.analysis.analysis_base_service import AnalysisService


class AnalysisDeleteView(APIView):
    """Handles analysis deletion operations"""

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="delete_analysis",
        operation_summary="Delete a specific analysis by ID (with cascade deletion of widgets)",
        operation_description="""
        Delete an analysis and all its associated widgets.

        **Authorization Rules:**
        - **Analysis Owner**: Can delete their own analysis (public or private)
        - **Super Admin**: Users with role.type = "super_admin" can delete ANY analysis
        - **Regular Users**: Cannot delete analyses they don't own

        **Cascade Deletion:**
        - All widgets associated with the analysis are automatically deleted
        - Deletion order: Analysis FIRST, then widgets (minimizes data integrity risk)
        - Note: Databricks doesn't support transactions, so this is best-effort cascade

        **Audit Trail:**
        - All super admin deletions are logged for audit purposes
        - Logs include: admin user ID/email, analysis ID, owner ID, analysis name
        """,
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Analysis ID to delete",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Analysis deleted successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Analysis and associated widgets deleted successfully",
                        "data": None,
                    }
                },
            ),
            401: openapi.Response(
                description="Authentication required - JWT token missing or invalid"
            ),
            403: openapi.Response(
                description="Permission denied - You must be the analysis owner or a super admin to delete this analysis",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "You do not have permission to delete this analysis",
                    }
                },
            ),
            404: openapi.Response(
                description="Analysis not found or access denied",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Analysis not found or access denied",
                    }
                },
            ),
        },
        tags=["analysis"],
    )
    def delete(self, request, id):
        """Delete an analysis by ID"""
        # Extract authenticated user from JWT middleware
        user_id = None
        user_email = None

        if hasattr(request, 'jwt_user') and request.jwt_user:
            user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
            user_email = request.jwt_user.get('email')
        elif hasattr(request, 'jwt_payload') and request.jwt_payload:
            user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
            user_email = request.jwt_payload.get('email')

        if not user_id:
            return ResponseBuilder.error(message="Authentication required", status_code=401)

        service = AnalysisService()
        result = service.delete_analysis(
            analysis_id=id, authenticated_user_id=user_id, authenticated_user_email=user_email
        )

        if result["success"]:
            return ResponseBuilder.success(message=result["message"], data=result.get("data"))
        else:
            status_code = result.get("status_code", 500)
            return ResponseBuilder.error(message=result["message"], status_code=status_code)
