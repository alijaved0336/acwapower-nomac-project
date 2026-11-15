import logging
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.dash_071 import Dash_071Service
from interface.schemas.dash_071 import ChemicalAnalysisResponseSchema
from infrastructure.utils.clickhouse.clickhouse_utils import (
    parse_date_range,
    validate_date_range_extended,
    parse_datetime_to_object
)

logger = logging.getLogger(__name__)

class Area(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_areas",
        operation_summary="Get areas for chemical graph retrieval",
        operation_description=(
            "Fetches areas dynamically based on the specific Site ID.\n\n"
            "**Behavior:**\n"
            "- If `site_id` is provided: Returns only areas configured for that specific site\n"
            "- If `site_id` is omitted: Returns all available areas across all sites\n\n"
            "**Response Format:**\n"
            "Returns areas formatted for dropdown UI with `label` and `value` fields."
        ),
        manual_parameters=[
            openapi.Parameter(
                'site_id',
                openapi.IN_QUERY,
                description="Site identifier (e.g., 'Rabigh3', 'Jubail-Jazlah', 'STPC', 'UAQ'). "
                           "When provided, returns only areas available for that site.",
                type=openapi.TYPE_STRING,
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "areas": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "label": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                description="Display name for dropdown"
                                            ),
                                            "value": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                description="Value to use in subsequent API calls"
                                            )
                                        }
                                    ),
                                    description="List of areas formatted for dropdown UI"
                                )
                            }
                        )
                    }
                )
            ),
            500: openapi.Response(
                "Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        },
        tags=["Dash-071"],
    )
    def get(self, request):
        site = request.GET.get('site_id', None)

        logger.info(f"Fetching areas for site_id: {site if site else 'all sites'}")

        try:
            with Dash_071Service() as service:
                areas = service.get_area_values(site=site)

                logger.info(f"Successfully retrieved {len(areas)} areas for site_id: {site if site else 'all'}")

                return ResponseBuilder.success(
                    data={"areas": areas},
                    message="Areas retrieved successfully"
                )
        except Exception as e:
            logger.error(f"Failed to retrieve areas for site_id {site}: {str(e)}")
            return ResponseBuilder.server_error(
                message="Failed to retrieve areas",
                data={"error": str(e)}
            )


class Chemicals(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_chemicals",
        operation_summary="Get chemicals against areas based on site for chemical graph retrieval",
        operation_description="Fetches chemicals against areas based on site for chemical graphs retrieval",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('area', openapi.IN_QUERY, description="Area", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response("Success", ChemicalAnalysisResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-071"],
    )
    def get(self, request):
        site = request.GET.get("site_id")
        area = request.GET.get("area")

        # Basic validation
        if not site or not area:
            return ResponseBuilder.error(
                message="Both 'site_id' and 'area' query parameters are required.",
                data={"chemicals": []}
            )

        try:
            with Dash_071Service() as service:
                chemicals_rows = service.get_chemical_list(site=site, area=area)

                if not chemicals_rows:
                    return ResponseBuilder.success(
                        data={"chemicals": []},
                        message=f"No chemicals found for site '{site}' and area '{area}'."
                    )

                # Always return a DRF-compatible Response on success
                return ResponseBuilder.success(
                    data={"chemicals": chemicals_rows},
                    message="Chemicals retrieved successfully"
                )

        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve chemicals",
                data={"error": str(e)}
            )


class ChemicalsData(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def _build_column_requests(columns, site, table):
        """
        Build column request list with inferred types.

        Args:
            columns: List of column definitions (dict or str)
            site: Site name
            table: Table name

        Returns:
            List of column request dictionaries
        """
        column_request = []
        for col in columns:
            if isinstance(col, dict):
                name = col["columnName"]
                ctype = col.get("columnType")
                if not ctype:
                    lname = str(name).lower()
                    ctype = "timestamp[ns]" if (
                            lname == "datetime" or lname.endswith("datetime") or lname == "timestamp") else "double"
            else:
                name = col
                lname = str(name).lower()
                ctype = "timestamp[ns]" if (
                        lname == "datetime" or lname.endswith("datetime") or lname == "timestamp") else "double"

            column_request.append({
                "siteName": site,
                "tableName": table,
                "columnName": name,
                "columnType": ctype
            })
        return column_request

    @swagger_auto_schema(
        operation_id="chemicals-data-post",
        operation_summary="Chemical data for graphs based on site, area, and chemical",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING,
                              required=True),
            openapi.Parameter('area', openapi.IN_QUERY, description="Area", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('from_date', openapi.IN_QUERY, description="Start Date", type=openapi.TYPE_STRING,
                              required=False),
            openapi.Parameter('to_date', openapi.IN_QUERY, description="End date", type=openapi.TYPE_STRING,
                              required=False),
            openapi.Parameter('chemical', openapi.IN_QUERY, description="Chemical", type=openapi.TYPE_STRING,
                              required=True),
        ],
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
        },
        tags=["Dash-071"],
    )
    def post(self, request):
        site = request.GET.get("site_id", None)
        from_date_str = request.GET.get("from_date", None)
        to_date_str = request.GET.get("to_date", None)
        area = request.GET.get("area")
        chemical = request.GET.get("chemical")

        # Validation
        if not site:
            return ResponseBuilder.error(
                message="site_id is required",
                data=""
            )

        if not area:
            return ResponseBuilder.error(message="area is required", data="")

        if not chemical:
            return ResponseBuilder.error(message="chemical is required", data="")

        try:
            start_date, end_date = parse_date_range(
                from_date=from_date_str,
                to_date=to_date_str,
                default_days=7
            )

            # Validate date range
            is_valid, error_msg = validate_date_range_extended(start_date, end_date, max_days=90)
            if not is_valid:
                return ResponseBuilder.error(
                    message=f"Invalid date range: {error_msg}",
                    data=""
                )

            logger.info(
                f"ChemicalsData: Parsed date range - "
                f"from_date: {start_date}, to_date: {end_date}"
            )

        except (ValueError, Exception) as e:
            return ResponseBuilder.error(
                message=f"Invalid date format: {str(e)}",
                data=""
            )

        # Use new EAV-based service method
        try:
            with Dash_071Service() as service:
                result = service.get_chemical_data(
                    site=site,
                    area=area,
                    chemical=chemical,
                    from_date=start_date,
                    to_date=end_date,
                )

                # Check for errors
                if "error" in result:
                    return ResponseBuilder.server_error(
                        message=f"Failed to retrieve chemical data: {result['error']}",
                        data=result
                    )

                # Determine message based on whether fallback was used
                data_available = result.get("data_availability_for_given_date", True)
                if data_available:
                    message = f"Successfully retrieved {chemical} data from {area} area for site {site}"
                else:
                    message = (
                        f"No data found for requested date range. Retrieved last 7 days of available data "
                        f"({result.get('from_date')} to {result.get('to_date')}) for {chemical} "
                        f"from {area} area for site {site}"
                    )

                return ResponseBuilder.success(
                    data=result,
                    message=message
                )

        except Exception as e:
            logger.exception(f"Error in ChemicalsData endpoint: {e}")
            return ResponseBuilder.server_error(
                message="Failed to retrieve chemical data",
                data={"error": str(e)}
            )

        column_request = self._build_column_requests(graph_cols, site, table_name)

        clickhouse_service = ClickHouseADLSService()

        # Get data with built-in fallback logic
        graph_response = clickhouse_service.get_column_data_sources(
            columns_list=column_request,
            from_date=start_date,
            to_date=end_date,
            enable_fallback=True  # Dashboard API - enable fallback to last 7 days
        )

        # Extract column data and metadata from response
        if isinstance(graph_response, dict) and 'column_data' in graph_response:
            graph_column_data = graph_response.get('column_data', [])
            graph_metadata = graph_response.get('metadata', {
                "data_availability_for_given_date": True,
                "from_date": start_date,
                "to_date": end_date
            })
        else:
            # Fallback for unexpected format
            logger.warning("Graph response is not in expected dict format")
            graph_column_data = graph_response if isinstance(graph_response, list) else []
            graph_metadata = {
                "data_availability_for_given_date": True,
                "from_date": start_date,
                "to_date": end_date
            }

        # ---------------------------
        # TABLE PULL
        # ---------------------------
        try:
            table_cols = chem_entry["table"]["columns"]
        except KeyError as e:
            return ResponseBuilder.success(
                message=f"Mapping for '{chemical}' in area '{area}' is missing TABLE columns: {e}",
                data=""
            )

        column_request = self._build_column_requests(table_cols, site, table_name)

        table_response = clickhouse_service.get_column_data_sources(
            columns_list=column_request,
            from_date=start_date,
            to_date=end_date,
            enable_fallback=True  # Dashboard API - enable fallback to last 7 days
        )

        # Extract column data and metadata from response
        if isinstance(table_response, dict) and 'column_data' in table_response:
            table_column_data = table_response.get('column_data', [])
            table_metadata = table_response.get('metadata', {
                "data_availability_for_given_date": True,
                "from_date": start_date,
                "to_date": end_date
            })
        else:
            # Fallback for unexpected format
            logger.warning("Table response is not in expected dict format")
            table_column_data = table_response if isinstance(table_response, list) else []
            table_metadata = {
                "data_availability_for_given_date": True,
                "from_date": start_date,
                "to_date": end_date
            }

        # Apply date filtering to table data before serialization
        filtered_table_data = chemical_service.filter_latest_records_by_date(table_column_data)

        # Serialize the data (now passing the actual column data, not the dict)
        graph_payload = serialize_column_responses(graph_column_data)
        table_payload = serialize_column_responses(filtered_table_data)

        # Use graph metadata (or table metadata if graph is empty)
        final_metadata = graph_metadata if graph_column_data else table_metadata

        # Prepare response with fallback metadata
        response_data = {
            "graph": graph_payload,
            "table": table_payload,
            # Append fallback metadata
            "data_availability_for_given_date": final_metadata.get("data_availability_for_given_date", True),
            "from_date": final_metadata.get("from_date"),
            "to_date": final_metadata.get("to_date")
        }

        # Determine message based on whether fallback was used
        if final_metadata.get("data_availability_for_given_date", True):
            message = f"Successfully retrieved {chemical} data from {area} area for site {site}"
        else:
            message = (f"No data found for requested date range. Retrieved last 7 days of available data "
                      f"({final_metadata.get('from_date')} to {final_metadata.get('to_date')}) for {chemical} "
                      f"from {area} area for site {site}")

        return ResponseBuilder.success(
            data=response_data,
            message=message
        )


class ChemicalDataByMetric(APIView):
    """
    API endpoint for retrieving chemical data segregated by metric type.

    This endpoint fetches all data for a specific chemical in one query,
    then separates it into Graph data (ppm, flow) and Table data (consumption).
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="chemical-data-by-metric",
        operation_summary="Get chemical data segregated by metric type (Graph vs Table)",
        operation_description=(
            "Fetches chemical data and segregates it based on the Metric column:\n\n"
            "**Graph Data (Visual Trends):**\n"
            "- Metric = 'ppm' → PPM measurements with unit indicator\n"
            "- Metric = 'Flow' → Flow measurements with unit indicator\n\n"
            "**Table Data (Consumption Reports):**\n"
            "- Metric = 'Consumption_per_Day' → Daily consumption\n"
            "- Metric = 'Consumption_per_Month' → Monthly consumption\n"
            "- Metric = 'Consumption_per_Year' → Yearly consumption\n\n"
            "**Implementation:**\n"
            "- Single query fetches all data for the chemical\n"
            "- Post-processing segregates by metric type\n"
            "- Table data is formatted date-wise for tabular view"
        ),
        manual_parameters=[
            openapi.Parameter(
                'site_id', openapi.IN_QUERY,
                description="Site identifier (e.g., 'Rabigh3', 'Jubail-Jazlah')",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'area', openapi.IN_QUERY,
                description="Area filter (e.g., 'RO', 'Pre-treatment', 'Post-treatment')",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'chemical', openapi.IN_QUERY,
                description="Chemical name (e.g., 'Ferric Chloride', 'Sodium Hypochlorite')",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'from_date', openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD or YYYY-MM-DD,HH:MM:SS)",
                type=openapi.TYPE_STRING, required=False
            ),
            openapi.Parameter(
                'to_date', openapi.IN_QUERY,
                description="End date (YYYY-MM-DD or YYYY-MM-DD,HH:MM:SS)",
                type=openapi.TYPE_STRING, required=False
            ),
        ],
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "graph": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Graph data for visual trends",
                                    properties={
                                        "ppm": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            description="PPM measurements",
                                            items=openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "dateTime": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "stream": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                                    "unit": openapi.Schema(type=openapi.TYPE_STRING)
                                                }
                                            )
                                        ),
                                        "flow": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            description="Flow measurements",
                                            items=openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "dateTime": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "stream": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                                    "unit": openapi.Schema(type=openapi.TYPE_STRING)
                                                }
                                            )
                                        )
                                    }
                                ),
                                "table": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Table data for consumption reports (date-wise)",
                                    properties={
                                        "rows": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "date": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "daily": openapi.Schema(
                                                        type=openapi.TYPE_ARRAY,
                                                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                                    ),
                                                    "monthly": openapi.Schema(
                                                        type=openapi.TYPE_ARRAY,
                                                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                                    ),
                                                    "yearly": openapi.Schema(
                                                        type=openapi.TYPE_ARRAY,
                                                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                                    )
                                                }
                                            )
                                        ),
                                        "columns": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_STRING)
                                        ),
                                        "total_rows": openapi.Schema(type=openapi.TYPE_INTEGER)
                                    }
                                ),
                                "data_availability_for_given_date": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                "from_date": openapi.Schema(type=openapi.TYPE_STRING),
                                "to_date": openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response("Bad Request"),
            500: openapi.Response("Server Error"),
        },
        tags=["Dash-071"],
    )
    def get(self, request):
        """
        GET /api/chemical-data-by-metric

        Retrieves chemical data segregated by metric type for graph and table views.
        """
        site = request.GET.get("site_id")
        area = request.GET.get("area")
        chemical = request.GET.get("chemical")
        from_date_str = request.GET.get("from_date")
        to_date_str = request.GET.get("to_date")

        # Validation
        if not site:
            return ResponseBuilder.error(message="site_id is required", data="")

        if not area:
            return ResponseBuilder.error(message="area is required", data="")

        if not chemical:
            return ResponseBuilder.error(message="chemical is required", data="")

        # Parse dates
        start_date = None
        end_date = None

        try:
            start_date, end_date = parse_date_range(
                from_date=from_date_str,
                to_date=to_date_str,
                default_days=7
            )

            # Validate date range
            is_valid, error_msg = validate_date_range_extended(start_date, end_date, max_days=90)
            if not is_valid:
                return ResponseBuilder.error(
                    message=f"Invalid date range: {error_msg}",
                    data=""
                )

            logger.info(
                f"ChemicalDataByMetric: site={site}, area={area}, chemical={chemical}, "
                f"from_date={start_date}, to_date={end_date}"
            )

        except (ValueError, Exception) as e:
            return ResponseBuilder.error(
                message=f"Invalid date format: {str(e)}",
                data=""
            )

        try:
            with Dash_071Service() as service:
                # Use get_chemical_data which returns ColumnData[] format for graph and table
                result = service.get_chemical_data(
                    site=site,
                    area=area,
                    chemical=chemical,
                    from_date=start_date,
                    to_date=end_date
                )

                # Check for errors
                if "error" in result:
                    return ResponseBuilder.server_error(
                        message=f"Failed to retrieve chemical data: {result['error']}",
                        data=result
                    )

            # Extract metadata from result
            data_available = result.get("data_availability_for_given_date", True)

            # Build response with ColumnData[] format for graph and table
            response_data = {
                "graph": result.get("graph", []),
                "table": result.get("table", []),
                "data_availability_for_given_date": data_available,
                "from_date": result.get("from_date"),
                "to_date": result.get("to_date")
            }

            # Determine message
            graph_count = len(result.get("graph", []))
            table_count = len(result.get("table", []))

            if data_available:
                message = (
                    f"Successfully retrieved {chemical} data for {area} area in {site}. "
                    f"Graph columns: {graph_count}, Table columns: {table_count}"
                )
            else:
                message = (
                    f"No data found for requested date range. Retrieved last 7 days of available data "
                    f"({result.get('from_date')} to {result.get('to_date')}) for {chemical}"
                )

            return ResponseBuilder.success(data=response_data, message=message)

        except Exception as e:
            logger.exception(f"Failed to fetch chemical data by metric: {e}")
            return ResponseBuilder.server_error(
                message="Failed to retrieve chemical data",
                data={"error": str(e)}
            )


class ChemicalsStock(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="chemicals-stock",
        operation_summary="Chemical Stock Data",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY, description="Optional exact date (YYYY-MM-DD) for point lookup",
                              type=openapi.TYPE_STRING, required=False),

        ],
        responses={200: openapi.Response("Success"), 400: openapi.Response("Bad Request")},
        tags=["Dash-071"],
    )
    def post(self, request):
        site = request.GET.get("site_id")
        target_date_str = request.GET.get("date")  # optional 'YYYY-MM-DD'

        if not site:
            return ResponseBuilder.error(message="site_id is required", data="")

        # Parse target date if provided
        target_date = None
        if target_date_str:
            try:
                target_date = parse_datetime_to_object(
                    target_date_str,
                    set_end_of_day=False
                )
                logger.info(f"ChemicalsStock: Parsed target_date: {target_date}")
            except (ValueError, Exception) as e:
                return ResponseBuilder.error(
                    message=f"Invalid date format: {str(e)}",
                    data=""
                )

        # Use new EAV-based service method
        try:
            with Dash_071Service() as service:
                result = service.get_chemical_stock_data(
                    site=site,
                    target_date=target_date,
                )

                # Check for errors
                if "error" in result:
                    return ResponseBuilder.server_error(
                        message=f"Failed to retrieve chemical stock data: {result['error']}",
                        data=result
                    )

                # Determine message based on whether fallback was used
                data_available = result.get("data_availability_for_given_date", True)
                chem_count = len(result.get("chemicals", {}))

                if data_available:
                    message = f"Fetched chemical stock data for {chem_count} chemicals (latest values)"
                else:
                    message = (
                        f"No data found for requested date. Retrieved latest available data "
                        f"({result.get('from_date')} to {result.get('to_date')}) "
                        f"for {chem_count} chemicals"
                    )

                return ResponseBuilder.success(
                    data=result,
                    message=message
                )

        except Exception as e:
            logger.exception(f"Failed to fetch chemical stock data: {e}")
            return ResponseBuilder.server_error(
                message="Failed to fetch chemical data",
                data={"error": str(e)}
            )


# class ChemicalsStock(APIView):
#     permission_classes = [AllowAny]
#     @swagger_auto_schema(
#         operation_id="chemicals-stock",
#         operation_summary="Chemical Stock Data",
#         manual_parameters=[
#             openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING,
#                               required=True),
#             openapi.Parameter('from_date', openapi.IN_QUERY, description="Start Date", type=openapi.TYPE_STRING,
#                               required=False),
#             openapi.Parameter('to_date', openapi.IN_QUERY, description="End date", type=openapi.TYPE_STRING,
#                               required=False),
#
#         ],
#         responses={
#             200: openapi.Response("Success"),
#             400: openapi.Response("Bad Request"),
#         },
#         tags=["Dash-071"],
#     )
#
#     def post(self, request):
#         site = request.GET.get("site_id")
#         target_date = request.GET.get("date")  # optional 'YYYY-MM-DD'
#         coordinates = str(request.GET.get("coordinates", "false")).lower() == "true"
#
#         if not site:
#             return ResponseBuilder.success("site_id is required", data="")
#
#         try:
#             with Dash_071Service() as svc:
#                 chemical_stocks = svc.get_stocks_mapping(site)
#
#             # --- helpers -----------------------------------------------------
#
#             def _group_by_table(items):
#                 """
#                 items: list of column descriptors (dict or str)
#                 returns: {tableName: [columnName, ...]}, and a flat index that maps back
#                 """
#                 by_table = {}
#                 order = []  # keep (table, column) in original order
#                 for col in items or []:
#                     if isinstance(col, dict):
#                         name = col.get("columnName")
#                         table = col.get("tableName")
#                     else:
#                         # string shorthand not expected here (but keep safe)
#                         name = str(col)
#                         table = None
#                     if not name or not table:
#                         # skip malformed entries
#                         continue
#                     by_table.setdefault(table, []).append(name)
#                     order.append((table, name))
#                 return by_table, order
#
#             def _fetch_for_label(site_name, label_items):
#                 """
#                 For a list of columns (with tableName), fetch data once per table,
#                 then return a list of arrays aligned to the original order, without names.
#                 """
#                 by_table, order = _group_by_table(label_items)
#                 if not order:
#                     return []
#
#                 # call fetch_latest_data once per table
#                 table_data_cache = {}
#                 for table_name, cols in by_table.items():
#                     res = fetch_latest_data(
#                         site=site_name,
#                         table=table_name,
#                         columns=cols,
#                         target_date=target_date,
#                         coordinates=coordinates
#                     )
#                     if not res.get("success") or not res.get("data"):
#                         table_data_cache[table_name] = {}
#                         continue
#                     # columns data is a dict: {colName: [values...]}
#                     table_data_cache[table_name] = res["data"].get("columns", {}) or {}
#
#                 # now reconstruct in original order, but return only the arrays (no names)
#                 arrays_in_order = []
#                 for table_name, col_name in order:
#                     series = table_data_cache.get(table_name, {}).get(col_name, [])
#                     arrays_in_order.append(series)
#                 return arrays_in_order
#
#             def _build_line_block(site_name, line_dict):
#                 """
#                 line_dict: {"measured":[...], "expected":[...]}  (each value is a list of column descriptors)
#                 returns: {"measured":[arr,...], "expected":[arr,...]} with only arrays
#                 """
#                 if not line_dict:
#                     return None
#                 out = {}
#                 if "measured" in line_dict:
#                     out["measured"] = _fetch_for_label(site_name, line_dict.get("measured"))
#                 if "expected" in line_dict:
#                     out["expected"] = _fetch_for_label(site_name, line_dict.get("expected"))
#                 # if nothing fetched, return None to keep payload tidy
#                 return out if (out.get("measured") or out.get("expected")) else None
#
#             def _build_simple_block(site_name, items):
#                 """
#                 items: list of column descriptors
#                 returns: [arr, arr, ...] (arrays only)
#                 """
#                 arrays = _fetch_for_label(site_name, items)
#                 return arrays if arrays else None
#
#             # --- build response ----------------------------------------------
#
#             response_payload = {
#                 "siteName": site,
#                 "dateFilter": target_date or "latest",
#                 "coordinates": coordinates,
#                 "chemicals": {}
#             }
#
#             for chem_name, chem_map in (chemical_stocks or {}).items():
#                 if not isinstance(chem_map, dict):
#                     continue
#
#                 chem_out = {}
#
#                 # line1 / line2 (with measured/expected)
#                 line1 = _build_line_block(site, chem_map.get("line1"))
#                 if line1:
#                     chem_out["line1"] = line1
#
#                 line2 = _build_line_block(site, chem_map.get("line2"))
#                 if line2:
#                     chem_out["line2"] = line2
#
#                 # level1 / level2 / stock (simple lists)
#                 lvl1 = _build_simple_block(site, chem_map.get("level1"))
#                 if lvl1:
#                     chem_out["level1"] = lvl1
#
#                 lvl2 = _build_simple_block(site, chem_map.get("level2"))
#                 if lvl2:
#                     chem_out["level2"] = lvl2
#
#                 stock = _build_simple_block(site, chem_map.get("stock"))
#                 if stock:
#                     chem_out["stock"] = stock
#
#                 # only include chemicals that yielded something
#                 if chem_out:
#                     response_payload["chemicals"][chem_name] = chem_out
#
#             return ResponseBuilder.success(
#                 data=response_payload,
#                 message=f"Fetched chemical data for {len(response_payload['chemicals'])} chemicals"
#             )
#
#         except Exception as e:
#             return ResponseBuilder.server_error(
#                 message="Failed to fetch chemical data",
#                 data={"error": str(e)}
#             )
