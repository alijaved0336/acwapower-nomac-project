import jwt
import logging
from django.conf import settings
from django.http import JsonResponse

from infrastructure.applevel.jwtService import JwtService
from infrastructure.orm.repositories.user import UserRepo


class JWTAuthMiddleware:
    """
    JWT Authentication Middleware -
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.user_repo = UserRepo()
        self.jwtService = JwtService()
        self.logger = logging.getLogger(__name__)
        self.logger.info("JWT Authentication Middleware Initialized!")

    def __call__(self, request):
        # paths that should NOT require authentication
        public_paths = [
            "/auth/", 
            "/docs/", 
            "/admin/", 
            "/docs.json",
            "/api/v1/adls-listener/",  # Event Grid webhook - no JWT needed
            "/health/",  # Health check endpoints
            "/liveness/",
            "/readiness/"
        ]

        # Specific validation paths that need to bypass JWT for 400 error responses
        validation_bypass_patterns = [
            # Pattern to catch invalid UUIDs in user role assignment
            "/api/users/",
        ]

        # skip auth for root path
        if request.path == "/":
            return self.get_response(request)

        # skip auth for public paths
        is_public = any(request.path.startswith(path) for path in public_paths)
        if is_public:
            return self.get_response(request)

        # For API endpoints, check if this might be a validation error case
        if any((request.path.startswith("/api/"), request.path.startswith("/analysis/"), request.path.startswith("/clickhouse/"), request.path.startswith("/widgets/"))):
            # Trace incoming request path and method for debugging
            self.logger.debug(
                "JWT check for path=%s method=%s", request.path, getattr(request, "method", "?")
            )
            # If this is a user role path, let Django resolve it first to check for validation errors
            if "/users/" in request.path and "/role/" in request.path:
                # Process the request first to see if it's a validation error (400)
                response = self.get_response(request)

                # If it's a 400 (validation error), return it directly
                if response.status_code == 400:
                    return response

                # If it's anything else and we need JWT, check JWT
                if response.status_code != 404 and not self._is_valid_jwt(request):
                    self.logger.warning(
                        "JWT invalid for user-role path. status=%s", response.status_code
                    )
                    return JsonResponse({"error": "Unauthorized User"}, status=401)

                return response

            # For other API endpoints, check JWT normally
            if not self._is_valid_jwt(request):
                try:
                    # Dump a sanitized view of incoming headers for debugging
                    incoming_headers = {
                        k: ("<redacted>" if k.lower() == "authorization" else v)
                        for k, v in request.headers.items()
                    }
                    self.logger.warning(
                        "Auth failed. Incoming headers (sanitized) for path=%s: %s",
                        request.path,
                        incoming_headers,
                    )
                except Exception:
                    pass
                self.logger.warning("JWT invalid for path=%s", request.path)
                return JsonResponse({"error": "Unauthorized User"}, status=401)

        # Process the request through Django's URL resolution
        response = self.get_response(request)

        return response

    def _is_valid_jwt(self, request):
        """Validate JWT token from Authorization header"""
        try:
            auth_header = request.headers.get("Authorization", "")

            if not auth_header.startswith("Bearer "):
                # Promote to WARNING so it shows up without DEBUG logging
                self.logger.warning(
                    "Authorization header missing or not Bearer for path=%s. header_present=%s",
                    request.path,
                    bool(auth_header),
                )
                return False

            token = auth_header.split(" ")[1]

            payload = self.jwtService.decode_and_verify(
                token,
            )
            self.logger.debug(
                "JWT decoded successfully for email=%s path=%s",
                payload.get("email"),
                request.path,
            )

            # Check if user exists in our database
            user = self.user_repo.find_by_email(payload.get("email"))

            if not user:
                self.logger.warning(
                    "JWT valid but user not found in DB. email=%s path=%s",
                    payload.get("email"),
                    request.path,
                )
                return False

            request.jwt_user = user
            request.jwt_payload = payload
            return True
            
        except (jwt.DecodeError, jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            # Invalid JWT tokens should return False to trigger 401 Unauthorized
            self.logger.warning(
                "JWT decode/verify failed: %s path=%s", e.__class__.__name__, request.path
            )
            return False
        except Exception as e:
            # Catch any other unexpected errors to prevent 500 errors
            self.logger.error(
                "Unexpected error during JWT validation: %s path=%s", e, request.path, exc_info=True
            )
            return False
