import os
import platform
import subprocess
import sys
from constants import DatabaseConfig
from pyspark.sql import SparkSession
# Import optimized connection manager
from config.spark_connection_optimized import SparkConnectionManager

def find_java_home():
    """Find Java installation path - Cross-platform (Windows, Mac, Linux)"""
    
    # Platform-specific Java locations
    possible_java_homes = [
        os.path.join(os.getcwd(), ".java"),  # Bundled Java in current working directory (PRIMARY)
        os.getenv("JAVA_HOME"),  # Environment variable (works on all platforms)
    ]
    
    # Add platform-specific paths
    system = platform.system().lower()
    
    if system == "windows":
        # Windows-specific Java locations
        possible_java_homes.extend([
            "C:\\Program Files\\Java\\jdk-17",
            "C:\\Program Files\\Java\\jdk-11",
            "C:\\Program Files\\Java\\jdk-21", 
            "C:\\Program Files\\OpenJDK\\jdk-17",
            "C:\\Program Files\\OpenJDK\\jdk-11",
            "C:\\Program Files (x86)\\Java\\jdk-17",
            "C:\\Program Files (x86)\\Java\\jdk-11",
            os.path.expanduser("~\\scoop\\apps\\openjdk\\current"),
            os.path.expanduser("~\\scoop\\apps\\openjdk17\\current"),
        ])
        java_executable_name = "java.exe"
        
    elif system == "darwin":  # macOS
        # macOS-specific Java locations
        possible_java_homes.extend([
            "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home",
            "/Library/Java/JavaVirtualMachines/temurin-11.jdk/Contents/Home",
            "/Library/Java/JavaVirtualMachines/openjdk-17.jdk/Contents/Home",
            "/Library/Java/JavaVirtualMachines/openjdk-11.jdk/Contents/Home",
            "/System/Library/Frameworks/JavaVM.framework/Versions/Current",
            "/usr/libexec/java_home",  # macOS java_home utility
            os.path.expanduser("~/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home"),
            "/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home",
            "/usr/local/opt/openjdk/libexec/openjdk.jdk/Contents/Home",
        ])
        java_executable_name = "java"
        
    else:  # Linux and others
        # Linux-specific Java locations  
        possible_java_homes.extend([
            "/home/site/wwwroot/.java",  # Azure App Service
            "/tmp/.java",  # Alternative bundled location
            "/usr/lib/jvm/java-17-openjdk-amd64",
            "/usr/lib/jvm/java-11-openjdk-amd64", 
            "/usr/lib/jvm/java-21-openjdk-amd64",
            "/usr/lib/jvm/default-java",
            "/opt/java/openjdk",
            "/usr/java/latest",
            "/usr/java/default",
        ])
        java_executable_name = "java"
    
    # Debug logging
    print(f"[DEBUG] Platform: {system}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    
    # Check each possible Java home
    for java_home in possible_java_homes:
        if java_home and os.path.exists(java_home):
            print(f"[DEBUG] Checking Java path: {java_home}")
            
            # Special handling for macOS java_home utility
            if system == "darwin" and java_home == "/usr/libexec/java_home":
                try:
                    result = subprocess.run([java_home], capture_output=True, text=True)
                    if result.returncode == 0:
                        actual_java_home = result.stdout.strip()
                        if os.path.exists(actual_java_home):
                            print(f"[DEBUG] macOS java_home utility returned: {actual_java_home}")
                            return actual_java_home
                except:
                    continue
            
            # Standard check for java executable
            java_executable = os.path.join(java_home, "bin", java_executable_name)
            print(f"[DEBUG] Java executable path: {java_executable}")
            
            if os.path.exists(java_executable):
                print(f"[DEBUG] Found working Java at: {java_home}")
                return java_home
    
    # Try to find java in PATH (cross-platform)
    try:
        if system == "windows":
            result = subprocess.run(['where', 'java'], capture_output=True, text=True)
        else:
            result = subprocess.run(['which', 'java'], capture_output=True, text=True)
            
        if result.returncode == 0:
            java_path = result.stdout.strip().split('\n')[0]  # Take first result
            print(f"[DEBUG] Found java in PATH: {java_path}")
            
            # Extract JAVA_HOME from java executable path
            if system == "windows":
                # Windows: java.exe is typically in JAVA_HOME\bin\java.exe
                java_home = java_path.replace('\\bin\\java.exe', '').replace('/bin/java.exe', '')
            else:
                # Unix-like: java is typically in JAVA_HOME/bin/java
                java_home = java_path.replace('/bin/java', '')
                
            if os.path.exists(java_home):
                print(f"[DEBUG] Derived JAVA_HOME from PATH: {java_home}")
                return java_home
    except Exception as e:
        print(f"[DEBUG] Error searching PATH: {e}")
    
    print(f"[DEBUG] No Java installation found")
    return None

def get_spark_connection():
    """Legacy function - now uses optimized connection manager for faster startup."""
    return SparkConnectionManager.get_spark_session()

def get_spark_connection_legacy():
    # Find and set Java home
    java_home = find_java_home()
    if not java_home:
        raise RuntimeError(
            "Java not found. Please ensure Java is installed and either:\n"
            "1. Set JAVA_HOME environment variable, or\n"
            "2. Install Java in one of the standard locations:\n"
            f"   - {os.path.join(os.getcwd(), '.java')} (bundled Java)\n"
            "   - /usr/lib/jvm/java-17-openjdk-amd64\n"
            "   - /usr/lib/jvm/java-11-openjdk-amd64\n"
            "   - /usr/lib/jvm/default-java\n"
            "3. Add java to your PATH"
        )
    
    # Set JAVA_HOME environment variable
    os.environ["JAVA_HOME"] = java_home
    print(f"Using Java at: {java_home}")
    
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "mpcswrosg")
    storage_key = os.getenv("AZURE_STORAGE_KEY")
    
    print(f"[SPARK_CONNECTION] AZURE_STORAGE_ACCOUNT: {storage_account}")
    print(f"[SPARK_CONNECTION] AZURE_STORAGE_KEY present: {'Yes' if storage_key else 'No'}")
    if storage_key:
        print(f"[SPARK_CONNECTION] AZURE_STORAGE_KEY length: {len(storage_key)}")
    else:
        print(f"[SPARK_CONNECTION] Environment variables available: {list(os.environ.keys())}")
    
    # Set HADOOP_HOME for Azure Blob Storage support
    if not os.getenv("HADOOP_HOME"):
        # Try to find hadoop in common locations
        possible_paths = [
            os.path.join(os.getcwd(), ".hadoop"),  # Local development
            "/home/site/wwwroot/.hadoop",  # Azure App Service
            "C:\\hadoop",  # Windows
            "C:\\Program Files\\hadoop",  # Windows
            os.path.join(os.path.dirname(os.getcwd()), "hadoop")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                os.environ["HADOOP_HOME"] = path
                break
        else:
            # If no hadoop found, create a temporary directory
            import tempfile
            temp_hadoop = tempfile.mkdtemp(prefix="hadoop_")
            os.makedirs(os.path.join(temp_hadoop, "conf"), exist_ok=True)
            os.environ["HADOOP_HOME"] = temp_hadoop
            print(f"Warning: Created temporary HADOOP_HOME at {temp_hadoop}")
            print("Please install Hadoop or set HADOOP_HOME environment variable")
    
    # Set HADOOP_CONF_DIR
    hadoop_home = os.getenv("HADOOP_HOME")
    if hadoop_home:
        hadoop_conf_dir = os.path.join(hadoop_home, "conf")
        os.environ["HADOOP_CONF_DIR"] = hadoop_conf_dir
        os.makedirs(hadoop_conf_dir, exist_ok=True)
    
    try:
        spark = (
            SparkSession.builder.appName("ADLSRead")
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-azure:3.3.4,com.microsoft.azure:azure-storage:8.6.6")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            
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
            
            # ENHANCED timestamp configuration - use INT96 to handle both microsecond and nanosecond timestamps
            .config("spark.sql.parquet.outputTimestampType", "INT96")  # INT96 supports both micros and nanos
            .config("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED")
            .config("spark.sql.parquet.int96RebaseModeInWrite", "CORRECTED")
            .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
            .config("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
            .config("spark.sql.parquet.enableVectorizedReader", "false")
            .config("spark.sql.parquet.timestampType", "INT96")  # INT96 supports both micros and nanos
            .config("spark.sql.parquet.readLegacyFormat", "true")
            # Additional timestamp compatibility
            .config("spark.sql.parquet.timestampNTZType", "INT96")  # INT96 supports both micros and nanos
            .config("spark.sql.parquet.respectSummaryFiles", "false")
            .config("spark.sql.parquet.mergeSchema", "false")
            .config("spark.sql.parquet.binaryAsString", "false")
            .config("spark.sql.parquet.pushdown.date", "false")
            .config("spark.sql.parquet.pushdown.timestamp", "false")
            .config("spark.sql.parquet.pushdown.decimal", "false")
            
            # PERFORMANCE OPTIMIZATIONS FOR PRODUCTION
            # Memory and Task Management
            .config("spark.executor.memory", "1g")
            .config("spark.executor.cores", "2")
            .config("spark.driver.memory", "1g")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.minPartitionSize", "32m")
            .config("spark.sql.adaptive.coalescePartitions.initialPartitionNum", "4")
            .config("spark.sql.adaptive.skewJoin.enabled", "true")
            
            # Partition and Task Size Optimization - Target under 1000 KiB tasks
            .config("spark.sql.files.maxPartitionBytes", "32m")  # Further reduced to 32MB
            .config("spark.sql.files.openCostInBytes", "2097152")  # 2MB (reduced from 4MB)
            .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "16m")  # Target 16MB partitions
            .config("spark.sql.adaptive.maxShuffleHashJoinLocalMapThreshold", "16m")
            
            # Parquet-specific optimizations
            .config("spark.sql.parquet.compression.codec", "snappy")
            .config("spark.sql.parquet.mergeSchema", "false")
            .config("spark.sql.parquet.filterPushdown", "true")
            .config("spark.sql.parquet.aggregatePushdown", "true")
            
            # Reduce task overhead for small operations
            .config("spark.task.maxFailures", "1")
            .config("spark.sql.execution.arrow.maxRecordsPerBatch", "5000")
            
            # Local mode optimizations for Azure App Service
            .config("spark.master", "local[2]")  # Use 2 cores max
            .config("spark.sql.shuffle.partitions", "4")  # Reduce from default 200
            
            # Serialization optimization
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            
            .getOrCreate()
        )
        return spark
    except Exception as e:
        print(f"Failed to initialize Spark session: {str(e)}")
        print(f"JAVA_HOME: {os.getenv('JAVA_HOME')}")
        print(f"Java executable exists: {os.path.exists(os.path.join(java_home, 'bin', 'java'))}")
        raise RuntimeError(f"Spark initialization failed: {str(e)}")
