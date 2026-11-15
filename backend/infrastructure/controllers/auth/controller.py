# controller.py
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from interface.serializers.users import UserSerializer

# Set up logging
logger = logging.getLogger(__name__)


from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.auth import AuthService
from interface.serializers.auth import RefreshTokenSerializer


class AuthVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def __init__(self):
        self.authService = AuthService()
    
    def post(self, request):
        return self.authService.verify_user(request.data)


class AuthRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def __init__(self):
        self.authService = AuthService()

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseBuilder.error(
                message=f"Invalid data: {serializer.errors}",
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Use validated_data to access the parsed refresh token
        refresh_token = serializer.validated_data["refresh_token"]
        return self.authService.verify_refresh_token(refresh_token)
