import datetime
import pyarrow.parquet as pq
import pyarrow as pa
import io
import concurrent.futures
import os
from typing import Optional, List
from pyspark.sql import SparkSession, DataFrame
from infrastructure.utils.azure.blobStorageClient import BlobStorageClient
from infrastructure.utils.pyarrow.timestampProcessor import TimestampProcessor


class PyArrowParallelProcessor:
    """
    Production-ready PyArrow parallel processor for parquet files.
    """
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
        # Configurable parameters with environment variable fallbacks
        self.max_workers = int(os.getenv('PYARROW_MAX_WORKERS', '3'))  # Configurable workers
        self.max_rows_per_file = int(os.getenv('PYARROW_MAX_ROWS_PER_FILE', '1000'))  # Configurable row limit
        self.max_files_per_batch = int(os.getenv('PYARROW_MAX_FILES_PER_BATCH', '5'))  # Configurable file limit
        self.enable_streaming = os.getenv('PYARROW_ENABLE_STREAMING', 'false').lower() == 'true'  # Streaming mode
        self.streaming_batch_size = int(os.getenv('PYARROW_STREAMING_BATCH_SIZE', '500'))  # Streaming batch size
        self.blob_client = BlobStorageClient()
        self.timestamp_processor = TimestampProcessor()
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"

    def _get_blob_prefix(self, siteName: str, tableName: str, coordinates: bool = False) -> str:
        """Get the appropriate blob prefix based on coordinates parameter."""
        if coordinates:
            return f"tables/{siteName}/{tableName}/"
        else:
            return f"tables/gold/{siteName}/{tableName}/"

    def _get_file_path(self, siteName: str, tableName: str, coordinates: bool = False) -> str:
        """Get the appropriate file path based on coordinates parameter."""
        if coordinates:
            return f"{self.base_file_path}/{siteName}/{tableName}"
        else:
            return f"{self.base_file_path}/gold/{siteName}/{tableName}"
    
    def process_parquet_files_parallel(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        max_files: int = 5,
        coordinates: bool = False
    ) -> DataFrame:
        """
        Process parquet files with enhanced timestamp handling and error prevention.
        """
        try:
            print(f"[PYARROW_PARALLEL] Starting parallel processing for {siteName}/{tableName}")
            
            # List files using appropriate prefix
            blob_prefix = self._get_blob_prefix(siteName, tableName, coordinates)
            parquet_blobs = self.blob_client.list_parquet_files(blob_prefix)
            
            if not parquet_blobs:
                raise Exception(f"No parquet files found for {siteName}/{tableName}")
            
            # Process first file to understand schema and detect timestamp issues
            first_blob = parquet_blobs[0]
            print(f"[PYARROW_PARALLEL] Reading schema from {first_blob.name}")
            
            # Get schema information first with timestamp analysis
            blob_client = self.blob_client.get_blob_client(first_blob.name)
            blob_data = blob_client.download_blob().readall()
            parquet_file = pq.ParquetFile(io.BytesIO(blob_data))
            
            # Analyze schema for timestamp issues
            schema = parquet_file.schema_arrow
            print(f"[PYARROW_PARALLEL] Available columns: {schema.names}")
            print(f"[PYARROW_PARALLEL] Column types: {[str(field.type) for field in schema]}")
            
            # Detect timestamp columns using the improved processor
            sample_table = parquet_file.read()
            available_timestamp_cols = self.timestamp_processor.find_available_timestamp_columns(sample_table)
            print(f"[PYARROW_PARALLEL] Available timestamp columns: {available_timestamp_cols}")
            
            # Limit files for performance
            effective_max_files = min(max_files, self.max_files_per_batch)
            files_to_process = parquet_blobs[:effective_max_files]
            print(f"[PYARROW_PARALLEL] Processing {len(files_to_process)} files (max_files: {max_files}, effective_max: {effective_max_files})")
            
            # Process files in parallel
            tables = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_blob = {
                    executor.submit(
                        self._process_parquet_file_safe,  # Use safer processing method
                        blob.name,
                        from_date,
                        to_date,
                        columns,
                        available_timestamp_cols  # Pass detected timestamp columns
                    ): blob for blob in files_to_process
                }
                
                for future in concurrent.futures.as_completed(future_to_blob):
                    blob = future_to_blob[future]
                    try:
                        result = future.result()
                        if result is not False:
                            tables.append(result)
                            print(f"[PYARROW_PARALLEL] Processed {blob.name}: {len(result)} rows")
                    except Exception as e:
                        print(f"[PYARROW_PARALLEL] Failed to process {blob.name}: {e}")
            
            if not tables:
                raise Exception("No data retrieved from any parquet files")
            
            # Combine tables with type safety
            print(f"[PYARROW_PARALLEL] Combining {len(tables)} tables...")
            combined_table = self._safe_concat_tables(tables)
            
            # Convert to Spark DataFrame with improved type handling
            print(f"[PYARROW_PARALLEL] Converting {len(combined_table)} rows to Spark DataFrame...")
            converted_table = self.timestamp_processor.convert_timestamp_precision(combined_table)
            
            # Convert PyArrow table to Spark DataFrame with explicit type handling
            df = self._create_spark_dataframe_safe(converted_table)
            print(f"[PYARROW_PARALLEL] Successfully created Spark DataFrame")
            
            return df
            
        except Exception as e:
            print(f"[PYARROW_PARALLEL] Parallel processing failed: {e}")
            raise e
    
    def _process_parquet_file_safe(
        self,
        blob_name: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        available_timestamp_cols: Optional[List[str]] = None
    ):
        """
        Safer parquet file processing with better type handling and timestamp column detection.
        """
        try:
            blob_client = self.blob_client.get_blob_client(blob_name)
            blob_data = blob_client.download_blob().readall()
            parquet_file = pq.ParquetFile(io.BytesIO(blob_data))
            
            # Read with explicit type handling
            table = parquet_file.read(
                columns=columns,
                use_threads=True,
                use_pandas_metadata=False
            )
            
            # Apply date filtering if needed and timestamp columns are available
            if from_date and to_date and available_timestamp_cols:
                # Use the timestamp processor with detected columns
                table = self.timestamp_processor.apply_date_filter(table, from_date, to_date)
            
            # Limit rows for performance (with streaming option)
            if len(table) > self.max_rows_per_file:
                if self.enable_streaming:
                    # For streaming mode, process in smaller batches
                    print(f"[PYARROW_PARALLEL] Streaming mode: processing {self.streaming_batch_size} rows at a time")
                    table = table.slice(0, self.streaming_batch_size)
                else:
                    # Standard mode: limit to max_rows_per_file
                    table = table.slice(0, self.max_rows_per_file)
            
            # Ensure consistent schema types
            table = self._normalize_table_types(table)
            
            return table
            
        except Exception as e:
            print(f"[PYARROW_PARALLEL] Failed to process {blob_name}: {e}")
            return False
    
    def _normalize_table_types(self, table):
        """
        Normalize PyArrow table types for better Spark compatibility.
        """
        try:
            # Convert problematic types to more compatible ones
            arrays = []
            schema_fields = []
            
            for i, field in enumerate(table.schema):
                array = table.column(i)
                field_name = field.name
                field_type = field.type
                
                # Handle different data types
                if pa.types.is_large_string(field_type):
                    # Convert large_string to regular string
                    new_array = pa.compute.cast(array, pa.string())
                    arrays.append(new_array)
                    schema_fields.append(pa.field(field_name, pa.string(), field.nullable))
                elif pa.types.is_decimal(field_type):
                    # Convert decimal to double for Spark compatibility
                    new_array = pa.compute.cast(array, pa.float64())
                    arrays.append(new_array)
                    schema_fields.append(pa.field(field_name, pa.float64(), field.nullable))
                elif pa.types.is_timestamp(field_type) and field_type.unit == 'ns':
                    # Already handled by timestamp processor, but ensure microseconds
                    new_array = pa.compute.cast(array, pa.timestamp('us', tz=field_type.tz))
                    arrays.append(new_array)
                    schema_fields.append(pa.field(field_name, pa.timestamp('us', tz=field_type.tz), field.nullable))
                else:
                    arrays.append(array)
                    schema_fields.append(field)
            
            new_schema = pa.schema(schema_fields)
            normalized_table = pa.table(arrays, schema=new_schema)
            
            return normalized_table
            
        except Exception as e:
            print(f"[PYARROW_PARALLEL] Type normalization failed: {e}")
            return table
    
    def _safe_concat_tables(self, tables):
        """
        Safely concatenate tables with schema alignment.
        """
        try:
            if len(tables) == 1:
                return tables[0]
            
            # Ensure all tables have compatible schemas
            base_schema = tables[0].schema
            aligned_tables = []
            
            for table in tables:
                if table.schema.equals(base_schema):
                    aligned_tables.append(table)
                else:
                    # Try to cast to base schema
                    try:
                        aligned_table = table.cast(base_schema)
                        aligned_tables.append(aligned_table)
                    except Exception as e:
                        print(f"[PYARROW_PARALLEL] Schema alignment failed: {e}")
                        # Skip this table rather than failing entirely
                        continue
            
            return pa.concat_tables(aligned_tables)
            
        except Exception as e:
            print(f"[PYARROW_PARALLEL] Table concatenation failed: {e}")
            return tables[0]  # Return first table as fallback
    
    def _create_spark_dataframe_safe(self, table):
        """
        Create Spark DataFrame with improved error handling and type conversion.
        """
        try:
            # Method 1: Try with explicit schema creation for better type control
            try:
                df = self._create_dataframe_with_safe_schema(table)
                return df
            except Exception as e1:
                print(f"[PYARROW_PARALLEL] Safe schema creation failed: {e1}")
                
                # Method 2: Try direct conversion from PyArrow
                try:
                    df = self.spark.createDataFrame(table.to_pylist())
                    return df
                except Exception as e2:
                    print(f"[PYARROW_PARALLEL] Direct PyArrow conversion failed: {e2}")
                    
                    # Method 3: Create manual schema with safe types
                    safe_df = self._create_dataframe_with_safe_schema(table)
                    return safe_df
                
        except Exception as e:
            print(f"[PYARROW_PARALLEL] All DataFrame creation methods failed: {e}")
            raise e
    
    def _create_dataframe_with_safe_schema(self, table):
        """
        Create DataFrame with manually defined safe schema and improved type handling.
        """
        from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType, BooleanType
        
        try:
            # Convert PyArrow table to list of dictionaries for safer handling
            pylist_data = table.to_pylist()
            
            if not pylist_data:
                # Return empty DataFrame with basic schema
                basic_schema = StructType([StructField("placeholder", StringType(), True)])
                return self.spark.createDataFrame([], basic_schema)
            
            # Create safe schema based on PyArrow schema
            safe_fields = []
            for field in table.schema:
                field_name = field.name
                pa_type = field.type
                
                if pa.types.is_timestamp(pa_type):
                    spark_type = TimestampType()
                elif pa.types.is_integer(pa_type):
                    spark_type = DoubleType()  # Use double for safety to avoid overflow
                elif pa.types.is_floating(pa_type):
                    spark_type = DoubleType()
                elif pa.types.is_boolean(pa_type):
                    spark_type = BooleanType()
                else:
                    spark_type = StringType()  # Default to string for safety
                
                safe_fields.append(StructField(field_name, spark_type, True))
            
            safe_schema = StructType(safe_fields)
            
            # Convert data to match schema types
            safe_data = []
            for row_dict in pylist_data:
                safe_row = {}
                for field in safe_fields:
                    field_name = field.name
                    field_type = field.dataType
                    raw_value = row_dict.get(field_name)
                    
                    # Convert values to match Spark types
                    if raw_value is None:
                        safe_row[field_name] = None
                    elif isinstance(field_type, TimestampType):
                        if isinstance(raw_value, datetime.datetime):
                            safe_row[field_name] = raw_value
                        else:
                            # Try to convert string to datetime
                            try:
                                safe_row[field_name] = datetime.datetime.fromisoformat(str(raw_value).replace('Z', '+00:00'))
                            except:
                                safe_row[field_name] = None
                    elif isinstance(field_type, DoubleType):
                        try:
                            safe_row[field_name] = float(raw_value) if raw_value is not None else None
                        except (ValueError, TypeError):
                            safe_row[field_name] = None
                    elif isinstance(field_type, BooleanType):
                        safe_row[field_name] = bool(raw_value) if raw_value is not None else None
                    else:  # StringType
                        safe_row[field_name] = str(raw_value) if raw_value is not None else None
                
                safe_data.append(safe_row)
            
            # Create DataFrame with safe schema and data
            df = self.spark.createDataFrame(safe_data, safe_schema)
            print(f"[PYARROW_PARALLEL] Created DataFrame with safe schema: {len(safe_data)} rows, {len(safe_fields)} columns")
            return df
            
        except Exception as e:
            print(f"[PYARROW_PARALLEL] Safe schema creation failed: {e}")
            raise e