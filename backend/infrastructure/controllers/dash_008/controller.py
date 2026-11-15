"""
Dashboard 008 Controller - Pump Analysis API
Provides endpoints for Pump List, Operational Trend and Performance Trend data.
"""

import re
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import logging

from infrastructure.services.dash_008 import Dash008Service
from infrastructure.services.dash_007 import Dash007Service
from infrastructure.applevel.responseBuilder import ResponseBuilder

logger = logging.getLogger(__name__)


class PumpListView(APIView):
    """
    API View for retrieving pumps grouped by category for a specific site.
    Uses ClickHouse ADLS service with dynamic table discovery.
    """

    @swagger_auto_schema(
        operation_id="dash_008_get_pumps",
        operation_summary="Get pumps grouped by category",
        operation_description=(
            "Retrieve all pumps for a specific site grouped by pump category. "
            "The endpoint automatically discovers the correct pump reference table "
            "using dynamic table discovery (Pattern 1: {site_id}_Pumps_Reference or "
            "Pattern 2: {site_id}_Stream_All_Pumps_Reference). "
            "Returns pumps grouped by categories including High Pressure Pumps, "
            "ERD Booster Pumps, Feed Pump Second Pass, etc. Empty categories are included in the response."
        ),
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier (e.g., 'Rabigh3', 'UAQ', 'STPC', 'Jubail-Jazlah')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success - Pumps retrieved successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Pump list retrieved successfully"
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Pumps grouped by category",
                            example={
                                "High_Pressure_Pump_HPP": [
                                    {"pump": "Pump_01", "Pump_id": "55550"},
                                    {"pump": "Pump_02", "Pump_id": "56661"}
                                ],
                                "ERD_Booster_Pump": [
                                    {"pump": "Pump_01", "Pump_id": "33330"}
                                ],
                                "Feed_Pump_Second_Pass": []
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                "Bad Request - Invalid site_id",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Site ID cannot be empty or whitespace"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: openapi.Response(
                "Not Found - Site or pump reference table not found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Site 'InvalidSite' not found"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Internal server error occurred"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        tags=["Dash-008"],
    )
    def get(self, request, site_id: str) -> Response:
        """
        GET /api/dash-008/get-pumps/{site_id}/
        Returns pumps grouped by category for the specified site.

        Args:
            request: HTTP request object
            site_id: Site identifier from URL path

        Returns:
            Response with pumps grouped by category
        """
        try:
            # Validate site_id is not empty or whitespace
            if not site_id or not site_id.strip():
                logger.warning("Empty or whitespace site_id provided")
                return ResponseBuilder.error(
                    message="Site ID cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Processing pump list request for site: {site_id}")

            # Get pumps grouped by category from Dash007Service
            # (Reusing existing functionality instead of duplicating code)
            service = Dash007Service()
            pumps_data = service.get_pumps_by_category(site_id.strip())

            logger.info(f"Successfully retrieved pumps for site {site_id}")

            return ResponseBuilder.success(
                data=pumps_data,
                message="Pump list retrieved successfully"
            )

        except ValueError as ve:
            # Handle validation errors (site not found, table not found)
            error_message = str(ve)
            logger.error(f"Validation error for site {site_id}: {error_message}")

            # Determine if it's a 404 error based on the error message
            if "not found" in error_message.lower():
                return ResponseBuilder.not_found(
                    message=error_message,
                    data={}
                )
            else:
                return ResponseBuilder.error(
                    message=error_message,
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Error in PumpListView for site {site_id}: {str(e)}", exc_info=True)
            return ResponseBuilder.server_error(
                message="Failed to retrieve pump list",
                data={"error": str(e)}
            )


class OperationalTrendView(APIView):
    """
    API View for retrieving operational trend data for pump analysis.
    Returns time-series data for operational metrics.
    """

    @swagger_auto_schema(
        operation_id="dash_008_operational_trend",
        operation_summary="Get operational trend data",
        operation_description=(
            "Retrieve time-series operational trend data for a specific pump within a date range. "
            "Returns metrics including flow_measured, pump_power_expected, pump_power_measured, "
            "efficiency, and temperature over time for line chart visualization. "
            "Pump ID is required to get data for a specific pump."
        ),
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier (e.g., 'UAQ', 'Rabigh3', 'STPC', 'Jubail-Jazlah')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "pump_type",
                openapi.IN_PATH,
                description="Pump type/category (e.g., 'High_Pressure_Pump_HPP', 'ERD_Booster_Pump')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "pump_id",
                openapi.IN_QUERY,
                description="Pump ID (e.g., '55550') - REQUIRED",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Start date in YYYY-MM-DD format (e.g., '2025-10-10')",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format (e.g., '2025-10-17')",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success - Operational trend data retrieved successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Operational trend data retrieved successfully"
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "column_data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "timestamp": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="2025-10-10T00:00:00Z"
                                            ),
                                            "flow_measured": openapi.Schema(
                                                type=openapi.TYPE_NUMBER,
                                                example=150.5
                                            ),
                                            "pump_power_expected": openapi.Schema(
                                                type=openapi.TYPE_NUMBER,
                                                example=250.3
                                            ),
                                            "pump_power_measured": openapi.Schema(
                                                type=openapi.TYPE_NUMBER,
                                                example=248.7
                                            ),
                                            "efficiency_measured": openapi.Schema(
                                                type=openapi.TYPE_NUMBER,
                                                example=92.5
                                            )
                                        }
                                    )
                                ),
                                "dropdown_data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    example=["Efficiency", "Flow", "Head", "Pump_Power", "SEC"]
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response("Bad Request - Invalid parameters or missing pump_id"),
            404: openapi.Response("Not Found - Site or pump type not found"),
            500: openapi.Response("Internal Server Error")
        },
        tags=["Dash-008"],
    )
    def get(self, request, site_id: str, pump_type: str) -> Response:
        """
        GET /api/dash-008/operational-trend/{site_id}/{pump_type}/
        Returns operational trend data for the specified pump.

        Args:
            request: HTTP request object
            site_id: Site identifier from URL path
            pump_type: Pump type/category from URL path

        Query Parameters:
            pump_id: Pump ID (REQUIRED)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Response with time-series operational data
        """
        try:
            # Validate path parameters
            if not site_id or not site_id.strip():
                logger.warning("Empty or whitespace site_id provided")
                return ResponseBuilder.error(
                    message="Site ID cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if not pump_type or not pump_type.strip():
                logger.warning("Empty or whitespace pump_type provided")
                return ResponseBuilder.error(
                    message="Pump type cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Get query parameters
            pump_id = request.query_params.get('pump_id')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

            # Validate pump_id is required and not empty
            if not pump_id or not pump_id.strip():
                logger.warning("pump_id is required but not provided or empty")
                return ResponseBuilder.error(
                    message="Pump ID is required and cannot be empty",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate date format
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            if from_date and not re.match(date_pattern, from_date):
                logger.warning(f"Invalid from_date format: {from_date}")
                return ResponseBuilder.error(
                    message="Invalid from_date format. Expected YYYY-MM-DD",
                    data={"from_date": from_date},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if to_date and not re.match(date_pattern, to_date):
                logger.warning(f"Invalid to_date format: {to_date}")
                return ResponseBuilder.error(
                    message="Invalid to_date format. Expected YYYY-MM-DD",
                    data={"to_date": to_date},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate date range
            if from_date and to_date:
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')

                    if from_date_obj > to_date_obj:
                        logger.warning(f"Invalid date range: from_date {from_date} is after to_date {to_date}")
                        return ResponseBuilder.error(
                            message="Invalid date range: from_date cannot be after to_date",
                            data={"from_date": from_date, "to_date": to_date},
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                except ValueError as ve:
                    logger.warning(f"Invalid date values: {str(ve)}")
                    return ResponseBuilder.error(
                        message=f"Invalid date values: {str(ve)}",
                        data={"from_date": from_date, "to_date": to_date},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            logger.info(
                f"Processing operational trend request - Site: {site_id}, "
                f"Pump Type: {pump_type}, Pump ID: {pump_id}, Date Range: {from_date} to {to_date}"
            )

            # Get operational trend data from service
            service = Dash008Service()
            operational_result = service.get_operational_trend_data(
                site_id=site_id.strip(),
                pump_type=pump_type.strip(),
                pump_id=pump_id.strip(),
                from_date=from_date,
                to_date=to_date
            )

            logger.info(
                f"Successfully retrieved operational trend data for {site_id}/{pump_type}/{pump_id}"
            )

            return ResponseBuilder.success(
                data=operational_result,
                message="Operational trend data retrieved successfully"
            )

        except ValueError as ve:
            error_message = str(ve)
            logger.error(
                f"Validation error for operational trend {site_id}/{pump_type}: {error_message}"
            )

            if "not found" in error_message.lower():
                return ResponseBuilder.not_found(
                    message=error_message,
                    data={}
                )
            else:
                return ResponseBuilder.error(
                    message=error_message,
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(
                f"Error in OperationalTrendView for {site_id}/{pump_type}: {str(e)}",
                exc_info=True
            )
            return ResponseBuilder.server_error(
                message="Failed to retrieve operational trend data",
                data={"error": str(e)}
            )


class PerformanceTrendView(APIView):
    """
    API View for retrieving performance trend data for pump analysis.
    Returns scatter plot data for performance metrics comparison.
    """

    @swagger_auto_schema(
        operation_id="dash_008_performance_trend",
        operation_summary="Get performance trend data",
        operation_description=(
            "Retrieve performance trend data for scatter plot analysis. "
            "Returns individual data points with metrics for comparing flow, power, efficiency, etc. "
            "Requires a specific pump ID - 'all' is not supported. "
            "Data includes VSD performance data grouped by speed ratios for filtering and visualization."
        ),
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier (e.g., 'UAQ', 'Rabigh3')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "pump_type",
                openapi.IN_PATH,
                description="Pump type/category (e.g., 'High_Pressure_Pump_HPP')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "pump_id",
                openapi.IN_QUERY,
                description="Pump ID (e.g., '55550') - REQUIRED",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Start date in YYYY-MM-DD format",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success - Performance trend data retrieved successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Performance trend data retrieved successfully"
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "column_data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "pump_id": openapi.Schema(type=openapi.TYPE_STRING, example="55550"),
                                            "pump_name": openapi.Schema(type=openapi.TYPE_STRING, example="Pump_01"),
                                            "timestamp": openapi.Schema(type=openapi.TYPE_STRING, example="2025-10-10T00:00:00Z"),
                                            "flow_measured": openapi.Schema(type=openapi.TYPE_NUMBER, example=150.5),
                                            "pump_power_expected": openapi.Schema(type=openapi.TYPE_NUMBER, example=250.3),
                                            "pump_power_measured": openapi.Schema(type=openapi.TYPE_NUMBER, example=248.7),
                                            "efficiency_measured": openapi.Schema(type=openapi.TYPE_NUMBER, example=92.5),
                                            "speed": openapi.Schema(type=openapi.TYPE_NUMBER, example=1450)
                                        }
                                    )
                                ),
                                "dropdown_data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    example=["Efficiency", "Flow", "Head", "Pump_Power", "SEC"]
                                ),
                                "vsd_performance_data": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    nullable=True,
                                    properties={
                                        "min_speed_ratio": openapi.Schema(type=openapi.TYPE_NUMBER, example=0.75),
                                        "max_speed_ratio": openapi.Schema(type=openapi.TYPE_NUMBER, example=1.19),
                                        "speed_groups": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            example={
                                                "80%": {
                                                    "Efficiency_Expected": [0.34, 0.48, 0.65],
                                                    "Flow_Expected": [0, 14.69, 29.39]
                                                },
                                                "90%": {}
                                            }
                                        )
                                    }
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response("Bad Request - Invalid parameters or missing pump_id"),
            404: openapi.Response("Not Found - Site or pump type not found"),
            500: openapi.Response("Internal Server Error")
        },
        tags=["Dash-008"],
    )
    def get(self, request, site_id: str, pump_type: str) -> Response:
        """
        GET /api/dash-008/performance-trend/{site_id}/{pump_type}/
        Returns performance trend data for scatter plot analysis.

        Args:
            request: HTTP request object
            site_id: Site identifier from URL path
            pump_type: Pump type/category from URL path

        Query Parameters:
            pump_id: Pump ID (REQUIRED)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Response with performance data points
        """
        try:
            # Validate path parameters
            if not site_id or not site_id.strip():
                logger.warning("Empty or whitespace site_id provided")
                return ResponseBuilder.error(
                    message="Site ID cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if not pump_type or not pump_type.strip():
                logger.warning("Empty or whitespace pump_type provided")
                return ResponseBuilder.error(
                    message="Pump type cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Get query parameters
            pump_id = request.query_params.get('pump_id')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

            # Validate pump_id is required and not empty
            if not pump_id or not pump_id.strip():
                logger.warning("pump_id is required but not provided or empty")
                return ResponseBuilder.error(
                    message="Pump ID is required and cannot be empty",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate date format
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            if from_date and not re.match(date_pattern, from_date):
                logger.warning(f"Invalid from_date format: {from_date}")
                return ResponseBuilder.error(
                    message="Invalid from_date format. Expected YYYY-MM-DD",
                    data={"from_date": from_date},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if to_date and not re.match(date_pattern, to_date):
                logger.warning(f"Invalid to_date format: {to_date}")
                return ResponseBuilder.error(
                    message="Invalid to_date format. Expected YYYY-MM-DD",
                    data={"to_date": to_date},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate date range
            if from_date and to_date:
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')

                    if from_date_obj > to_date_obj:
                        logger.warning(f"Invalid date range: from_date {from_date} is after to_date {to_date}")
                        return ResponseBuilder.error(
                            message="Invalid date range: from_date cannot be after to_date",
                            data={"from_date": from_date, "to_date": to_date},
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                except ValueError as ve:
                    logger.warning(f"Invalid date values: {str(ve)}")
                    return ResponseBuilder.error(
                        message=f"Invalid date values: {str(ve)}",
                        data={"from_date": from_date, "to_date": to_date},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            logger.info(
                f"Processing performance trend request - Site: {site_id}, "
                f"Pump Type: {pump_type}, Pump ID: {pump_id}, Date Range: {from_date} to {to_date}"
            )

            # Get performance trend data from service
            service = Dash008Service()
            performance_result = service.get_performance_trend_data(
                site_id=site_id.strip(),
                pump_type=pump_type.strip(),
                pump_id=pump_id.strip(),
                from_date=from_date,
                to_date=to_date
            )

            logger.info(
                f"Successfully retrieved performance trend data for {site_id}/{pump_type}/{pump_id}"
            )

            return ResponseBuilder.success(
                data=performance_result,
                message="Performance trend data retrieved successfully"
            )

        except ValueError as ve:
            error_message = str(ve)
            logger.error(
                f"Validation error for performance trend {site_id}/{pump_type}: {error_message}"
            )

            if "not found" in error_message.lower():
                return ResponseBuilder.not_found(
                    message=error_message,
                    data={}
                )
            else:
                return ResponseBuilder.error(
                    message=error_message,
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(
                f"Error in PerformanceTrendView for {site_id}/{pump_type}: {str(e)}",
                exc_info=True
            )
            return ResponseBuilder.server_error(
                message="Failed to retrieve performance trend data",
                data={"error": str(e)}
            )