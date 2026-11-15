"""
Enhanced data migration helper for parquet files to ClickHouse.
This module provides utilities for the main migration command.
"""

import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from typing import List, Dict, Any
from azure.storage.filedatalake import DataLakeServiceClient

logger = logging.getLogger(__name__)


class ParquetDataMigrator:
    """Helper class for migrating parquet data to ClickHouse."""

    def __init__(self, azure_ops, clickhouse_client):
        self.azure_ops = azure_ops
        self.clickhouse_client = clickhouse_client

    def migrate_table_data_batch(self, site_name: str, table_name: str,
                                table_path: str, clickhouse_table_name: str,
                                batch_size: int = 10000, max_files: int = 10,
                                file_list: List[str] = None) -> Dict[str, Any]:
        """
        Migrate parquet data to ClickHouse in batches.

        Args:
            site_name: Site identifier
            table_name: Table identifier
            table_path: ADLS path to parquet files
            clickhouse_table_name: Target ClickHouse table name
            batch_size: Number of rows per batch
            max_files: Maximum number of parquet files to process
            file_list: Optional specific list of files to process (if None, gets all files)

        Returns:
            Dictionary with total_rows and file_details (mapping file paths to row counts)
        """
        total_rows = 0
        file_details = {}

        try:
            # Get list of parquet files
            if file_list:
                parquet_files = file_list[:max_files]
            else:
                parquet_files = self._get_parquet_files(table_path, max_files)

            if not parquet_files:
                logger.warning(f"No parquet files found in {table_path}")
                return {'total_rows': 0, 'file_details': {}}

            logger.info(f"Found {len(parquet_files)} parquet files to migrate for {table_name}")

            # Process each file
            for file_path in parquet_files:
                try:
                    file_rows = self._migrate_single_file(
                        file_path, clickhouse_table_name, batch_size
                    )
                    total_rows += file_rows
                    file_details[file_path] = file_rows
                    logger.info(f"Migrated {file_rows} rows from {file_path}")

                except Exception as e:
                    logger.error(f"Failed to migrate file {file_path}: {e}")
                    file_details[file_path] = 0
                    continue

            logger.info(f"Successfully migrated {total_rows} total rows for {table_name}")
            return {
                'total_rows': total_rows,
                'file_details': file_details
            }

        except Exception as e:
            logger.error(f"Error migrating table data for {table_name}: {e}")
            raise

    def _get_parquet_files(self, table_path: str, max_files: int) -> List[str]:
        """Get list of parquet files in the table directory."""
        try:
            filesystem_client = self.azure_ops.filesystem_client
            paths = filesystem_client.get_paths(path=table_path, recursive=True)

            parquet_files = []
            for path in paths:
                if not path.is_directory and path.name.endswith('.parquet'):
                    parquet_files.append(path.name)

                    if len(parquet_files) >= max_files:
                        break

            return parquet_files[:max_files]

        except Exception as e:
            logger.error(f"Error listing parquet files in {table_path}: {e}")
            return []

    def _filter_null_timestamps(self, df: pd.DataFrame, file_path: str) -> tuple:
        """
        Filter out rows with NULL timestamps from DataFrame.

        This method identifies datetime columns and removes rows where ANY datetime column is NULL.
        This prevents ClickHouse insertion errors when trying to insert None into DateTime64 columns.

        Args:
            df: Pandas DataFrame to filter
            file_path: File path (for logging purposes)

        Returns:
            Tuple of (filtered_dataframe, count_of_filtered_rows)
        """
        try:
            if df.empty:
                return df, 0

            original_count = len(df)

            # Find all datetime columns
            datetime_columns = []
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_columns.append(col)

            # If no datetime columns, return as-is
            if not datetime_columns:
                return df, 0

            # Create filter mask: keep rows where ALL datetime columns are NOT NULL
            mask = pd.Series([True] * len(df), index=df.index)
            for col in datetime_columns:
                mask &= df[col].notna()

            # Filter the dataframe
            df_filtered = df[mask].copy()

            filtered_count = original_count - len(df_filtered)

            # Log details if rows were filtered
            if filtered_count > 0:
                null_columns = []
                for col in datetime_columns:
                    null_count = df[col].isna().sum()
                    if null_count > 0:
                        null_columns.append(f"{col}({null_count})")

                logger.debug(
                    f"Filtered {filtered_count} rows with NULL timestamps from {file_path}. "
                    f"NULL counts by column: {', '.join(null_columns)}"
                )

            return df_filtered, filtered_count

        except Exception as e:
            logger.error(f"Error filtering NULL timestamps from {file_path}: {e}")
            # On error, return original dataframe to avoid breaking the migration
            return df, 0

    def _migrate_single_file(self, file_path: str, clickhouse_table_name: str,
                           batch_size: int) -> int:
        """Migrate a single parquet file to ClickHouse."""
        try:
            # Download parquet file
            filesystem_client = self.azure_ops.filesystem_client
            file_client = filesystem_client.get_file_client(file_path)
            download_data = file_client.download_file()
            content = download_data.readall()

            # Read parquet file
            parquet_file = pq.ParquetFile(pa.BufferReader(content))
            total_rows = 0
            total_filtered_rows = 0

            # Process in batches
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                # Convert to pandas DataFrame
                df = batch.to_pandas()

                if df.empty:
                    continue

                # Filter out rows with NULL timestamps
                df_cleaned, filtered_count = self._filter_null_timestamps(df, file_path)
                total_filtered_rows += filtered_count

                if df_cleaned.empty:
                    continue

                # Convert to ClickHouse format and insert
                rows_inserted = self._insert_dataframe_to_clickhouse(
                    df_cleaned, clickhouse_table_name, source_file_path=file_path
                )
                total_rows += rows_inserted

            # Log if any rows were filtered
            if total_filtered_rows > 0:
                logger.warning(
                    f"Skipped {total_filtered_rows} rows with NULL timestamps in {file_path} "
                    f"for table {clickhouse_table_name}"
                )

            return total_rows

        except Exception as e:
            logger.error(f"Error migrating file {file_path}: {e}")
            raise

    def _insert_dataframe_to_clickhouse(self, df: pd.DataFrame,
                                      clickhouse_table_name: str,
                                      source_file_path: str = None) -> int:
        """
        Insert pandas DataFrame into ClickHouse table.

        Args:
            df: Pandas DataFrame to insert
            clickhouse_table_name: Target ClickHouse table name
            source_file_path: ADLS path of source parquet file (for deletion tracking)

        Returns:
            Number of rows inserted
        """
        try:
            if df.empty:
                return 0

            # Add source file path column for deletion tracking
            if source_file_path:
                df = df.copy()  # Avoid modifying original DataFrame
                df['_source_file_path'] = source_file_path

            # Prepare data for ClickHouse
            # Convert DataFrame to list of tuples
            data_rows = []
            for _, row in df.iterrows():
                # Convert pandas values to Python native types
                converted_row = []
                for value in row:
                    if pd.isna(value):
                        converted_row.append(None)
                    elif isinstance(value, pd.Timestamp):
                        converted_row.append(value.to_pydatetime())
                    elif hasattr(value, 'as_tuple'):  # decimal.Decimal check
                        # Convert Decimal to string for ClickHouse String columns
                        converted_row.append(str(value))
                    else:
                        converted_row.append(value)
                data_rows.append(tuple(converted_row))

            # Build INSERT statement
            columns = df.columns.tolist()
            columns_sql = ", ".join([f"`{col}`" for col in columns])
            placeholders = ", ".join(["%s"] * len(columns))

            insert_sql = f"""
            INSERT INTO {clickhouse_table_name} ({columns_sql})
            VALUES ({placeholders})
            """

            # Execute batch insert
            self.clickhouse_client.insert(
                clickhouse_table_name,
                data_rows,
                column_names=columns
            )

            logger.debug(f"Inserted {len(data_rows)} rows into {clickhouse_table_name}")
            return len(data_rows)

        except Exception as e:
            logger.error(f"Error inserting data into {clickhouse_table_name}: {e}")
            raise

    def get_table_row_count(self, clickhouse_table_name: str) -> int:
        """Get the current row count for a ClickHouse table."""
        try:
            count_query = f"SELECT COUNT(*) FROM {clickhouse_table_name}"
            result = self.clickhouse_client.query(count_query)
            return result.result_rows[0][0] if result.result_rows else 0

        except Exception as e:
            logger.error(f"Error getting row count for {clickhouse_table_name}: {e}")
            return 0

    def validate_data_migration(self, clickhouse_table_name: str) -> Dict[str, Any]:
        """Validate the migrated data in ClickHouse."""
        try:
            # Get basic statistics
            stats_query = f"""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT *) as unique_rows
            FROM {clickhouse_table_name}
            """

            result = self.clickhouse_client.query(stats_query)
            stats = result.result_rows[0] if result.result_rows else (0, 0)

            # Get sample data
            sample_query = f"SELECT * FROM {clickhouse_table_name} LIMIT 5"
            sample_result = self.clickhouse_client.query(sample_query)

            return {
                "total_rows": stats[0],
                "unique_rows": stats[1],
                "sample_data": sample_result.result_rows,
                "validation_status": "success" if stats[0] > 0 else "warning"
            }

        except Exception as e:
            logger.error(f"Error validating data for {clickhouse_table_name}: {e}")
            return {
                "validation_status": "error",
                "error_message": str(e)
            }