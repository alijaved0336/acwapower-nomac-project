# services.py
import logging
import re
from typing import Any, Dict

from rest_framework import status
from rest_framework.response import Response

from constants import AuthConfig, HttpStatusCodes, ResponseMessages
from infrastructure.applevel.jwtService import JwtService
from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.orm.repositories.user import UserRepo
from interface.serializers.users import UserSerializer
from jwt import ExpiredSignatureError, InvalidTokenError
from infrastructure.orm.repositories.roles import RoleRepository

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.user_repo = UserRepo()
        self.jwt_service = JwtService()
        self.role_repo = RoleRepository()

    def verify_user(self, payload: Dict[str, Any]) -> Response:
        serializer = UserSerializer(data=payload)
        if not serializer.is_valid():
            # show actual serializer errors
            return ResponseBuilder.error(
                message=f"{ResponseMessages.INVALID_DATA}: {serializer.errors}",
                data={},
                status_code=HttpStatusCodes.BAD_REQUEST,
            )

        # Normalize (keep validation with serializer)
        validated = serializer.validated_data
        email = validated["email"].strip().lower()
        name = validated.get("name") or ""
        picture = validated.get("picture")
        sub = validated.get("sub")

        # Look up user (case-insensitive match ideally at DB level)
        user = self.user_repo.find_by_email_with_role(email)

        default_role = self.role_repo.get_by_name("User")
        default_role_id = default_role["id"]

        if not user:
            # Assign default role; consider moving this to a config table
            user = self.user_repo.create_user(
                name=name,
                email=email,
                picture=picture,
                sub=sub,
                role_id=default_role_id,
                is_active=True,
            )

        return self.return_user_with_token(user)

    def verify_refresh_token(self, refresh_token):
        try:
            token = self.jwt_service.decode_and_verify(refresh_token, expected_type="refresh")
        except ExpiredSignatureError:
            return ResponseBuilder.error(
                message="Refresh token expired",
                data={},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except InvalidTokenError as e:
            # Log detailed error server-side for debugging
            logger.warning(
                f"Invalid refresh token attempt: {str(e)}",
                extra={
                    "error_type": type(e).__name__,
                    "token_prefix": refresh_token[:10] if refresh_token else None
                }
            )
            # Return generic error to client (don't expose JWT details)
            return ResponseBuilder.error(
                message="Invalid or malformed refresh token",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        user = self.user_repo.find_by_email_with_role(token["email"])
        if not user:
            return ResponseBuilder.error(
                message="User not found",
                data={},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return self.return_user_with_token(user)

    def return_user_with_token(self, user):
        access_token = self.jwt_service.generate_access_token(user)
        refresh_token = self.jwt_service.generate_refresh_token(user)

        # Return explicit keys, not a set
        return ResponseBuilder.success(
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user,  # already includes role via your repo function
            },
            message=ResponseMessages.USER_SUCCESSFULLY_VERIFIED,
            status_code=HttpStatusCodes.OK,
        )
