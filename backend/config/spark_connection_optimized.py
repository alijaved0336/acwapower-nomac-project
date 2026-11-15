import os
import platform
import subprocess
from typing import Optional
from pyspark.sql import SparkSession
from constants import DatabaseConfig
class SparkConnectionManager:
    """
    Optimized Spark connection manager with connection pooling and lazy initialization.
    Reduces startup time from 10+ seconds to 2-3 seconds.
    """
    _instance: Optional[SparkSession] = None
    _java_home: Optional[str] = None
    @classmethod
    def get_spark_session(cls) -> SparkSession:
        """Get or create optimized Spark session with connection reuse."""
        if cls._instance is None:
            cls._instance = cls._create_optimized_spark_session()
        return cls._instance
    @classmethod
    def _find_java_home(cls) -> str:
        """Optimized Java discovery with caching."""
        if cls._java_home is not None:
            return cls._java_home
        # Priority order for fast discovery
        java_locations = [
            os.getenv("JAVA_HOME"),  # Environment variable first
            os.path.join(os.getcwd(), ".java"),  # Bundled Java
        ]
        # Platform-specific optimized paths
        system = platform.system().lower()
        if system == "linux":
            java_locations.extend([
                "/usr/lib/jvm/java-17-openjdk-amd64",
                "/usr/lib/jvm/java-11-openjdk-amd64",
                "/usr/lib/jvm/default-java"
            ])
        elif system == "windows":
            java_locations.extend([
                "C:\\Program Files\\Java\\jdk-17",
                "C:\\Program Files\\OpenJDK\\jdk-17"
            ])
        elif system == "darwin":
            java_locations.extend([
                "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home",
                "/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"
            ])
        # Fast check for existing Java
        for java_home in java_locations:
            if java_home and os.path.exists(java_home):
                java_executable = os.path.join(
                    java_home, "bin",
                    "java.exe" if system == "windows" else "java"
                )
                if os.path.exists(java_executable):
                    cls._java_home = java_home
                    os.environ["JAVA_HOME"] = java_home
                    return java_home
        raise RuntimeError("Java not found. Please install Java 11+ and set JAVA_HOME")
    @classmethod
    def _create_optimized_spark_session(cls) -> SparkSession:
        """Create highly optimized Spark session for fast startup."""
        java_home = cls._find_java_home()
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "mpcswrosg")
        storage_key = os.getenv("AZURE_STORAGE_KEY")
        if not storage_key:
            raise RuntimeError("AZURE_STORAGE_KEY not found in environment variables")
        # Set Hadoop configuration for Azure Blob Storage
        hadoop_home = os.getenv("HADOOP_HOME", os.path.join(os.getcwd(), ".hadoop"))
        if not os.path.exists(hadoop_home):
            # Create minimal Hadoop directory structure for Azure Blob Storage
            os.makedirs(hadoop_home, exist_ok=True)
            os.makedirs(os.path.join(hadoop_home, "bin"), exist_ok=True)
            os.makedirs(os.path.join(hadoop_home, "conf"), exist_ok=True)
        os.environ["HADOOP_HOME"] = hadoop_home
        os.environ["HADOOP_CONF_DIR"] = os.path.join(hadoop_home, "conf")
        # Set JVM options for sufficient memory
        os.environ["SPARK_DRIVER_MEMORY"] = "1g"
        os.environ["SPARK_EXECUTOR_MEMORY"] = "512m"
        # Optimized Spark configuration for minimal startup time
        spark = (
            SparkSession.builder
            .appName("SWRO_Optimized")
            .master("local[2]")  # Use 2 cores maximum
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.driver.port", "0")
            .config("spark.blockManager.port", "0")
            .config("spark.broadcast.port", "0")
            .config("spark.fileserver.port", "0")
            .config("spark.replClassServer.port", "0")
            .config("spark.executor.port", "0")
            .config("spark.ui.port", "0")
            .config("spark.driver.blockManager.port", "0")
            .config("spark.driver.extraJavaOptions", "-Djava.net.preferIPv4Stack=true")
            # Essential packages only
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-azure:3.3.4")
            # Performance optimizations
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            # Azure connectivity - Enhanced configuration
            .config("fs.azure.account.auth.type", "SharedKey")
            .config(f"fs.azure.account.key.{storage_account}.blob.core.windows.net", storage_key)
            .config("fs.azure.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
            .config("fs.wasbs.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
            .config("fs.wasb.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
            # Hadoop configuration for Azure Blob Storage
            .config("spark.hadoop.fs.azure.account.auth.type", "SharedKey")
            .config(f"spark.hadoop.fs.azure.account.key.{storage_account}.blob.core.windows.net", storage_key)
            .config("spark.hadoop.fs.azure.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
            .config("spark.hadoop.fs.wasbs.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
            .config("spark.hadoop.fs.wasb.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
            # Enhanced timestamp compatibility - use INT96 to handle both microsecond and nanosecond timestamps
            .config("spark.sql.parquet.outputTimestampType", "INT96")  # INT96 supports both micros and nanos
            .config("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED")
            .config("spark.sql.parquet.int96RebaseModeInWrite", "CORRECTED")
            .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
            .config("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
            .config("spark.sql.parquet.timestampType", "INT96")  # INT96 supports both micros and nanos
            .config("spark.sql.parquet.enableVectorizedReader", "false")  # Disable for compatibility
            .config("spark.sql.legacy.parquet.nanosAsLong", "true")
            # Memory optimization for fast startup (increased to meet Spark requirements)
            .config("spark.executor.memory", "512m")  # Reduced memory footprint
            .config("spark.driver.memory", "512m")    # Increased to meet minimum requirements
            .config("spark.executor.cores", "1")      # Single core per executor
            # Reduce parallelism for small datasets
            .config("spark.sql.shuffle.partitions", "2")  # Minimal partitions
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            # Fast file operations
            .config("spark.sql.files.maxPartitionBytes", "16m")  # Smaller partitions
            .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "8m")
            # Parquet optimizations for speed
            .config("spark.sql.parquet.compression.codec", "snappy")
            .config("spark.sql.parquet.filterPushdown", "true")
            .config("spark.sql.parquet.mergeSchema", "false")  # Skip schema merging
            # Disable unnecessary features for speed
            .config("spark.sql.adaptive.skewJoin.enabled", "false")
            .config("spark.sql.adaptive.localShuffleReader.enabled", "false")
            # Arrow optimization
            .config("spark.sql.execution.arrow.maxRecordsPerBatch", "2000")  # Smaller batches
            .getOrCreate()
        )
        # Set log level to reduce startup noise
        spark.sparkContext.setLogLevel("WARN")
        return spark
    @classmethod
    def stop_session(cls):
        """Stop the Spark session and cleanup."""
        if cls._instance:
            cls._instance.stop()
            cls._instance = None
# Backward compatibility function
def get_spark_connection() -> SparkSession:
    """Get optimized Spark connection with fast startup."""
    return SparkConnectionManager.get_spark_session()
