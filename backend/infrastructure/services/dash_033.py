from typing import Optional, Dict, List
from datetime import datetime, timedelta, timezone
import logging
import math

from infrastructure.orm.repositories.sparkRepository import SparkRepository
from infrastructure.services.fastMetadataService import FastMetadataService
from infrastructure.services.columnMetadataService import ColumnMetadataService
from infrastructure.utils.queryOptimizer import QueryOptimizer
from infrastructure.utils.datetime_utils import DateTimeParser
from infrastructure.services.dash_001 import Dash_001Service
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, TimestampType

logger = logging.getLogger(__name__)


class Dash_033OptimizedService:
    """
    Optimized Dash_033 Service using robust column handling pattern from cip-flushing.
    All functions now include column diagnostics, flexible matching, and error handling.
    Train data is returned in ascending order.
    """
    
    def __init__(self):
        # Initialize existing repositories
        self.spark_repo = SparkRepository()
        self.fast_metadata_service = FastMetadataService()
        self.column_metadata_service = ColumnMetadataService()
        self.query_optimizer = QueryOptimizer()
    
    def get_defaults(self, user):
        """Get default site for user - unchanged business logic"""
        cluster = user.get("role").get("clusters")[0]           
        all_sites = self.get_sites_by_cluster(cluster)
        site_name = all_sites[0] 
        return site_name
    
    def get_sites_by_cluster(self, cluster: str):
        """Get site names filtered by cluster - unchanged business logic"""
        plant_mappings = {
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_landing": "Jubail Energy Plant",
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_rabigh_landing": "Rabigh Energy Plant",
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_stpc_landing": "STPC Energy Plant",
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_uaq_landing": "UAQ Energy Plant"
        }

        site_names = set()
        for table_name in plant_mappings.keys():
            where_params = {"Cluster_Name": cluster}
            service = Dash_001Service()
            cluster_count = service.plant_repository.get_cluster_count_by_table(table_name, where_params)

            if cluster_count > 0:
                plant_results = service.plant_repository.get_sites_by_cluster_and_table(table_name, where_params)
                for plant_row in plant_results:
                    site_name = plant_row['Site_Name']
                    site_names.add(site_name)

        return list(site_names)
    
    def _map_site_to_site_id(self, site_name: str) -> str:
        """Map site names to site_id format for new architecture"""
        site_map = {
            "Jubail - Jazlah": "Jubail-Jazlah",
            "Rabigh3": "Rabigh3",
            "STPC": "STPC",
            "UAQ": "UAQ",
        }
        return site_map.get(site_name, site_name)
    
    def _map_site_to_table_prefix(self, site_name: str) -> str:
        """Map site names to table prefix"""
        prefix_map = {
            "Jubail - Jazlah": "Jubail-Jazlah",
            "Rabigh3": "r3",
            "STPC": "STPC",
            "UAQ": "UAQ",
        }
        return prefix_map.get(site_name, "")
    
    def _build_table_id(self, site_name: str, table_suffix: str) -> str:
        """Build table_id from site and suffix"""
        prefix = self._map_site_to_table_prefix(site_name)
        return f"{prefix}{table_suffix}"
    
    def _filter_by_datetime_spark(self, spark_df, start_col, end_col, start_time=None, end_time=None):
        """
        Apply datetime filtering using Spark DataFrame operations.
        Mimics the filter_by_datetime function from the original file.
        """
        try:
            # Ensure datetime columns are properly cast
            df = spark_df.withColumn(start_col, F.col(start_col).cast(TimestampType())) \
                        .withColumn(end_col, F.col(end_col).cast(TimestampType()))
            
            if start_time and end_time:
                # Parse provided times
                start_dt = F.lit(start_time).cast(TimestampType())
                end_dt = F.lit(end_time).cast(TimestampType())
            else:
                # Default: last 7 days until now
                end_dt = F.current_timestamp()
                start_dt = end_dt - F.expr("INTERVAL 7 DAYS")
            
            # Filter: records fully inside range
            filtered_df = df.filter(
                (F.col(start_col) >= start_dt) & (F.col(end_col) <= end_dt)
            )
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error in datetime filtering: {e}")
            return spark_df  # Return original if filtering fails
    
    def _filter_by_racks_spark(self, spark_df, racks: Optional[List[str]]):
        """
        Apply rack filtering using flexible column matching.
        
        Args:
            spark_df: Spark DataFrame
            racks: List of rack IDs to filter by
            
        Returns:
            Filtered DataFrame or original if no racks filter or no matching column found
        """
        try:
            if not racks or not isinstance(racks, list) or len(racks) == 0:
                print("[RACK_FILTER] No racks filter provided, returning original DataFrame")
                return spark_df
            
            available_columns = spark_df.columns
            print(f"[RACK_FILTER] Available columns: {available_columns}")
            print(f"[RACK_FILTER] Filtering by racks: {racks}")
            
            # Find Train/Rack column using flexible matching
            train_column = None
            train_possible = ["Train", "train", "Train_ID", "train_id", "Unit", "unit", "Rack", "rack"]
            
            for col_name in train_possible:
                if col_name in available_columns:
                    train_column = col_name
                    print(f"[RACK_FILTER] Found train column: {train_column}")
                    break
            
            if not train_column:
                print(f"[RACK_FILTER] No train column found for rack filtering. Available: {available_columns}")
                return spark_df  # Return original if no Train column found
            
            # Apply rack filtering
            filtered_df = spark_df.filter(F.col(train_column).isin(racks))
            filtered_count = filtered_df.count()
            original_count = spark_df.count()
            
            print(f"[RACK_FILTER] Filtered from {original_count} to {filtered_count} records using racks: {racks}")
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error in rack filtering: {e}")
            return spark_df  # Return original if filtering fails

    def _filter_by_mode_spark(self, spark_df, modes: Optional[List[str]]):
        """
        Apply mode filtering using flexible column matching.
        
        Args:
            spark_df: Spark DataFrame
            modes: List of mode values to filter by
            
        Returns:
            Filtered DataFrame or original if no modes filter or no matching column found
        """
        try:
            if not modes or not isinstance(modes, list) or len(modes) == 0:
                print("[MODE_FILTER] No modes filter provided, returning original DataFrame")
                return spark_df
            
            available_columns = spark_df.columns
            print(f"[MODE_FILTER] Available columns: {available_columns}")
            print(f"[MODE_FILTER] Filtering by modes: {modes}")
            
            # Find Mode column using flexible matching
            mode_column = None
            mode_possible = ["Mode_Validated"]
            
            for col_name in mode_possible:
                if col_name in available_columns:
                    mode_column = col_name
                    print(f"[MODE_FILTER] Found mode column: {mode_column}")
                    break
            
            if not mode_column:
                print(f"[MODE_FILTER] No mode column found for mode filtering. Available: {available_columns}")
                return spark_df  # Return original if no Mode column found
            
            # Apply mode filtering
            filtered_df = spark_df.filter(F.col(mode_column).isin(modes))
            filtered_count = filtered_df.count()
            original_count = spark_df.count()
            
            print(f"[MODE_FILTER] Filtered from {original_count} to {filtered_count} records using modes: {modes}")
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error in mode filtering: {e}")
            return spark_df  # Return original if filtering fails
    
    def _get_data_using_existing_repos(
        self,
        site_id: str,
        table_id: str,
        operation: str = "query",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Get data using existing repository functions with robust error handling.
        """
        try:
            start_time = datetime.now()
            print(f"Starting {operation} operation for {site_id}/{table_id}")
            
            # Use SparkRepository for all operations to avoid conversion issues
            try:
                print(f"Using SparkRepository for {operation}...")
                
                # Use the optimized read method from SparkRepository
                spark_df = self.spark_repo.read_parquet_optimized(
                    siteName=site_id,
                    tableName=table_id,
                    from_date=from_date,
                    to_date=to_date,
                    columns=columns,
                    limit=limit
                )
                
                row_count = spark_df.count() if spark_df else 0
                print(f"Retrieved {row_count} rows using SparkRepository")
                
                return {
                    "success": True,
                    "spark_df": spark_df,
                    "row_count": row_count,
                    "method_used": "spark_repository"
                }
                
            except Exception as e:
                print(f"SparkRepository failed: {e}")
                return self._create_fallback_response(site_id, table_id, str(e))
                
        except Exception as e:
            logger.error(f"Data retrieval failed: {e}")
            return self._create_fallback_response(site_id, table_id, str(e))
    
    def _create_fallback_response(self, site_id: str, table_id: str, error: str) -> Dict:
        """Create fallback response when all methods fail"""
        print(f"All methods failed for {site_id}/{table_id}: {error}")
        
        return {
            "success": False,
            "error": f"All processing methods failed for {site_id}/{table_id}: {error}",
            "spark_df": None,
            "row_count": 0,
            "method_used": "fallback"
        }

    def get_racks_runtime_only(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Get rack runtime percentages with proper calculation logic from original file and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_racks_operation")
            
            print(f"Getting runtime data for {site_id}/{table_id} with racks filter: {racks}")
            
            # Use existing SparkRepository for data retrieval
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=start_time,
                to_date=end_time
            )
            
            if result["success"] and result["spark_df"]:
                spark_df = result["spark_df"]
                
                # DIAGNOSE AVAILABLE COLUMNS
                available_columns = spark_df.columns
                print(f"[RUNTIME] Available columns: {available_columns}")
                
                # ENHANCED FLEXIBLE COLUMN MATCHING - Now includes Duration_day
                column_mappings = {
                    "Train": ["Train", "train", "Train_ID", "train_id", "Unit", "unit", "Rack", "rack"],
                    "Start_Time": ["Start_Time", "start_time", "StartTime", "start", "Begin_Time", "Datetime"],
                    "End_Time": ["End_Time", "end_time", "EndTime", "end", "Finish_Time"],
                    "Duration_Hours": ["Duration_Hours", "duration_hours", "Duration", "duration", "Runtime_Hours"],
                    "Duration_Days": ["Duration_day", "Duration_Days", "duration_day", "duration_days", "Duration_Day"]
                }
                
                found_columns = {}
                duration_unit = None  # Track whether we found hours or days
                
                for standard_name, possible_names in column_mappings.items():
                    for possible_name in possible_names:
                        if possible_name in available_columns:
                            found_columns[standard_name] = possible_name
                            print(f"[RUNTIME] Mapped {standard_name} -> {possible_name}")
                            
                            # Track duration unit type
                            if standard_name == "Duration_Hours":
                                duration_unit = "hours"
                            elif standard_name == "Duration_Days":
                                duration_unit = "days"
                            break
                
                if not found_columns.get("Train"):
                    print(f"[RUNTIME] No Train column found. Available: {available_columns}")
                    sample_data = spark_df.limit(3).collect()
                    return {
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "sample_data": [row.asDict() for row in sample_data[:2]] if sample_data else [],
                            "message": "No Train column found for runtime calculation"
                        }
                    }
                
                # Apply rack filtering FIRST
                filtered_df = self._filter_by_racks_spark(spark_df, racks)
                
                # Apply date filtering if columns are available
                if found_columns.get("Start_Time") and found_columns.get("End_Time"):
                    filtered_df = self._filter_by_datetime_spark(
                        filtered_df, 
                        found_columns["Start_Time"], 
                        found_columns["End_Time"], 
                        start_time, 
                        end_time
                    )
                
                # Process runtime calculations using found columns and duration unit
                runtime_df = self._calculate_runtime_percentage_spark(
                    filtered_df, found_columns, duration_unit
                )
                
                if runtime_df:
                    return self._format_runtime_result_spark(runtime_df)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in get_racks_runtime_only: {e}")
            return {}

    def _calculate_runtime_percentage_spark(self, spark_df, found_columns, duration_unit=None):
        """
        Calculate runtime percentage using Spark operations.
        Replicates the logic from calculate_runtime_percentage in the original file.
        Train data is sorted in ascending order.
        Now includes Start_Time and End_Time in the result.
        Supports both Duration_Hours and Duration_Days with automatic conversion.
        """
        try:
            train_col = found_columns.get("Train")
            start_col = found_columns.get("Start_Time")
            end_col = found_columns.get("End_Time") 
            duration_col_hours = found_columns.get("Duration_Hours")
            duration_col_days = found_columns.get("Duration_Days")
            
            # Determine which duration column to use
            duration_col = duration_col_hours or duration_col_days
            
            if not train_col:
                print("[RUNTIME_CALC] No Train column available")
                return None
            
            # Ensure timestamp columns are properly cast
            if start_col and end_col:
                df = spark_df.withColumn(start_col, F.col(start_col).cast(TimestampType())) \
                            .withColumn(end_col, F.col(end_col).cast(TimestampType()))
            else:
                df = spark_df
            
            # Handle duration conversion if needed
            if duration_col:
                print(f"[RUNTIME_CALC] Using duration column: {duration_col} with unit: {duration_unit}")
                
                if duration_unit == "days" and duration_col_days:
                    # Convert days to hours: multiply by 24
                    df = df.withColumn("duration_hours_converted", 
                        F.col(duration_col_days).cast(DoubleType()) * 24.0)
                    duration_col_to_use = "duration_hours_converted"
                    print("[RUNTIME_CALC] Converted days to hours (days * 24)")
                elif duration_unit == "hours" and duration_col_hours:
                    # Use hours directly
                    df = df.withColumn("duration_hours_converted", 
                        F.col(duration_col_hours).cast(DoubleType()))
                    duration_col_to_use = "duration_hours_converted"
                    print("[RUNTIME_CALC] Using hours directly")
                else:
                    # Fallback - assume the column is in hours
                    df = df.withColumn("duration_hours_converted", 
                        F.col(duration_col).cast(DoubleType()))
                    duration_col_to_use = "duration_hours_converted"
                    print("[RUNTIME_CALC] Using duration column as-is (assuming hours)")
            else:
                duration_col_to_use = None
            
            # Group by Train and calculate runtime metrics
            # This replicates the original logic:
            # - Calculate total_hours as span from min start to max end time
            # - Sum duration_hours for runtime_hours
            # - Calculate runtime_pct = (runtime_hours / total_hours) * 100
            
            if start_col and end_col and duration_col_to_use:
                # Full calculation with time span and converted duration
                runtime_df = df.groupBy(train_col).agg(
                    F.min(start_col).alias("min_start"),
                    F.max(end_col).alias("max_end"),
                    F.sum(duration_col_to_use).alias("runtime_hours")
                ).withColumn(
                    "total_hours",
                    (F.col("max_end").cast("long") - F.col("min_start").cast("long")) / 3600.0
                ).withColumn(
                    "runtime_pct",
                    F.when(F.col("total_hours") > 0, 
                        (F.col("runtime_hours") / F.col("total_hours")) * 100)
                    .otherwise(0.0)
                ).withColumn(
                    "stoptime_pct", 
                    100.0 - F.col("runtime_pct")
                ).select(
                    F.col(train_col).alias("Rack_ID"),
                    F.col("min_start").alias("Start_Time"),
                    F.col("max_end").alias("End_Time"),
                    F.col("total_hours").alias("Total_Hours"),
                    F.col("runtime_hours").alias("Runtime_Hours"),
                    F.col("runtime_pct").alias("Runtime_%"),
                    F.col("stoptime_pct").alias("Stoptime_%")
                ).orderBy("Rack_ID")  # Sort by Train/Rack_ID in ascending order
                
                print(f"[RUNTIME_CALC] Calculated runtime using time span and converted duration")
                
            elif duration_col_to_use:
                # Simplified calculation with just converted duration
                runtime_df = df.groupBy(train_col).agg(
                    F.min(start_col).alias("min_start") if start_col else F.lit(None).alias("min_start"),
                    F.max(end_col).alias("max_end") if end_col else F.lit(None).alias("max_end"),
                    F.sum(duration_col_to_use).alias("runtime_hours")
                ).withColumn(
                    "total_hours", F.lit(24.0)  # Assume 24 hour period
                ).withColumn(
                    "runtime_pct", 
                    F.when(F.col("runtime_hours") > 0,
                        F.least((F.col("runtime_hours") / F.col("total_hours")) * 100, F.lit(100.0)))
                    .otherwise(0.0)
                ).withColumn(
                    "stoptime_pct", 
                    100.0 - F.col("runtime_pct")
                ).select(
                    F.col(train_col).alias("Rack_ID"),
                    F.col("min_start").alias("Start_Time"),
                    F.col("max_end").alias("End_Time"),
                    F.col("total_hours").alias("Total_Hours"),
                    F.col("runtime_hours").alias("Runtime_Hours"),
                    F.col("runtime_pct").alias("Runtime_%"),
                    F.col("stoptime_pct").alias("Stoptime_%")
                ).orderBy("Rack_ID")  # Sort by Train/Rack_ID in ascending order
                
                print(f"[RUNTIME_CALC] Calculated runtime using converted duration only")
                
            else:
                # Fallback - just count records
                runtime_df = df.groupBy(train_col).agg(
                    F.min(start_col).alias("min_start") if start_col else F.lit(None).alias("min_start"),
                    F.max(end_col).alias("max_end") if end_col else F.lit(None).alias("max_end"),
                    F.count("*").alias("record_count")
                ).withColumn(
                    "runtime_pct", F.lit(75.0)  # Default runtime percentage
                ).withColumn(
                    "stoptime_pct", F.lit(25.0)  # Default stoptime percentage
                ).select(
                    F.col(train_col).alias("Rack_ID"),
                    F.col("min_start").alias("Start_Time"),
                    F.col("max_end").alias("End_Time"),
                    F.lit(24.0).alias("Total_Hours"),
                    F.lit(18.0).alias("Runtime_Hours"),
                    F.col("runtime_pct").alias("Runtime_%"),
                    F.col("stoptime_pct").alias("Stoptime_%")
                ).orderBy("Rack_ID")  # Sort by Train/Rack_ID in ascending order
                
                print(f"[RUNTIME_CALC] Used fallback calculation (no duration column available)")
            
            return runtime_df
                
        except Exception as e:
            logger.error(f"Error in runtime calculation: {e}")
            return None

    def _format_runtime_result_spark(self, spark_df) -> dict:
        """Format runtime results matching the original format with Duration_Hours and End_Time included"""
        try:
            if not spark_df:
                return {}
            
            result_data = spark_df.collect()
            
            racks = [row["Rack_ID"] for row in result_data]
            runtime_pct = [f"{row['Runtime_%']:.2f}" if row['Runtime_%'] is not None else "0.00" for row in result_data]
            stoptime_pct = [f"{row['Stoptime_%']:.2f}" if row['Stoptime_%'] is not None else "0.00" for row in result_data]
            duration_hours = [f"{row['Runtime_Hours']:.2f}" if row['Runtime_Hours'] is not None else "0.00" for row in result_data]
            
            # Format End_Time as it comes from DB
            end_times = []
            for row in result_data:
                try:
                    end_time = row['End_Time'] if 'End_Time' in row else None
                except:
                    # Fallback to attribute access
                    end_time = getattr(row, 'End_Time', None)
                
                if end_time is not None:
                    # Keep the original format from DB
                    if hasattr(end_time, 'strftime'):
                        end_times.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        end_times.append(str(end_time))
                else:
                    end_times.append(None)
            
            return {
                "rackruntimestoptime": {
                    "G1": {
                        "x": [{"name": "Racks", "data": racks}],
                        "y": [
                            {"name": "Runtime %", "data": runtime_pct},
                            {"name": "Stoptime %", "data": stoptime_pct},
                            {"name": "Duration Hours", "data": duration_hours},
                            {"name": "End_Time", "data": end_times}
                        ]
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error formatting runtime result: {e}")
            return {}
        
    def get_membrane_graph_averages(
        self,
        site_name: str = None,
        user: dict = None,
        col_pre: str = "AVG_Salt_Passage_Normalized_Pre",
        col_post: str = "AVG_Salt_Passage_Normalized_Post",
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Get membrane graph averages with proper calculation logic from original file and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_maintenance")
            
            # Use existing SparkRepository
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=start_time,
                to_date=end_time
            )
            
            if result["success"] and result["spark_df"]:
                spark_df = result["spark_df"]
                
                # DIAGNOSE AVAILABLE COLUMNS
                available_columns = spark_df.columns
                print(f"[MEMBRANE_AVG] Available columns: {available_columns}")
                
                # FLEXIBLE COLUMN MATCHING
                train_column = None
                train_possible = ["Train", "train", "Train_ID", "Unit", "Rack"]
                for col_name in train_possible:
                    if col_name in available_columns:
                        train_column = col_name
                        print(f"[MEMBRANE_AVG] Found train column: {train_column}")
                        break
                
                if not train_column:
                    print(f"[MEMBRANE_AVG] No train column found. Available: {available_columns}")
                    sample_data = spark_df.limit(3).collect()
                    return {
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "sample_data": [row.asDict() for row in sample_data[:2]] if sample_data else [],
                            "message": "No Train column found"
                        }
                    }
                
                # Apply rack filtering FIRST
                filtered_df = self._filter_by_racks_spark(spark_df, racks)
                
                # Find the actual column names for pre and post
                actual_col_pre = None
                actual_col_post = None
                
                # Try exact match first
                if col_pre in available_columns:
                    actual_col_pre = col_pre
                if col_post in available_columns:
                    actual_col_post = col_post
                
                # If not found, try alternatives
                if not actual_col_pre:
                    pre_alternatives = [col_pre, col_pre.lower(), col_pre.replace("AVG_", ""), "Salt_Passage_Pre", "salt_passage_pre"]
                    for alt in pre_alternatives:
                        if alt in available_columns:
                            actual_col_pre = alt
                            print(f"[MEMBRANE_AVG] Found pre column: {actual_col_pre}")
                            break
                
                if not actual_col_post:
                    post_alternatives = [col_post, col_post.lower(), col_post.replace("AVG_", ""), "Salt_Passage_Post", "salt_passage_post"]
                    for alt in post_alternatives:
                        if alt in available_columns:
                            actual_col_post = alt
                            print(f"[MEMBRANE_AVG] Found post column: {actual_col_post}")
                            break
                
                if not actual_col_pre or not actual_col_post:
                    print(f"[MEMBRANE_AVG] Required columns not found. Looking for: {col_pre}, {col_post}")
                    return {
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "requested_pre": col_pre,
                            "requested_post": col_post,
                            "message": f"Columns {col_pre} or {col_post} not found"
                        }
                    }
                
                # Apply date filtering if possible
                if "Start_Time" in available_columns and "End_Time" in available_columns:
                    filtered_df = self._filter_by_datetime_spark(
                        filtered_df, "Start_Time", "End_Time", start_time, end_time
                    )
                
                # Calculate train metrics using found columns
                metrics_df = self._calculate_train_metric_spark(
                    filtered_df, train_column, actual_col_pre, actual_col_post
                )
                
                if metrics_df:
                    return self._format_membrane_result_spark(metrics_df, actual_col_pre, actual_col_post)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in get_membrane_graph_averages: {e}")
            return {}
    
    def _calculate_train_metric_spark(self, spark_df, train_col, col_pre, col_post):
        """
        Calculate train metrics using Spark operations.
        Replicates the logic from calculate_train_metric in the original file.
        Train data is sorted in ascending order.
        """
        try:
            # Group by Train and calculate averages
            # This replicates the original logic:
            # - Calculate average Pre and Post values per Train
            # - Compute percentage as (Avg_Pre / (Avg_Pre + Avg_Post)) * 100
            
            train_avg = spark_df.groupBy(train_col).agg(
                F.avg(col_pre).alias(f"Avg_{col_pre}"),
                F.avg(col_post).alias(f"Avg_{col_post}")
            ).withColumn(
                "Percentage_Pre",
                (F.col(f"Avg_{col_pre}") / (F.col(f"Avg_{col_pre}") + F.col(f"Avg_{col_post}"))) * 100
            ).withColumn(
                "Percentage_Post", 
                (F.col(f"Avg_{col_post}") / (F.col(f"Avg_{col_pre}") + F.col(f"Avg_{col_post}"))) * 100
            ).withColumnRenamed(train_col, "Train").orderBy("Train")  # Sort by Train in ascending order
            
            return train_avg
            
        except Exception as e:
            logger.error(f"Error in train metric calculation: {e}")
            return None
    
    def _format_membrane_result_spark(self, spark_df, col_pre, col_post) -> dict:
        """Format membrane results matching the original format"""
        try:
            if not spark_df:
                return {}
            
            result_data = spark_df.collect()
            trains = [row["Train"] for row in result_data]
            
            pre_values = []
            post_values = []
            pre_percentages = []
            post_percentages = []
            
            for row in result_data:
                pre_val = row[f"Avg_{col_pre}"]
                post_val = row[f"Avg_{col_post}"]
                pre_pct = row["Percentage_Pre"]
                post_pct = row["Percentage_Post"]
                
                pre_values.append(f"{pre_val:.2f}" if pre_val is not None else None)
                post_values.append(f"{post_val:.2f}" if post_val is not None else None)
                pre_percentages.append(f"{pre_pct:.2f}" if pre_pct is not None else None)
                post_percentages.append(f"{post_pct:.2f}" if post_pct is not None else None)
            
            return {
                "rackmembrance": {
                    "G1": {
                        "x": [{"name": "Train", "data": trains}],
                        "y": [
                            {
                                "name": col_pre,
                                "data": {
                                    "value": pre_values,
                                    "percentage": pre_percentages
                                }
                            },
                            {
                                "name": col_post,
                                "data": {
                                    "value": post_values,
                                    "percentage": post_percentages
                                }
                            }
                        ]
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error formatting membrane result: {e}")
            return {}
    
    def get_membrane_graph_percentages(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Get membrane graph percentages with proper calculation logic from original file and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_maintenance")

            # Use existing SparkRepository
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=start_time,
                to_date=end_time
            )
            
            if result["success"] and result["spark_df"]:
                spark_df = result["spark_df"]
                
                # DIAGNOSE AVAILABLE COLUMNS
                available_columns = spark_df.columns
                print(f"[MEMBRANE_PCT] Available columns: {available_columns}")
                
                # FLEXIBLE COLUMN MATCHING
                column_mappings = {
                    "Train": ["Train", "train", "Train_ID", "Unit", "Rack"],
                    "Diff_Salt_Passage_%": ["Diff_Salt_Passage_%", "diff_salt_passage_pct", "Salt_Passage_Diff_%"],
                    "Diff_Norm_DP_%": ["Diff_Norm_DP_%", "diff_norm_dp_pct", "DP_Diff_%"],
                    "Diff_Norm_Perm_Flow_%": ["Diff_Norm_Perm_Flow_%", "diff_norm_perm_flow_pct", "Flow_Diff_%"]
                }
                
                found_columns = {}
                for standard_name, possible_names in column_mappings.items():
                    for possible_name in possible_names:
                        if possible_name in available_columns:
                            found_columns[standard_name] = possible_name
                            print(f"[MEMBRANE_PCT] Mapped {standard_name} -> {possible_name}")
                            break
                
                if not found_columns.get("Train"):
                    print(f"[MEMBRANE_PCT] No train column found. Available: {available_columns}")
                    sample_data = spark_df.limit(3).collect()
                    return {
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "sample_data": [row.asDict() for row in sample_data[:2]] if sample_data else [],
                            "message": "No Train column found"
                        }
                    }
                
                # Apply rack filtering FIRST
                filtered_df = self._filter_by_racks_spark(spark_df, racks)
                
                # Apply date filtering if possible
                if "Start_Time" in available_columns and "End_Time" in available_columns:
                    filtered_df = self._filter_by_datetime_spark(
                        filtered_df, "Start_Time", "End_Time", start_time, end_time
                    )
                
                # Calculate percentage metrics using found columns
                metrics_df = self._calculate_train_metric_single_spark(filtered_df, found_columns)
                
                if metrics_df:
                    return self._format_membrane_percentage_result_spark(metrics_df, found_columns)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in get_membrane_graph_percentages: {e}")
            return {}
    
    def _calculate_train_metric_single_spark(self, spark_df, found_columns):
        """
        Calculate single train metrics using Spark operations.
        Replicates the logic from calculate_train_metric_single in the original file.
        Train data is sorted in ascending order.
        """
        try:
            train_col = found_columns.get("Train")
            
            # Build aggregation expressions for available columns
            agg_exprs = []
            if found_columns.get("Diff_Salt_Passage_%"):
                agg_exprs.append(F.avg(found_columns["Diff_Salt_Passage_%"]).alias("Avg_Diff_Salt_Passage_%"))
            if found_columns.get("Diff_Norm_DP_%"):
                agg_exprs.append(F.avg(found_columns["Diff_Norm_DP_%"]).alias("Avg_Diff_Norm_DP_%"))
            if found_columns.get("Diff_Norm_Perm_Flow_%"):
                agg_exprs.append(F.avg(found_columns["Diff_Norm_Perm_Flow_%"]).alias("Avg_Diff_Norm_Perm_Flow_%"))
            
            if not agg_exprs:
                print("[TRAIN_CALC] No percentage columns found")
                return None
            
            # Group by Train and calculate averages
            train_avg = spark_df.groupBy(train_col).agg(*agg_exprs)\
                .withColumnRenamed(train_col, "Train").orderBy("Train")  # Sort by Train in ascending order
            
            return train_avg
            
        except Exception as e:
            logger.error(f"Error in single train metric calculation: {e}")
            return None
    
    def _format_membrane_percentage_result_spark(self, spark_df, found_columns) -> dict:
        """Format membrane percentage results matching the original format"""
        try:
            if not spark_df:
                return {}
            
            result_data = spark_df.collect()
            trains = [row["Train"] for row in result_data]
            
            y_data = []
            
            # Create y-axis data for each percentage column found
            percentage_columns = ["Diff_Salt_Passage_%", "Diff_Norm_DP_%", "Diff_Norm_Perm_Flow_%"]
            for col_name in percentage_columns:
                if found_columns.get(col_name):
                    values = []
                    avg_col = f"Avg_{col_name}"
                    for row in result_data:
                        val = getattr(row, avg_col, None) if hasattr(row, avg_col) else None
                        values.append(f"{val:.2f}" if val is not None else None)
                    
                    y_data.append({
                        "name": col_name,
                        "data": values
                    })
            
            return {
                "rackmembrance": {
                    "G1": {
                        "x": [{"name": "Train", "data": trains}],
                        "y": y_data
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error formatting membrane percentage result: {e}")
            return {}
    
    def get_cip_validated_info(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ):
        """
        Get CIP validated info with proper filtering, formatting, and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_cip")
            
            print(f"Getting CIP validated data for {site_id}/{table_id} with racks filter: {racks}")
            
            # Use existing SparkRepository for data retrieval
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=start_time,
                to_date=end_time
            )
            
            if result["success"] and result["spark_df"]:
                spark_df = result["spark_df"]
                
                # DIAGNOSE AVAILABLE COLUMNS
                available_columns = spark_df.columns
                print(f"[CIP_VALIDATED] Available columns: {available_columns}")
                
                # FLEXIBLE COLUMN MATCHING for mode validation
                mode_column = None
                possible_mode_columns = ['Mode_Validated', 'mode_validated', 'Mode', 'mode', 'Status', 'status', 'Type', 'type', 'Validation_Status']
                
                for col_name in possible_mode_columns:
                    if col_name in available_columns:
                        mode_column = col_name
                        print(f"[CIP_VALIDATED] Found mode column: {mode_column}")
                        break
                
                if not mode_column:
                    print(f"[CIP_VALIDATED] No mode column found. Available: {available_columns}")
                    sample_data = spark_df.limit(3).collect()
                    return {
                        "items": [],
                        "total": 0,
                        "page": page,
                        "limit": limit,
                        "pages": 0,
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "sample_data": [row.asDict() for row in sample_data[:2]] if sample_data else [],
                            "message": "No mode validation column found"
                        }
                    }
                
                # Apply rack filtering FIRST
                filtered_df = self._filter_by_racks_spark(spark_df, racks)
                
                # Apply date filtering
                if "Start_Time" in available_columns and "End_Time" in available_columns:
                    filtered_df = self._filter_by_datetime_spark(
                        filtered_df, "Start_Time", "End_Time", start_time, end_time
                    )
                
                # Filter for "Validated CIP" records
                validated_df = filtered_df.filter(filtered_df[mode_column] == "Validated CIP")
                total_count = validated_df.count()
                
                print(f"[CIP_VALIDATED] Found {total_count} validated CIP records after rack filtering")
                
                # Apply pagination
                offset = (page - 1) * limit
                paginated_df = validated_df.offset(offset).limit(limit)
                
                # Convert to result format
                data = self._format_flexible_result(paginated_df)
                
                total_pages = math.ceil(total_count / limit) if limit > 0 else 1
                
                return {
                    "items": data,
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            
            return {"items": [], "total": 0, "page": page, "limit": limit, "pages": 0}
            
        except Exception as e:
            logger.error(f"Error in get_cip_validated_info: {e}")
            return {"items": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    def get_cip_flushing_info(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ):
        """
        Get CIP flushing info with proper filtering, formatting, and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_cip")

            # Use existing SparkRepository for data retrieval
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=start_time,
                to_date=end_time
            )
            
            if result["success"] and result["spark_df"]:
                spark_df = result["spark_df"]
                
                # DIAGNOSE AVAILABLE COLUMNS
                available_columns = spark_df.columns
                print(f"[CIP_FLUSHING] Available columns: {available_columns}")
                
                # FLEXIBLE COLUMN MATCHING
                mode_column = None
                possible_mode_columns = ['Mode_Validated', 'mode_validated', 'Mode', 'mode', 'Status', 'status', 'Type', 'type']
                
                for col_name in possible_mode_columns:
                    if col_name in available_columns:
                        mode_column = col_name
                        print(f"[CIP_FLUSHING] Found mode column: {mode_column}")
                        break
                
                if not mode_column:
                    print(f"[CIP_FLUSHING] No suitable mode column found. Available: {available_columns}")
                    sample_data = spark_df.limit(5).collect()
                    
                    return {
                        "items": [],
                        "total": 0,
                        "page": page,
                        "limit": limit,
                        "pages": 0,
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "sample_data": [row.asDict() for row in sample_data[:2]] if sample_data else [],
                            "message": "No suitable mode validation column found"
                        }
                    }
                
                # Apply rack filtering FIRST
                filtered_df = self._filter_by_racks_spark(spark_df, racks)
                
                # Apply date filtering
                if "Start_Time" in available_columns and "End_Time" in available_columns:
                    filtered_df = self._filter_by_datetime_spark(
                        filtered_df, "Start_Time", "End_Time", start_time, end_time
                    )
                
                # Filter for "Flushing" records
                flushing_df = filtered_df.filter(filtered_df[mode_column] == "Flushing")
                total_count = flushing_df.count()
                
                # Apply pagination
                offset = (page - 1) * limit
                paginated_df = flushing_df.offset(offset).limit(limit)
                
                # Convert to result format
                data = self._format_flexible_result(paginated_df)
                
                total_pages = math.ceil(total_count / limit) if limit > 0 else 1
                
                return {
                    "items": data,
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            
            return {"items": [], "total": 0, "page": page, "limit": limit, "pages": 0}
            
        except Exception as e:
            logger.error(f"Error in get_cip_flushing_info: {e}")
            return {"items": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    def get_cip_summary(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Get CIP summary with proper formatting and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_cip_summary")
            
            # Use existing SparkRepository for consistent processing
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=start_time,
                to_date=end_time,
                limit=1000
            )
            
            if result["success"] and result["spark_df"]:
                spark_df = result["spark_df"]
                
                # DIAGNOSE AVAILABLE COLUMNS
                available_columns = spark_df.columns
                print(f"[CIP_SUMMARY] Available columns: {available_columns}")
                
                # Apply rack filtering FIRST
                filtered_df = self._filter_by_racks_spark(spark_df, racks)
                
                # FLEXIBLE COLUMN MATCHING
                column_mappings = {
                    "Train": ["Train", "train", "Train_ID", "Unit", "Rack"],
                    "Days_Since_Last_CIP": ["Days_Since_Last_CIP", "days_since_last_cip", "Days_Since_CIP", "DaysSinceCIP", "days_since"]
                }
                
                found_columns = {}
                for standard_name, possible_names in column_mappings.items():
                    for possible_name in possible_names:
                        if possible_name in available_columns:
                            found_columns[standard_name] = possible_name
                            print(f"[CIP_SUMMARY] Mapped {standard_name} -> {possible_name}")
                            break
                
                if not found_columns:
                    print(f"[CIP_SUMMARY] No required columns found. Available: {available_columns}")
                    sample_data = filtered_df.limit(3).collect()
                    return {
                        "diagnostic_info": {
                            "available_columns": available_columns,
                            "sample_data": [row.asDict() for row in sample_data[:2]] if sample_data else [],
                            "message": "No required columns found for CIP summary"
                        }
                    }
                
                return self._format_cip_summary_result_spark(filtered_df, found_columns)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in get_cip_summary: {e}")
            return {}
    
    def _format_cip_summary_result_spark(self, spark_df, found_columns) -> dict:
        """Format CIP summary results matching the original format with Train data sorted in ascending order"""
        try:
            if not spark_df:
                return {}
            
            train_col = found_columns.get("Train", "Train")
            days_col = found_columns.get("Days_Since_Last_CIP", "days_since")
            
            # Sort by Train column in ascending order before collecting results
            sorted_df = spark_df.orderBy(train_col)
            result_data = sorted_df.collect()
            
            train_data = []
            days_data = []
            
            for row in result_data:
                try:
                    train_data.append(getattr(row, train_col, None))
                    days_data.append(getattr(row, days_col, None))
                except Exception as row_error:
                    print(f"[CIP_SUMMARY] Row processing error: {row_error}")
                    continue
            
            return {
                "rackcipstatus": {
                    "G1": {
                        "x": [{"name": "Days Since Last CIP", "data": days_data}],
                        "y": [{"name": "Train", "data": train_data}]
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error formatting CIP summary result: {e}")
            return {}
    
    def get_membrane_info(
        self,
        site_name: str = None,
        user: dict = None,
        page: int = 1,
        limit: int = 25,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None,
        modes: Optional[List[str]] = None
    ):
        """
        Get membrane info with proper pagination, formatting, rack filtering, and mode filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            table_suffixes = ["_mode_maintenance", "_mode_cip"]
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_maintenance")
            
            print(f"Getting membrane info for {site_id}/{table_id} with racks filter: {racks}, modes filter: {modes}")
            
            merged_df = None
        
            for table_suffix in table_suffixes:
                table_id = self._build_table_id(site_name, table_suffix)
                print(f"Processing table: {site_id}/{table_id}")
                
                # Get data from current table
                result = self._get_data_using_existing_repos(
                    site_id=site_id,
                    table_id=table_id,
                    operation="query",
                    from_date=start_time,
                    to_date=end_time
                )
                
                if result["success"] and result["spark_df"]:
                    current_df = result["spark_df"]
                    
                    # Add source table information for debugging/tracking
                    current_df = current_df.withColumn("source_table", F.lit(table_suffix))
                    
                    if merged_df is None:
                        merged_df = current_df
                    else:
                        # Union the DataFrames - this requires same schema
                        try:
                            merged_df = merged_df.union(current_df)
                            print(f"Successfully merged data from {table_id}")
                        except Exception as union_error:
                            print(f"Warning: Failed to union {table_id}: {union_error}")
                            merged_df = self._union_with_schema_alignment(merged_df, current_df, table_suffix)
                else:
                    print(f"No data or failed to get data from table: {table_id}")
            
            if merged_df is None:
                print("No data found in any of the specified tables")
                return {"items": [], "total": 0, "page": page, "limit": limit, "pages": 0}
            
            print(f"Total rows after merging all tables: {merged_df.count()}")
            
            # Apply filters to merged dataset
            filtered_df = merged_df
            
            # Apply rack filtering FIRST
            filtered_df = self._filter_by_racks_spark(filtered_df, racks)
            
            # Apply mode filtering SECOND  
            filtered_df = self._filter_by_mode_spark(filtered_df, modes)
            
            # Apply date filtering THIRD
            if "Start_Time" in merged_df.columns and "End_Time" in merged_df.columns:
                filtered_df = self._filter_by_datetime_spark(
                    filtered_df, "Start_Time", "End_Time", start_time, end_time
                )
            
            total_count = filtered_df.count()
            print(f"Total rows after filtering: {total_count}")
            
            # Apply pagination
            offset = (page - 1) * limit
            paginated_df = filtered_df.offset(offset).limit(limit)
            
            # Format result with all available columns
            data = self._format_flexible_result(paginated_df)
            
            total_pages = math.ceil(total_count / limit) if limit > 0 else 1
            
            return {
                "items": data,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "source_tables": table_suffixes,  # Include info about source tables
                "merged_from": len(table_suffixes)
            }
            
        except Exception as e:
            logger.error(f"Error in get_membrane_info_multi_tables: {e}")
            return {"items": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    def _union_with_schema_alignment(self, df1, df2, table_suffix):
        """
        Helper method to union DataFrames with potentially different schemas.
        Aligns schemas by adding missing columns with null values.
        """
        try:
            print(f"Attempting schema alignment for table: {table_suffix}")
            
            # Get column lists
            cols1 = set(df1.columns)
            cols2 = set(df2.columns)
            
            print(f"DF1 columns ({len(cols1)}): {sorted(cols1)}")
            print(f"DF2 columns ({len(cols2)}): {sorted(cols2)}")
            
            # Find missing columns
            missing_in_df1 = cols2 - cols1
            missing_in_df2 = cols1 - cols2
            
            # Add missing columns to df1
            for col in missing_in_df1:
                df1 = df1.withColumn(col, F.lit(None))
                print(f"Added missing column '{col}' to df1")
            
            # Add missing columns to df2  
            for col in missing_in_df2:
                df2 = df2.withColumn(col, F.lit(None))
                print(f"Added missing column '{col}' to df2")
            
            # Ensure column order is the same
            all_columns = sorted(cols1.union(cols2))
            df1_aligned = df1.select(*all_columns)
            df2_aligned = df2.select(*all_columns)
            
            # Union the aligned DataFrames
            result = df1_aligned.union(df2_aligned)
            print(f"Successfully aligned and merged schemas")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in schema alignment: {e}")
            print(f"Schema alignment failed, returning original df1: {e}")
            return df1
    
    def _format_flexible_result(self, spark_df):
        """
        Universal flexible formatting method.
        Works with any DataFrame structure and detects numeric vs text columns.
        Train data is sorted in ascending order.
        """
        try:
            if not spark_df:
                return {}
            
            # Check if there's a Train column and sort by it if found
            train_columns = ['Train', 'train', 'Train_ID', 'train_id', 'Unit', 'unit', 'Rack', 'rack']
            sort_column = None
            
            for col in spark_df.columns:
                if col in train_columns:
                    sort_column = col
                    break
            
            # Sort by Train column if found, otherwise keep original order
            if sort_column:
                sorted_df = spark_df.orderBy(sort_column)
                result_data = sorted_df.collect()
            else:
                result_data = spark_df.collect()
            
            if not result_data:
                return {}
            
            formatted = {}
            
            # Determine column types by examining data
            for col in spark_df.columns:
                col_data = []
                col_lower = col.lower()
                is_datetime_column = (
                    col_lower in ['datetime', 'timestamp', 'start_time', 'end_time', 'created_on', 'updated_on'] or
                    'time' in col_lower or 
                    'date' in col_lower
                )
                
                for row in result_data:
                    value = getattr(row, col, None)
                    
                    # Handle different data types
                    if value is None:
                        col_data.append(None)
                    elif isinstance(value, datetime):
                        # Format datetime values without timezone
                        col_data.append(DateTimeParser.format_datetime_without_timezone(value))
                    elif is_datetime_column and isinstance(value, str):
                        # Try to parse and format datetime strings for datetime columns
                        try:
                            parsed_dt = DateTimeParser.parse_datetime(value)
                            if parsed_dt:
                                col_data.append(DateTimeParser.format_datetime_without_timezone(parsed_dt))
                            else:
                                col_data.append(str(value))
                        except:
                            col_data.append(str(value))
                    elif col_lower in ['train', 'train_id', 'unit', 'rack']:
                        # Train identifiers should be integers (actual int, not string)
                        if isinstance(value, (int, float)):
                            col_data.append(int(float(value)))
                        else:
                            # Try to convert to int, fallback to string
                            try:
                                col_data.append(int(float(str(value))))
                            except (ValueError, TypeError):
                                col_data.append(str(value))
                    elif isinstance(value, (int, float)):
                        # Numeric data - format to 2 decimal places as string
                        col_data.append(f"{float(value):.2f}")
                    else:
                        # Other data - convert to string
                        col_data.append(str(value))
                
                # Standardize train column name
                if col.lower() in ['train', 'train_id', 'unit', 'rack']:
                    formatted["Train"] = {
                        "name": "Train",
                        "data": col_data
                    }
                else:
                    formatted[col] = {
                        "name": col,
                        "data": col_data
                    }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error in flexible formatting: {e}")
            return {}
    
    def get_columns_metadata(
        self,
        site_name: str = None,
        user: dict = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False
    ):
        """
        Get column metadata for membrane maintenance data with chart groupings.
        Returns data structured for G1, G2, G3 charts with specific column sets.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_cip")
            
            print(f"Getting columns metadata for {site_id}/{table_id}")
            
            # Define column groups for different charts
            chart_columns = {
                "G1": [  # Perm Flow Norm Chart
                    "Train",
                    "AVG_Perm_Flow_Normalized_Pre",
                    "AVG_Perm_Flow_Normalized_Post",
                    "Diff_Norm_Perm_Flow_%"
                ],
                "G2": [  # Dp Flow Norm Chart
                    "Train",
                    "AVG_DP_Normalized_BAR_Pre",
                    "AVG_DP_Normalized_BAR_Post",
                    "Diff_DP_%"
                ],
                "G3": [  # Salt Passage Norm Chart
                    "Train",
                    "AVG_Salt_Passage_Normalized_Pre",
                    "AVG_Salt_Passage_Normalized_Post",
                    "Diff_Norm_Salt_Passage_%"
                ]
            }
            
            # Get all unique columns needed
            all_columns = set()
            for group_cols in chart_columns.values():
                all_columns.update(group_cols)
            
            # Get data using existing repository method
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                from_date=from_date,
                to_date=to_date,
                columns=list(all_columns)
            )
            
            if not result["success"] or not result["spark_df"]:
                return {
                    "charts": {},
                    "date_filter": {
                        "from_date": from_date,
                        "to_date": to_date,
                        "rows_in_range": 0,
                        "sample_size": 0,
                        "processing_time_seconds": 0
                    },
                    "method_used": result.get("method_used", "failed"),
                    "performance": {
                        "processing_time_seconds": 0,
                        "rows_processed": 0,
                        "columns_found": 0
                    }
                }
            
            spark_df = result["spark_df"]
            start_time = datetime.now()
            
            # Build response structure for each chart group
            charts_data = {}
            
            for chart_id, columns in chart_columns.items():
                chart_data = self._build_chart_metadata_spark(spark_df, columns, exclude_null, include_samples)
                if chart_data:
                    charts_data[chart_id] = chart_data
            
            processing_time = (datetime.now() - start_time).total_seconds()
            total_rows = result.get("row_count", 0)
            
            return {
                "charts": charts_data,
                "date_filter": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "rows_in_range": total_rows,
                    "sample_size": total_rows,
                    "processing_time_seconds": processing_time
                },
                "method_used": result.get("method_used", "spark_repository"),
                "performance": {
                    "processing_time_seconds": processing_time,
                    "rows_processed": total_rows,
                    "columns_found": len(all_columns)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_columns_metadata: {e}")
            return {
                "charts": {},
                "date_filter": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "rows_in_range": 0,
                    "sample_size": 0,
                    "processing_time_seconds": 0
                },
                "method_used": "error",
                "performance": {
                    "processing_time_seconds": 0,
                    "rows_processed": 0,
                    "columns_found": 0
                }
            }

    def _build_chart_metadata_spark(self, spark_df, columns, exclude_null=True, include_samples=True):
        """
        Build chart metadata structure from Spark DataFrame for specific columns.
        """
        try:
            from pyspark.sql import functions as F
            
            # Check which columns actually exist in the DataFrame
            available_columns = spark_df.columns
            existing_columns = [col for col in columns if col in available_columns]
            
            if not existing_columns:
                return None
            
            # Filter DataFrame to only include existing columns
            filtered_df = spark_df.select(*existing_columns)
            
            # Collect sample data
            if include_samples:
                sample_data = filtered_df.collect()
            else:
                sample_data = []
            
            # Find Train column (x-axis)
            train_columns = ["Train", "train", "Train_ID", "Unit", "Rack"]
            train_col = None
            for col in train_columns:
                if col in existing_columns:
                    train_col = col
                    break
            
            chart_structure = {
                "x": [],
                "y": []
            }
            
            # Build x-axis data (Train column)
            if train_col and include_samples:
                train_values = []
                for row in sample_data:
                    val = getattr(row, train_col, None)
                    if val is not None:
                        train_values.append(str(val))
                    elif not exclude_null:
                        train_values.append(None)
                
                # Get unique sorted train values
                unique_trains = sorted(list(set([t for t in train_values if t is not None])), 
                                    key=lambda x: int(x) if x and x.isdigit() else 999)
                
                chart_structure["x"].append({
                    "name": train_col,
                    "type": "int64",
                    "nullable": True,
                    "dataSource": unique_trains
                })
            
            # Build y-axis data (other columns)
            for col in existing_columns:
                if col == train_col:
                    continue  # Skip train column as it's in x-axis
                
                if include_samples:
                    col_values = []
                    for row in sample_data:
                        val = getattr(row, col, None)
                        if val is not None:
                            if isinstance(val, (int, float)):
                                col_values.append(str(val))
                            else:
                                col_values.append(str(val))
                        elif not exclude_null:
                            col_values.append(None)
                    
                    # Determine column type
                    sample_val = next((v for v in col_values if v is not None), None)
                    if sample_val and sample_val.replace('.', '').replace('-', '').isdigit():
                        col_type = "double"
                    else:
                        col_type = "string"
                    
                    chart_structure["y"].append({
                        "name": col,
                        "type": col_type,
                        "nullable": True,
                        "dataSource": col_values[:20] if len(col_values) > 20 else col_values  # Limit sample size
                    })
                else:
                    # Just metadata without samples
                    chart_structure["y"].append({
                        "name": col,
                        "type": "unknown",
                        "nullable": True,
                        "dataSource": []
                    })
            
            return chart_structure
            
        except Exception as e:
            logger.error(f"Error building chart metadata: {e}")
            return None

    def get_racks_data(
        self,
        site_name: str = None,
        user: dict = None
    ):
        """
        Get unique rack/train data for a site.
        Returns unique Train column values.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)
            
            site_id = self._map_site_to_site_id(site_name)
            table_id = self._build_table_id(site_name, "_mode_racks_operation")
            
            print(f"Getting racks data for {site_id}/{table_id}")
            
            # Get data using existing repository method - only need Train column
            result = self._get_data_using_existing_repos(
                site_id=site_id,
                table_id=table_id,
                operation="query",
                columns=["Train"]  # Only fetch Train column for efficiency
            )
            
            if not result["success"] or not result["spark_df"]:
                print(f"Failed to get data: {result.get('error', 'Unknown error')}")
                return {
                    "racks": [],
                    "count": 0
                }
            
            spark_df = result["spark_df"]
            
            # Find the train column using flexible matching
            available_columns = spark_df.columns
            train_column = None
            train_possible = ["Train", "train", "Train_ID", "train_id", "Unit", "unit", "Rack", "rack"]
            
            for col_name in train_possible:
                if col_name in available_columns:
                    train_column = col_name
                    print(f"Found train column: {train_column}")
                    break
            
            if not train_column:
                print(f"No train column found. Available: {available_columns}")
                return {
                    "racks": [],
                    "count": 0
                }
            
            # Get unique train values using Spark operations
            
            unique_trains_df = spark_df.select(train_column).distinct().filter(
                F.col(train_column).isNotNull()
            ).orderBy(F.col(train_column).asc())
            
            # Collect the results
            unique_trains_data = unique_trains_df.collect()
            
            # Extract train values and convert to integers
            racks_list = []
            for row in unique_trains_data:
                train_val = getattr(row, train_column, None)
                if train_val is not None:
                    try:
                        # Convert to integer for proper sorting
                        racks_list.append(int(float(train_val)))
                    except (ValueError, TypeError):
                        # If conversion fails, use string representation
                        racks_list.append(str(train_val))
            
            # Sort the list (integers will sort numerically)
            racks_list.sort()
            
            return {
                "racks": racks_list,
                "count": len(racks_list)
            }
            
        except Exception as e:
            logger.error(f"Error in get_racks_data: {e}")
            return {
                "racks": [],
                "count": 0
            }