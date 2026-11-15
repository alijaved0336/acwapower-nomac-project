"""
Health check controller for Docker health checks and monitoring
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
from django.db import connection
import os
import sys


class HealthCheckController(APIView):
    """
    Health check endpoint for monitoring application status
    """
    permission_classes = [AllowAny]  # No authentication required for health checks

    @swagger_auto_schema(
        operation_id="health_check",
        operation_summary="Application health check",
        operation_description="Returns the health status of the application and its dependencies",
        responses={
            200: openapi.Response(
                description="Application is healthy",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Health status'),
                        'services': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'django': openapi.Schema(type=openapi.TYPE_STRING),
                                'cache': openapi.Schema(type=openapi.TYPE_STRING),
                                'delta_lake': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'version': openapi.Schema(type=openapi.TYPE_STRING, description='Application version'),
                        'python_version': openapi.Schema(type=openapi.TYPE_STRING, description='Python version'),
                    }
                )
            ),
            503: openapi.Response(description="Service unavailable")
        },
        tags=["Health"]
    )
    def get(self, request):
        """
        Check application health status
        """
        health_status = {
            'status': 'healthy',
            'services': {
                'django': 'ok',
                'cache': 'unknown',
                'delta_lake': 'unknown',
            },
            'version': '1.0.0',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }

        # Check Redis cache
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health_status['services']['cache'] = 'ok'
            else:
                health_status['services']['cache'] = 'error'
        except Exception as e:
            health_status['services']['cache'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'

        # Check Delta Lake path
        try:
            delta_lake_path = os.environ.get('DELTALAKE_USERS_TABLE_PATH', '/app/data/users')
            if os.path.exists(os.path.dirname(delta_lake_path)):
                health_status['services']['delta_lake'] = 'ok'
            else:
                health_status['services']['delta_lake'] = 'path not found'
        except Exception as e:
            health_status['services']['delta_lake'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'

        # Return appropriate status code
        if health_status['status'] == 'healthy':
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class LivenessController(APIView):
    """
    Simple liveness probe for Kubernetes/Docker
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="liveness_probe",
        operation_summary="Liveness probe",
        operation_description="Simple endpoint to check if the application is alive",
        responses={
            200: openapi.Response(
                description="Application is alive",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, default='alive')
                    }
                )
            )
        },
        tags=["Health"]
    )
    def get(self, request):
        """
        Simple liveness check
        """
        return Response({'status': 'alive'}, status=status.HTTP_200_OK)


class ReadinessController(APIView):
    """
    Readiness probe to check if the application is ready to serve requests
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="readiness_probe",
        operation_summary="Readiness probe",
        operation_description="Check if the application is ready to serve requests",
        responses={
            200: openapi.Response(
                description="Application is ready",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, default='ready'),
                        'checks_passed': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            503: openapi.Response(description="Service not ready")
        },
        tags=["Health"]
    )
    def get(self, request):
        """
        Check if application is ready to serve requests
        """
        checks_passed = True

        # Check if we can access cache
        try:
            cache.set('readiness_check', 'ok', 5)
            cache.get('readiness_check')
        except:
            checks_passed = False

        if checks_passed:
            return Response({'status': 'ready', 'checks_passed': True}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'not_ready', 'checks_passed': False}, status=status.HTTP_503_SERVICE_UNAVAILABLE)