from typing import Optional, Dict, List
from datetime import datetime
from infrastructure.orm.repositories.sparkSqlRepository import SparkSqlRepository
from infrastructure.orm.repositories.pyarrowParallelProcessor import PyArrowParallelProcessor
from infrastructure.utils.queryOptimizer import QueryOptimizer
from infrastructure.utils.dateOptimizer import DateOptimizer
from infrastructure.utils.datetime_utils import DateTimeParser
from config.spark_connection import get_spark_connection

class ColumnMetadataService:
    """
    Optimized column metadata service with performance enhancements.
    Handles efficient column information retrieval with minimal data processing.
    """
    
    def __init__(self):
        self.spark = get_spark_connection()
        self.spark_sql_repo = SparkSqlRepository(self.spark)
        self.pyarrow_processor = PyArrowParallelProcessor(self.spark)
        self.query_optimizer = QueryOptimizer()
        self.date_optimizer = DateOptimizer()
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"

    def _get_file_path(self, site_id: str = None, table_id: str = None, coordinates: bool = False) -> str:
        """
        Get the appropriate file path based on coordinates parameter.
        
        Args:
            site_id: Site identifier (required for coordinates=True)
            table_id: Table identifier (required for coordinates=True)
            coordinates: If True, use coordinates path; if False, use gold path
            
        Returns:
            Constructed file path
        """
        if coordinates:
            if not site_id or not table_id:
                raise ValueError("site_id and table_id are required when coordinates=True")
            return f"{self.base_file_path}/{site_id}/{table_id}"
        else:
            return f"{self.base_file_path}/gold"
    
    def get_optimized_column_metadata(
        self,
        table_id: str,
        site_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime",
        sample_size: int = 50,
        coordinates: bool = False
    ) -> Dict:
        """
        Get column metadata using the most efficient method available.
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[COLUMN_METADATA] Starting optimized metadata retrieval for {site_id}/{table_id} from {data_type} data")
            
            # Validate inputs
            if not self._validate_inputs(from_date, to_date, site_id, table_id):
                raise ValueError("Invalid input parameters")
            
            # Optimize date range for performance
            optimized_from, optimized_to, date_metadata = self.date_optimizer.get_performance_optimized_range(
                from_date=from_date,
                to_date=to_date
            )
            
            print(f"[COLUMN_METADATA] Date optimization: {date_metadata}")
            
            # Get query optimization hints based on date range
            query_hints = self.date_optimizer.get_query_optimization_hints(optimized_from, optimized_to)
            print(f"[COLUMN_METADATA] Query hints: {query_hints}")
            
            # Use optimized dates for performance assessment
            complexity = self.query_optimizer.estimate_query_complexity(
                columns=None,  # Getting all columns
                from_date=optimized_from,
                to_date=optimized_to,
                limit=sample_size
            )
            
            # Override method selection based on date optimization hints
            if query_hints.get("recommended_method"):
                complexity["recommended_method"] = query_hints["recommended_method"]
            
            print(f"[COLUMN_METADATA] Query complexity: {complexity['estimated_time']}")
            
            # Try Direct SQL first (fastest method)
            try:
                result = self._get_metadata_with_direct_sql(
                    site_id, table_id, optimized_from, optimized_to, date_column, sample_size, coordinates
                )
                result["method_used"] = f"direct_sql_{data_type}"
                result["performance"] = complexity
                result["date_optimization"] = date_metadata
                result["query_hints"] = query_hints
                result["data_source"] = data_type
                return result
                
            except Exception as direct_sql_error:
                print(f"[COLUMN_METADATA] Direct SQL failed: {direct_sql_error}")
                
                # Fallback to SparkSQL
                try:
                    result = self._get_metadata_with_sparksql(
                        site_id, table_id, optimized_from, optimized_to, date_column, sample_size, coordinates
                    )
                    result["method_used"] = f"sparksql_{data_type}"
                    result["performance"] = complexity
                    result["date_optimization"] = date_metadata
                    result["query_hints"] = query_hints
                    result["data_source"] = data_type
                    return result
                    
                except Exception as sparksql_error:
                    print(f"[COLUMN_METADATA] SparkSQL failed: {sparksql_error}")
                    
                    # Fallback to PyArrow parallel processing
                    try:
                        result = self._get_metadata_with_pyarrow(
                            site_id, table_id, optimized_from, optimized_to, date_column, sample_size, coordinates
                        )
                        result["method_used"] = f"pyarrow_parallel_{data_type}"
                        result["performance"] = complexity
                        result["date_optimization"] = date_metadata
                        result["query_hints"] = query_hints
                        result["data_source"] = data_type
                        return result
                        
                    except Exception as pyarrow_error:
                        print(f"[COLUMN_METADATA] PyArrow fallback failed: {pyarrow_error}")
                        
                        # Fast production response - no data found
                        return {
                            "columns": [],
                            "date_filter": {
                                "from_date": optimized_from,
                                "to_date": optimized_to,
                                "date_column": "Datetime",
                                "rows_in_range": 0,
                                "message": f"No data found in requested date range for {data_type} data"
                            },
                            "method_used": f"production_fallback_{data_type}",
                            "performance": complexity,
                            "date_optimization": date_metadata,
                            "query_hints": query_hints,
                            "data_source": data_type
                        }
        
        except Exception as e:
            print(f"[COLUMN_METADATA] Error in optimized metadata retrieval: {e}")
            raise e
    
    def _get_metadata_with_direct_sql(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        date_column: str,
        sample_size: int,
        coordinates: bool = False
    ) -> Dict:
        """
        Get metadata using direct SQL optimization (fastest method).
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[COLUMN_METADATA] Using direct SQL method for {data_type} data")
            
            result = self.spark_sql_repo.get_metadata_with_direct_sql(
                siteName=site_id,
                tableName=table_id,
                from_date=from_date,
                to_date=to_date,
                date_column=date_column,
                sample_size=sample_size,
                coordinates=coordinates
            )
            
            return result
            
        except Exception as e:
            raise e

    def _validate_inputs(
        self, 
        from_date: Optional[str], 
        to_date: Optional[str], 
        site_id: str, 
        table_id: str
    ) -> bool:
        """
        Validate input parameters for security and correctness.
        """
        try:
            # Validate date formats
            if from_date and not self.query_optimizer.validate_date_format(from_date):
                return False
            if to_date and not self.query_optimizer.validate_date_format(to_date):
                return False
            
            # Check for path traversal attempts
            if '..' in site_id or '..' in table_id or '/' in site_id or '/' in table_id:
                return False
            if '\\' in site_id or '\\' in table_id:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _get_metadata_with_sparksql(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        date_column: str,
        sample_size: int,
        coordinates: bool = False
    ) -> Dict:
        """
        Get metadata using optimized SparkSQL approach.
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        view_name = None
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[COLUMN_METADATA] Using SparkSQL method for {data_type} data")
            
            # Create optimized temporary view
            view_name = self.spark_sql_repo.create_optimized_temp_view(
                siteName=site_id,
                tableName=table_id,
                coordinates=coordinates
            )
            
            # Get table metadata efficiently
            metadata = self.spark_sql_repo.get_table_metadata(view_name)
            
            # Get sample data with date filtering
            sample_data = self.spark_sql_repo.get_sample_data(
                view_name=view_name,
                columns=None,
                sample_size=sample_size,
                from_date=from_date,
                to_date=to_date,
                date_column=date_column
            )
            
            # Build column information with samples
            columns = self._build_column_info(metadata, sample_data, table_id)
            
            # Get row count estimate (optional for performance)
            try:
                row_count = self.spark_sql_repo.execute_count_query(
                    view_name=view_name,
                    from_date=from_date,
                    to_date=to_date,
                    date_column=date_column
                )
            except:
                row_count = len(sample_data) if sample_data else 0
            
            return {
                "columns": columns,
                "date_filter": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "date_column": date_column,
                    "rows_in_range": row_count,
                    "sample_size": len(sample_data)
                }
            }
            
        except Exception as e:
            raise e
        finally:
            # Cleanup
            if view_name:
                self.spark_sql_repo.cleanup_temp_view(view_name)
    
    def _get_metadata_with_pyarrow(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        date_column: str,
        sample_size: int,
        coordinates: bool = False
    ) -> Dict:
        """
        Get metadata using PyArrow parallel processing fallback.
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[COLUMN_METADATA] Using PyArrow parallel method for {data_type} data")
            
            # Process with PyArrow (limited files for metadata)
            df = self.pyarrow_processor.process_parquet_files_parallel(
                siteName=site_id,
                tableName=table_id,
                from_date=from_date,
                to_date=to_date,
                columns=None,  # Get all columns for metadata
                max_files=3,   # Limit files for faster metadata retrieval
                coordinates=coordinates
            )
            
            # Check if DataFrame has data
            sample_rows = df.take(min(sample_size, 100))
            if not sample_rows:
                raise Exception(f"No data found for {site_id}/{table_id} in the given range from {data_type} data")
            
            # Get schema and sample data
            schema = df.schema
            
            # Build column metadata
            columns = []
            for field in schema.fields:
                name = field.name
                sample_vals = []
                
                # Extract sample values from collected rows
                for row in sample_rows[:10]:  # Use only first 10 rows for samples
                    try:
                        value = row[name]
                        if value is not None:
                            if isinstance(value, datetime):
                                sample_vals.append(DateTimeParser.format_datetime_without_timezone(value))
                            elif isinstance(value, (int, float, str, bool)):
                                sample_vals.append(str(value))
                            else:
                                sample_vals.append(str(value))
                        if len(sample_vals) >= 5:  # Limit sample values
                            break
                    except:
                        continue

                columns.append({
                    "name": name,
                    "dataSource": sample_vals,
                    "type": str(field.dataType),
                    "nullable": field.nullable,
                    "table": table_id,
                })
            
            # Estimate row count without expensive operations
            estimated_rows = len(sample_rows) if len(sample_rows) < sample_size else f"{sample_size}+"
            
            return {
                "columns": columns,
                "date_filter": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "date_column": date_column,
                    "estimated_rows": estimated_rows,
                    "sample_size": len(sample_rows)
                }
            }
            
        except Exception as e:
            raise e
    
    def _build_column_info(self, metadata: List[Dict], sample_data: List, table_id: str) -> List[Dict]:
        """
        Build comprehensive column information from metadata and sample data.
        """
        try:
            columns = []
            
            for col_meta in metadata:
                col_name = col_meta["name"]
                
                # Extract sample values for this column
                sample_values = []
                for sample_row in sample_data[:10]:  # Limit to first 10 rows
                    try:
                        if hasattr(sample_row, col_name):
                            value = getattr(sample_row, col_name)
                        elif isinstance(sample_row, dict) and col_name in sample_row:
                            value = sample_row[col_name]
                        else:
                            value = sample_row[col_name] if col_name in sample_row else None
                        
                        if value is not None:
                            if isinstance(value, datetime):
                                sample_values.append(value.isoformat())
                            elif isinstance(value, (int, float, str, bool)):
                                sample_values.append(str(value))
                            else:
                                sample_values.append(str(value))
                        
                        if len(sample_values) >= 5:
                            break
                    except Exception:
                        continue
                
                columns.append({
                    "name": col_name,
                    "type": col_meta.get("type", "unknown"),
                    "nullable": col_meta.get("nullable", True),
                    "dataSource": sample_values,
                    "table": table_id
                })
            
            return columns
            
        except Exception as e:
            print(f"[COLUMN_METADATA] Error building column info: {e}")
            return []
    
    def get_performance_insights(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        coordinates: bool = False
    ) -> Dict:
        """
        Get performance insights and recommendations for the query.
        
        Args:
            coordinates: If True, analyze coordinates data; if False, analyze gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[COLUMN_METADATA] Getting performance insights for {site_id}/{table_id} from {data_type} data")
            
            # Get file metadata
            file_metadata = self.pyarrow_processor.get_file_metadata(site_id, table_id, coordinates=coordinates)
            
            # Get query recommendations
            recommendations = self.query_optimizer.get_performance_recommendations(
                siteName=site_id,
                tableName=table_id,
                from_date=from_date,
                to_date=to_date,
                columns=None
            )
            
            # Estimate query complexity
            complexity = self.query_optimizer.estimate_query_complexity(
                columns=None,
                from_date=from_date,
                to_date=to_date,
                limit=None
            )
            
            # Add coordinates-specific recommendations
            if coordinates:
                recommendations.append("Coordinates data typically has smaller file sizes - consider direct Spark for better performance")
                recommendations.append("Coordinates data may have different partitioning - adjust query strategies accordingly")
            
            return {
                "file_metadata": file_metadata,
                "recommendations": recommendations,
                "complexity_assessment": complexity,
                "optimal_method": "sparksql" if complexity["score"] < 40 else "pyarrow_parallel",
                "data_source": data_type
            }
            
        except Exception as e:
            print(f"[COLUMN_METADATA] Error getting performance insights: {e}")
            return {
                "error": str(e),
                "recommendations": ["Use date filtering for better performance"]
            }
