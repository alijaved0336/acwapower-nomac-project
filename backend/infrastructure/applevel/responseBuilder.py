from rest_framework import status
from rest_framework.response import Response

from constants import HttpStatusCodes, ResponseFields, ResponseMessages


class ResponseBuilder:
    """
    A wrapper class to build standardized API responses.
    Format:
    {
        "success": bool,
        "message": str,
        "data": dict | list | None
    }
    """

    @staticmethod
    def success(
        data=None,
        message=ResponseMessages.REQUEST_SUCCESSFUL,
        status_code=HttpStatusCodes.OK,
    ):
        """
        Build a successful response.

        Args:
            data: Response data (dict, list, or None)
            message: Success message
            status_code: HTTP status code (default: 200)
        """
        return Response(
            {
                ResponseFields.SUCCESS: True,
                ResponseFields.MESSAGE: message,
                ResponseFields.DATA: data or {},
            },
            status=status_code,
        )

    @staticmethod
    def error(
        message=ResponseMessages.SOMETHING_WENT_WRONG,
        data=None,
        status_code=HttpStatusCodes.BAD_REQUEST,
    ):
        """
        Build an error response.

        Args:
            message: Error message
            data: Additional error data (optional)
            status_code: HTTP status code (default: 400)
        """
        return Response(
            {
                ResponseFields.SUCCESS: False,
                ResponseFields.MESSAGE: message,
                ResponseFields.DATA: data or {},
            },
            status=status_code,
        )

    @staticmethod
    def created(data=None, message=ResponseMessages.RESOURCE_CREATED_SUCCESSFULLY):
        """
        Build a resource created response (HTTP 201).

        Args:
            data: Created resource data
            message: Success message
        """
        return ResponseBuilder.success(
            data=data, message=message, status_code=HttpStatusCodes.CREATED
        )

    @staticmethod
    def not_found(message=ResponseMessages.RESOURCE_NOT_FOUND, data=None):
        """
        Build a not found response (HTTP 404).

        Args:
            message: Not found message
            data: Additional data (optional)
        """
        return ResponseBuilder.error(
            message=message, data=data, status_code=HttpStatusCodes.NOT_FOUND
        )

    @staticmethod
    def server_error(message=ResponseMessages.INTERNAL_SERVER_ERROR, data=None):
        """
        Build a server error response (HTTP 500).

        Args:
            message: Error message
            data: Additional error data (optional)
        """
        return ResponseBuilder.error(
            message=message,
            data=data,
            status_code=HttpStatusCodes.INTERNAL_SERVER_ERROR,
        )
