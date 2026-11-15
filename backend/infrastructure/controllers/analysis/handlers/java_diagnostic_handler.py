"""
Java Diagnostic Handler - Diagnostic endpoint for checking Java environment status
"""
import logging
import os
import subprocess
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

logger = logging.getLogger(__name__)


class JavaDiagnosticView(APIView):
    """
    Diagnostic endpoint to check Java environment and bundled Java status
    GET /debug/java/
    """
    permission_classes = [AllowAny]
    # Hide from Swagger documentation - internal diagnostic tool
    swagger_schema = None

    @swagger_auto_schema(
        operation_id="get_java_diagnostics",
        operation_summary="Get Java environment diagnostics",
        operation_description="Diagnostic endpoint to check Java environment and bundled Java status",
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def get(self, request):
        """Get Java environment diagnostic information"""
        diagnostic_info = {
            "current_working_directory": os.getcwd(),
            "environment_variables": {
                "JAVA_HOME": os.getenv("JAVA_HOME"),
                "PATH": os.getenv("PATH"),
            },
            "file_system_checks": {},
            "java_search_paths": [],
        }
        
        # Check common Java locations
        java_locations = [
            "/home/site/wwwroot/.java",
            "/home/site/wwwroot",
            "/tmp/.java",
            "/usr/lib/jvm/java-17-openjdk-amd64",
            "/usr/lib/jvm/default-java",
            "/opt/java/openjdk",
        ]
        
        # Check if bundled Java exists
        bundled_java_path = "/home/site/wwwroot/.java"
        diagnostic_info["bundled_java_exists"] = os.path.exists(bundled_java_path)
        diagnostic_info["bundled_java_executable"] = os.path.exists(os.path.join(bundled_java_path, "bin", "java"))
        
        # Check file system permissions
        for location in java_locations:
            if os.path.exists(location):
                try:
                    # Check if we can read the directory
                    os.listdir(location)
                    diagnostic_info["file_system_checks"][location] = "accessible"
                except PermissionError:
                    diagnostic_info["file_system_checks"][location] = "permission_denied"
                except Exception as e:
                    diagnostic_info["file_system_checks"][location] = f"error: {str(e)}"
            else:
                diagnostic_info["file_system_checks"][location] = "not_found"
        
        diagnostic_info["java_search_paths"] = java_locations
        
        # Try to run java -version if available
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
            diagnostic_info["java_version_output"] = result.stderr  # Java version info goes to stderr
            diagnostic_info["java_available"] = True
        except FileNotFoundError:
            diagnostic_info["java_version_output"] = "Java not found in PATH"
            diagnostic_info["java_available"] = False
        except Exception as e:
            diagnostic_info["java_version_error"] = str(e)
            diagnostic_info["java_available"] = False
        
        return Response({
            "success": True,
            "message": "Java diagnostic information retrieved",
            "data": diagnostic_info
        })