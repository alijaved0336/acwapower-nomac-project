"""
Dashboard 007 Controller - Pump List API and Pump Data API
Provides endpoints for retrieving pumps grouped by category and pump time-series data.
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

from infrastructure.services.dash_007 import Dash007Service
from infrastructure.applevel.responseBuilder import ResponseBuilder

logger = logging.getLogger(__name__)


class PumpListView(APIView):
    """
    API View for retrieving pumps grouped by category for a specific site.
    Uses ClickHouse ADLS service with dynamic table discovery.
    """

    @swagger_auto_schema(
        operation_id="dash_007_get_pumps",
        operation_summary="Get pumps grouped by category",
        operation_description=(
            "Retrieve all pumps for a specific site grouped by pump category. "
            "The endpoint automatically discovers the correct pump reference table "
            "using dynamic table discovery (Pattern 1: {site_id}_Pumps_Reference or "
            "Pattern 2: {site_id}_Stream_All_Pumps_Reference). "
            "Returns pumps grouped by categories including Feed Pumps, High Pressure Pumps, "
            "Booster Pumps, etc. Empty categories are included in the response."
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
                                "Feed Pumps": [
                                    {"pump": "Feed Pump 1A", "Pump_id": "FP-001"},
                                    {"pump": "Feed Pump 1B", "Pump_id": "FP-002"}
                                ],
                                "High Pressure Pumps": [
                                    {"pump": "HP Pump 2A", "Pump_id": "HPP-001"}
                                ],
                                "Booster Pumps": []
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
        tags=["Dash-007"],
    )
    def get(self, request, site_id: str) -> Response:
        """
        GET /api/dash-007/get-pumps/{site_id}/
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

            # Get pumps grouped by category from service
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


class PumpDataView(APIView):
    """
    API View for retrieving pump data with date filtering.
    Returns time-series data for pump operational metrics.
    """

    @swagger_auto_schema(
        operation_id="dash_007_get_pump_data",
        operation_summary="Get pump data with date filtering",
        operation_description=(
            "Retrieve time-series column data for a specific pump within a date range. "
            "Returns real data columns (Pump_Power, Efficiency, Head, Pump_Current, Pump_Flow, "
            "Pump_Discharge_Press, Pump_Feed_Press) from ClickHouse, plus expected/measured columns "
            "(SEC_Measured, SEC_Expected, Pump_Power_Measured, Pump_Power_Expected, etc.), "
            "and 1 calculated column: Pump_Differential_Pressure = Pump_Discharge_Press - Pump_Feed_Press. "
            "Additionally, returns VSD Performance Expected Trend data grouped by speed ratios (if available). "
            "The endpoint automatically discovers the correct pump operational performance table "
            "using dynamic table discovery (Pattern 1: {site_id}_Pumps_Operational_Performance_{Pump_Category} or "
            "Pattern 2: {site_id}_Stream_All_Pumps_Reference_{Pump_Category})."
        ),
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier (e.g., 'Jubail-Jazlah', 'Rabigh3', 'STPC', 'UAQ')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "Pump_Category",
                openapi.IN_PATH,
                description="Pump category (e.g., 'seawater_intake_system', 'feed_pump_second_pass')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "pump",
                openapi.IN_PATH,
                description="Pump name (e.g., 'Pump_01', 'Feed_Pump_1A')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "Pump_id",
                openapi.IN_PATH,
                description="Pump ID (e.g., '23331', 'FP-001')",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Start date in YYYY-MM-DD format (e.g., '2025-01-02')",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format (e.g., '2025-02-02')",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success - Pump data retrieved successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Pump data retrieved successfully"
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "column_data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Array of column data objects including operational data and all paired expected/measured columns",
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "columnName": openapi.Schema(type=openapi.TYPE_STRING, example="Pump_Power"),
                                            "columnType": openapi.Schema(type=openapi.TYPE_STRING, example="double"),
                                            "dataSource": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(type=openapi.TYPE_NUMBER),
                                                example=[245.5, 248.2, 243.9]
                                            ),
                                            "siteName": openapi.Schema(type=openapi.TYPE_STRING, example="Jubail-Jazlah"),
                                            "tableName": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="Jubail_Jazlah_Pumps_Operational_Performance_seawater_intake_system"
                                            )
                                        }
                                    )
                                ),
                                "dropdown_data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Array of base column names for paired expected/measured columns (dynamically discovered)",
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    example=["Efficiency", "Flow", "Head", "Pump_Power", "SEC"]
                                ),
                                "vsd_performance_data": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="VSD Performance Expected Trend data grouped by speed ratios (optional - null if unavailable)",
                                    nullable=True,
                                    properties={
                                        "min_speed_ratio": openapi.Schema(
                                            type=openapi.TYPE_NUMBER,
                                            description="Minimum speed ratio from operational data",
                                            example=0.75
                                        ),
                                        "max_speed_ratio": openapi.Schema(
                                            type=openapi.TYPE_NUMBER,
                                            description="Maximum speed ratio from operational data",
                                            example=1.15
                                        ),
                                        "speed_groups": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            description=(
                                                "Performance metrics grouped by speed ratio (1 decimal precision). "
                                                "Includes: Flow_Ratio, SEC_Expected, Pump_Power_Expected, "
                                                "Efficiency_Expected, Head_Expected, Flow_Expected. "
                                                "Excludes filter columns (Pump, Pump_ID, Pump_Category) and redundant Speed_Percent."
                                            ),
                                            example={
                                                "0.8": {
                                                    "Flow_Ratio": [0.75, 0.76],
                                                    "SEC_Expected": [3.2, 3.1],
                                                    "Pump_Power_Expected": [250.5, 252.0],
                                                    "Efficiency_Expected": [82.5, 83.0],
                                                    "Head_Expected": [10.5, 10.6],
                                                    "Flow_Expected": [1500, 1520]
                                                },
                                                "0.9": {
                                                    "Flow_Ratio": [0.85, 0.86],
                                                    "SEC_Expected": [3.0, 2.9],
                                                    "Pump_Power_Expected": [280.5, 282.0],
                                                    "Efficiency_Expected": [85.5, 86.0],
                                                    "Head_Expected": [12.2, 12.3],
                                                    "Flow_Expected": [1700, 1720]
                                                },
                                                "1.0": {
                                                    "Flow_Ratio": [0.95, 0.96],
                                                    "SEC_Expected": [2.8, 2.7],
                                                    "Pump_Power_Expected": [310.5, 312.0],
                                                    "Efficiency_Expected": [88.5, 89.0],
                                                    "Head_Expected": [14.0, 14.1],
                                                    "Flow_Expected": [1900, 1920]
                                                }
                                            }
                                        )
                                    }
                                ),
                                "data_availability_for_given_date": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description=(
                                        "Indicates if data exists for the requested date range. "
                                        "If false, auto-fallback logic was triggered to fetch the last 7 days of available data."
                                    ),
                                    example=True
                                ),
                                "from_date": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Actual start date used for data retrieval (YYYY-MM-DD). May differ from requested date if auto-fallback occurred.",
                                    example="2025-01-02"
                                ),
                                "to_date": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Actual end date used for data retrieval (YYYY-MM-DD). May differ from requested date if auto-fallback occurred.",
                                    example="2025-02-02"
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                "Bad Request - Invalid parameters or date format",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Invalid date format. Expected YYYY-MM-DD"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: openapi.Response(
                "Not Found - Site, table, or pump not found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="No pump operational performance table found for site 'Jubail-Jazlah' and category 'seawater_intake_system'"
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
                            example="Failed to retrieve pump data"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        tags=["Dash-007"],
    )
    def get(self, request, site_id: str, Pump_Category: str, pump: str, Pump_id: str) -> Response:
        """
        GET /api/dash-007/pump-data/{site_id}/{Pump_Category}/{pump}/{Pump_id}/
        Returns column data for the specified pump within the date range.

        Args:
            request: HTTP request object
            site_id: Site identifier from URL path
            Pump_Category: Pump category from URL path
            pump: Pump name from URL path
            Pump_id: Pump ID from URL path

        Query Parameters:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Response with array of column data objects
        """
        try:
            # Step 1: Validate path parameters
            if not site_id or not site_id.strip():
                logger.warning("Empty or whitespace site_id provided")
                return ResponseBuilder.error(
                    message="Site ID cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if not Pump_Category or not Pump_Category.strip():
                logger.warning("Empty or whitespace Pump_Category provided")
                return ResponseBuilder.error(
                    message="Pump Category cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if not pump or not pump.strip():
                logger.warning("Empty or whitespace pump provided")
                return ResponseBuilder.error(
                    message="Pump name cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if not Pump_id or not Pump_id.strip():
                logger.warning("Empty or whitespace Pump_id provided")
                return ResponseBuilder.error(
                    message="Pump ID cannot be empty or whitespace",
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Step 2: Validate query parameters
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

          
            # Step 3: Validate date format (YYYY-MM-DD)
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

            # Step 4: Validate date range
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
                f"Processing pump data request - Site: {site_id}, Category: {Pump_Category}, "
                f"Pump: {pump}, ID: {Pump_id}, Date Range: {from_date} to {to_date}"
            )

            # Step 5: Get pump data from service
            service = Dash007Service()
            pump_data_result = service.get_pump_data(
                site_id=site_id.strip(),
                pump_category=Pump_Category.strip(),
                pump=pump.strip(),
                pump_id=Pump_id.strip(),
                from_date=from_date,
                to_date=to_date
            )

            logger.info(
                f"Successfully retrieved pump data for {site_id}/{Pump_Category}/{pump}/{Pump_id}"
            )

            # Return column_data, dropdown_data, vsd_performance_data, and metadata fields
            return ResponseBuilder.success(
                data={
                    "column_data": pump_data_result.get("column_data", []),
                    "dropdown_data": pump_data_result.get("dropdown_data", []),
                    "vsd_performance_data": pump_data_result.get("vsd_performance_data"),
                    "data_availability_for_given_date": pump_data_result.get("data_availability_for_given_date", True),
                    "from_date": pump_data_result.get("from_date"),
                    "to_date": pump_data_result.get("to_date")
                },
                message="Pump data retrieved successfully"
            )

        except ValueError as ve:
            # Handle validation errors (site not found, table not found, pump not found)
            error_message = str(ve)
            logger.error(
                f"Validation error for pump {site_id}/{Pump_Category}/{pump}/{Pump_id}: {error_message}"
            )

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
            logger.error(
                f"Error in PumpDataView for pump {site_id}/{Pump_Category}/{pump}/{Pump_id}: {str(e)}",
                exc_info=True
            )
            return ResponseBuilder.server_error(
                message="Failed to retrieve pump data",
                data={"error": str(e)}
            )
