# 🚀 Developer Session: Spark, SQL & PyArrow in SWRO Backend

## 📋 Session Agenda

1. **Introduction & Overview** (10 mins)
2. **Technology Selection Guide** (15 mins)
3. **Step-by-Step Implementation** (30 mins)
4. **Real Examples & Hands-on** (20 mins)
5. **Best Practices & Common Pitfalls** (10 mins)
6. **Q&A & Discussion** (15 mins)

---

## 🎯 Part 1: Introduction & Overview

### What We're Building Today

```python
# 🎯 GOAL: Learn to build APIs like this
class MyDataAPIView(APIView):
    def get(self, request, site_id: str, table_id: str):
        # Step 1: Choose the right technology
        # Step 2: Implement with proper error handling
        # Step 3: Return optimized results
        pass
```

### The Three Technologies We'll Use

| Technology | Speed | Best For | When to Use |
|------------|-------|----------|-------------|
| **🔥 PyArrow** | ⚡⚡⚡ Ultra Fast | Metadata, Schema, Small Data | Column info, quick lookups |
| **⚡ SparkSQL** | ⚡⚡ Very Fast | Filtered Queries, Joins | Date ranges, aggregations |
| **🚀 Apache Spark** | ⚡ Fast | Complex Analytics, Large Data | Transformations, ML |

### The Magic: Automatic Selection

```python
# 🎯 This is what we'll learn to build
def get_data_smart(site_id: str, table_id: str):
    try:
        # Try PyArrow first (fastest)
        return pyarrow_service.get_metadata(site_id, table_id)
    except:
        try:
            # Fallback to SparkSQL (fast)
            return sparksql_service.get_data(site_id, table_id)
        except:
            # Last resort: Spark (powerful)
            return spark_service.get_data(site_id, table_id)
```

---

## 🧭 Part 2: Technology Selection Guide

### 🎯 Decision Tree: Which Technology to Use?

```python
# 🤔 Ask yourself these questions:

def choose_technology(operation_type: str, data_size: str, complexity: str):
    """
    Simple decision tree for technology selection
    """
    
    # Question 1: What do you need?
    if operation_type == "metadata":
        return "PyArrow"  # ⚡ Fastest for column info
    
    # Question 2: How much data?
    if data_size == "small" and complexity == "simple":
        return "PyArrow"  # ⚡ Perfect for quick operations
    
    # Question 3: Need complex operations?
    if complexity == "complex" or data_size == "large":
        return "Spark"  # 🚀 Most powerful
    
    # Question 4: Need SQL-like operations?
    if operation_type == "query" and complexity == "medium":
        return "SparkSQL"  # ⚡ Fast SQL operations
    
    return "Spark"  # Default fallback
```

### 📊 Real Examples from Our Codebase

```python
# ✅ PyArrow Examples (Ultra Fast)
# - Get column names and types
# - Check if data exists
# - Quick schema validation

# ✅ SparkSQL Examples (Very Fast)  
# - Filter by date range
# - Simple aggregations (COUNT, SUM, AVG)
# - Basic joins

# ✅ Spark Examples (Powerful)
# - Complex transformations
# - Machine learning features
# - Large dataset processing
```

---

## 🛠️ Part 3: Step-by-Step Implementation

### 🎯 Step 1: Basic Setup & Imports

```python
# 📁 File: my_new_api.py

# Step 1.1: Import the basics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

# Step 1.2: Import our data processing tools
from infrastructure.orm.repositories.sparkRepository import SparkRepository
from infrastructure.orm.repositories.sparkSqlRepository import SparkSqlRepository
from infrastructure.orm.repositories.pyarrowParallelProcessor import PyArrowParallelProcessor
from infrastructure.services.fastMetadataService import FastMetadataService

# Step 1.3: Import connection manager
from config.spark_connection_optimized import SparkConnectionManager

# Step 1.4: Set up logging
logger = logging.getLogger(__name__)

print("✅ Step 1 Complete: All imports ready!")
```

### 🎯 Step 2: Create Your Service Class

```python
# Step 2.1: Create a service class to handle data operations
class MyDataService:
    """
    🎯 This is where all the magic happens!
    This class will handle choosing the right technology
    """
    
    def __init__(self):
        # Step 2.2: Initialize all our tools (lazy loading for speed)
        self.spark = None
        self.spark_repo = None
        self.spark_sql_repo = None
        self.pyarrow_processor = None
        self.fast_metadata_service = None
        
        print("✅ Step 2 Complete: Service class created!")
    
    def _initialize_components(self):
        """
        🎯 Lazy initialization - only create what we need, when we need it
        This makes our API start faster!
        """
        if self.spark is None:
            print("🔄 Initializing Spark components...")
            self.spark = SparkConnectionManager.get_spark_session()
            self.spark_repo = SparkRepository()
            self.spark_sql_repo = SparkSqlRepository(self.spark)
            self.pyarrow_processor = PyArrowParallelProcessor(self.spark)
            self.fast_metadata_service = FastMetadataService()
            print("✅ Spark components initialized!")
```

### 🎯 Step 3: Implement the Smart Data Method

```python
    def get_data_smart(self, site_id: str, table_id: str, **options):
        """
        🎯 This is the main method that automatically chooses the best technology!
        
        Args:
            site_id: The site we want data from (e.g., "Rabigh3")
            table_id: The table we want data from (e.g., "Rabigh3_Chemicals_ppm")
            **options: Additional options like from_date, to_date, etc.
        """
        
        # Step 3.1: Initialize components if needed
        self._initialize_components()
        
        # Step 3.2: Try PyArrow first (fastest for metadata)
        try:
            print(f"🔥 Trying PyArrow for {site_id}/{table_id}...")
            result = self._get_data_with_pyarrow(site_id, table_id, **options)
            result["method_used"] = "pyarrow"
            print("✅ PyArrow succeeded!")
            return result
            
        except Exception as pyarrow_error:
            print(f"⚠️ PyArrow failed: {pyarrow_error}")
            
            # Step 3.3: Fallback to SparkSQL (fast for queries)
            try:
                print(f"⚡ Trying SparkSQL for {site_id}/{table_id}...")
                result = self._get_data_with_sparksql(site_id, table_id, **options)
                result["method_used"] = "sparksql"
                print("✅ SparkSQL succeeded!")
                return result
                
            except Exception as sparksql_error:
                print(f"⚠️ SparkSQL failed: {sparksql_error}")
                
                # Step 3.4: Last resort - Spark (most powerful)
                try:
                    print(f"🚀 Trying Spark for {site_id}/{table_id}...")
                    result = self._get_data_with_spark(site_id, table_id, **options)
                    result["method_used"] = "spark"
                    print("✅ Spark succeeded!")
                    return result
                    
                except Exception as spark_error:
                    print(f"❌ All methods failed: {spark_error}")
                    return {
                        "success": False,
                        "error": f"All data retrieval methods failed: {spark_error}",
                        "data": []
                    }
```

### 🎯 Step 4: Implement Each Technology Method

```python
    def _get_data_with_pyarrow(self, site_id: str, table_id: str, **options):
        """
        🔥 PyArrow Method - Ultra Fast for Metadata
        Use this for: Column info, schema, quick data checks
        """
        print("🔥 Using PyArrow (Ultra Fast)...")
        
        # Step 4.1: Use the fast metadata service
        result = self.fast_metadata_service.get_fast_column_metadata(
            site_id=site_id,
            table_id=table_id,
            from_date=options.get('from_date'),
            to_date=options.get('to_date'),
            max_rows=options.get('max_rows', 100)  # Limit for speed
        )
        
        # Step 4.2: Format the result
        return {
            "success": True,
            "data": result.get("columns", []),
            "row_count": result.get("date_filter", {}).get("rows_in_range", 0),
            "processing_time": result.get("performance", {}).get("processing_time_seconds", 0)
        }
    
    def _get_data_with_sparksql(self, site_id: str, table_id: str, **options):
        """
        ⚡ SparkSQL Method - Very Fast for Queries
        Use this for: Date filtering, simple aggregations, joins
        """
        print("⚡ Using SparkSQL (Very Fast)...")
        
        # Step 4.3: Create a temporary view
        view_name = self.spark_sql_repo.create_optimized_temp_view(
            siteName=site_id,
            tableName=table_id
        )
        
        try:
            # Step 4.4: Build the SQL query
            sql_query = self._build_sql_query(view_name, **options)
            print(f"📝 Executing SQL: {sql_query}")
            
            # Step 4.5: Execute the query
            result_df = self.spark.sql(sql_query)
            result_data = [row.asDict() for row in result_df.collect()]
            
            return {
                "success": True,
                "data": result_data,
                "row_count": len(result_data)
            }
            
        finally:
            # Step 4.6: Always cleanup the temporary view
            self.spark_sql_repo.cleanup_temp_view(view_name)
    
    def _get_data_with_spark(self, site_id: str, table_id: str, **options):
        """
        🚀 Spark Method - Most Powerful
        Use this for: Complex transformations, large datasets, ML features
        """
        print("🚀 Using Spark (Most Powerful)...")
        
        # Step 4.7: Read data with Spark
        df = self.spark_repo.read_parquet_optimized(
            siteName=site_id,
            tableName=table_id,
            from_date=options.get('from_date'),
            to_date=options.get('to_date'),
            columns=options.get('columns'),
            limit=options.get('limit', 1000)
        )
        
        # Step 4.8: Apply any additional transformations
        if options.get('transform'):
            df = self._apply_transformations(df, options['transform'])
        
        # Step 4.9: Collect results
        result_data = [row.asDict() for row in df.collect()]
        
        return {
            "success": True,
            "data": result_data,
            "row_count": len(result_data)
        }
```

### 🎯 Step 5: Helper Methods

```python
    def _build_sql_query(self, view_name: str, **options):
        """
        🎯 Helper method to build SQL queries
        """
        # Step 5.1: Start with basic SELECT
        query = f"SELECT * FROM {view_name}"
        
        # Step 5.2: Add WHERE clause for date filtering
        conditions = []
        if options.get('from_date'):
            conditions.append(f"Datetime >= '{options['from_date']}'")
        if options.get('to_date'):
            conditions.append(f"Datetime <= '{options['to_date']}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Step 5.3: Add LIMIT
        if options.get('limit'):
            query += f" LIMIT {options['limit']}"
        
        return query
    
    def _apply_transformations(self, df, transform_type: str):
        """
        🎯 Helper method for Spark transformations
        """
        from pyspark.sql import functions as F
        
        if transform_type == "normalize":
            # Example: Normalize values
            df = df.withColumn("normalized_value", F.col("Value") / 100)
        elif transform_type == "categorize":
            # Example: Add categories
            df = df.withColumn("category", 
                F.when(F.col("Value") > 50, "High")
                .when(F.col("Value") > 25, "Medium")
                .otherwise("Low")
            )
        
        return df
```

### 🎯 Step 6: Create the API View

```python
# Step 6.1: Create the API view class
class MyDataAPIView(APIView):
    """
    🎯 This is your API endpoint!
    This is what other developers will call
    """
    
    def __init__(self):
        super().__init__()
        # Step 6.2: Initialize our service
        self.data_service = MyDataService()
        print("✅ API View created with data service!")
    
    def get(self, request, site_id: str, table_id: str):
        """
        🎯 This method handles GET requests to your API
        
        Example URL: /api/my-data/Rabigh3/Rabigh3_Chemicals_ppm/
        """
        try:
            print(f"📥 Received request for {site_id}/{table_id}")
            
            # Step 6.3: Get query parameters
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            limit = request.GET.get('limit', 100)
            
            # Step 6.4: Call our smart data service
            result = self.data_service.get_data_smart(
                site_id=site_id,
                table_id=table_id,
                from_date=from_date,
                to_date=to_date,
                limit=int(limit)
            )
            
            # Step 6.5: Return the response
            return Response({
                "success": True,
                "message": f"Data retrieved successfully for {site_id}/{table_id}",
                "data": result.get("data", []),
                "method_used": result.get("method_used", "unknown"),
                "row_count": result.get("row_count", 0),
                "filters_applied": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "limit": limit
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            logger.error(f"Error in MyDataAPIView: {str(e)}")
            
            return Response({
                "success": False,
                "message": f"Failed to retrieve data: {str(e)}",
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 🎯 Step 7: Add URL Configuration

```python
# 📁 File: urls.py

from django.urls import path
from .my_new_api import MyDataAPIView

urlpatterns = [
    # Step 7.1: Add your new API endpoint
    path("my-data/<str:site_id>/<str:table_id>/", MyDataAPIView.as_view(), name="my_data_api"),
]
```

---

## 🎯 Part 4: Real Examples & Hands-on

### 🎯 Example 1: Simple Column Metadata API

```python
# 🎯 Let's build a simple API that gets column information
class ColumnInfoAPIView(APIView):
    """
    📊 Simple API to get column information
    Perfect for PyArrow usage!
    """
    
    def get(self, request, site_id: str, table_id: str):
        try:
            # Step 1: Use PyArrow (perfect for metadata)
            fast_service = FastMetadataService()
            result = fast_service.get_fast_column_metadata(
                site_id=site_id,
                table_id=table_id,
                max_rows=10  # Just need a few rows for column info
            )
            
            # Step 2: Extract just the column information
            columns_info = []
            for column in result.get("columns", []):
                columns_info.append({
                    "name": column["name"],
                    "type": column["type"],
                    "nullable": column["nullable"],
                    "sample_values": column["dataSource"][:5]  # First 5 values
                })
            
            return Response({
                "success": True,
                "site_id": site_id,
                "table_id": table_id,
                "columns": columns_info,
                "method_used": "pyarrow_fast_metadata"
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)
```

### 🎯 Example 2: Date-Filtered Data API

```python
# 🎯 Let's build an API that filters data by date range
class DateFilteredDataAPIView(APIView):
    """
    📅 API to get data within a date range
    Perfect for SparkSQL usage!
    """
    
    def get(self, request, site_id: str, table_id: str):
        try:
            # Step 1: Get date parameters
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            
            if not from_date or not to_date:
                return Response({
                    "success": False,
                    "error": "from_date and to_date are required"
                }, status=400)
            
            # Step 2: Use SparkSQL (perfect for date filtering)
            spark = SparkConnectionManager.get_spark_session()
            sql_repo = SparkSqlRepository(spark)
            
            # Step 3: Create temporary view
            view_name = sql_repo.create_optimized_temp_view(site_id, table_id)
            
            try:
                # Step 4: Build and execute SQL query
                sql_query = f"""
                    SELECT Datetime, Value, Category
                    FROM {view_name}
                    WHERE Datetime >= '{from_date}' 
                    AND Datetime <= '{to_date}'
                    ORDER BY Datetime
                    LIMIT 1000
                """
                
                result_df = spark.sql(sql_query)
                result_data = [row.asDict() for row in result_df.collect()]
                
                return Response({
                    "success": True,
                    "data": result_data,
                    "row_count": len(result_data),
                    "date_range": {"from": from_date, "to": to_date},
                    "method_used": "sparksql_optimized"
                })
                
            finally:
                # Step 5: Always cleanup
                sql_repo.cleanup_temp_view(view_name)
                
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)
```

### 🎯 Example 3: Complex Analytics API

```python
# 🎯 Let's build an API that does complex analytics
class AnalyticsAPIView(APIView):
    """
    📈 API for complex data analytics
    Perfect for Spark usage!
    """
    
    def get(self, request, site_id: str, table_id: str):
        try:
            # Step 1: Use Spark for complex operations
            spark_repo = SparkRepository()
            
            # Step 2: Read the data
            df = spark_repo.read_parquet_optimized(
                siteName=site_id,
                tableName=table_id
            )
            
            # Step 3: Perform complex analytics
            from pyspark.sql import functions as F
            
            # Calculate daily statistics
            daily_stats = df.groupBy(
                F.date_format("Datetime", "yyyy-MM-dd").alias("date")
            ).agg(
                F.avg("Value").alias("avg_value"),
                F.max("Value").alias("max_value"),
                F.min("Value").alias("min_value"),
                F.count("Value").alias("count"),
                F.stddev("Value").alias("stddev_value")
            ).orderBy("date")
            
            # Calculate trends
            trend_analysis = daily_stats.withColumn(
                "trend",
                F.when(F.col("avg_value") > F.lag("avg_value").over(
                    F.Window.partitionBy().orderBy("date")
                ), "increasing")
                .when(F.col("avg_value") < F.lag("avg_value").over(
                    F.Window.partitionBy().orderBy("date")
                ), "decreasing")
                .otherwise("stable")
            )
            
            # Step 4: Collect results
            result_data = [row.asDict() for row in trend_analysis.collect()]
            
            return Response({
                "success": True,
                "analytics": result_data,
                "method_used": "spark_complex_analytics"
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)
```

---

## 🎯 Part 5: Best Practices & Common Pitfalls

### ✅ Best Practices

#### 1. **Always Use the Processing Hierarchy**

```python
# ✅ GOOD: Try fast methods first, fallback to powerful methods
def get_data_smart(site_id: str, table_id: str):
    try:
        return pyarrow_service.get_metadata(site_id, table_id)  # Fastest
    except:
        try:
            return sparksql_service.get_data(site_id, table_id)  # Fast
        except:
            return spark_service.get_data(site_id, table_id)  # Powerful

# ❌ BAD: Always using the most powerful method
def get_data_slow(site_id: str, table_id: str):
    return spark_service.get_data(site_id, table_id)  # Overkill for simple tasks
```

#### 2. **Proper Error Handling**

```python
# ✅ GOOD: Comprehensive error handling
def robust_operation(site_id: str, table_id: str):
    try:
        result = primary_method(site_id, table_id)
        return result
    except Exception as primary_error:
        logger.warning(f"Primary method failed: {primary_error}")
        try:
            result = fallback_method(site_id, table_id)
            return result
        except Exception as fallback_error:
            logger.error(f"All methods failed: {fallback_error}")
            return {"error": "Operation failed", "data": []}

# ❌ BAD: No error handling
def fragile_operation(site_id: str, table_id: str):
    result = primary_method(site_id, table_id)  # Can crash the API
    return result
```

#### 3. **Resource Cleanup**

```python
# ✅ GOOD: Always cleanup resources
def process_with_cleanup(site_id: str, table_id: str):
    view_name = None
    try:
        view_name = sql_repo.create_optimized_temp_view(site_id, table_id)
        result = spark.sql(f"SELECT * FROM {view_name}")
        return result.collect()
    finally:
        if view_name:
            sql_repo.cleanup_temp_view(view_name)  # Always cleanup

# ❌ BAD: No cleanup
def process_without_cleanup(site_id: str, table_id: str):
    view_name = sql_repo.create_optimized_temp_view(site_id, table_id)
    result = spark.sql(f"SELECT * FROM {view_name}")
    return result.collect()  # View never cleaned up - memory leak!
```

#### 4. **Parameter Validation**

```python
# ✅ GOOD: Validate parameters
def validated_operation(site_id: str, table_id: str, from_date: str = None):
    # Validate required parameters
    if not site_id or not table_id:
        raise ValueError("site_id and table_id are required")
    
    # Validate date format
    if from_date:
        try:
            datetime.strptime(from_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("from_date must be in YYYY-MM-DD format")
    
    # Proceed with operation
    return process_data(site_id, table_id, from_date)

# ❌ BAD: No validation
def unvalidated_operation(site_id: str, table_id: str, from_date: str = None):
    return process_data(site_id, table_id, from_date)  # Can fail unexpectedly
```

### ❌ Common Pitfalls

#### 1. **Using Wrong Technology for the Task**

```python
# ❌ BAD: Using Spark for simple metadata
def get_column_names_slow(site_id: str, table_id: str):
    spark_repo = SparkRepository()
    df = spark_repo.read_parquet_optimized(site_id, table_id)  # Overkill!
    return [field.name for field in df.schema.fields]

# ✅ GOOD: Using PyArrow for simple metadata
def get_column_names_fast(site_id: str, table_id: str):
    fast_service = FastMetadataService()
    result = fast_service.get_fast_column_metadata(site_id, table_id)
    return [col["name"] for col in result["columns"]]
```

#### 2. **Not Handling Memory Issues**

```python
# ❌ BAD: Loading all data into memory
def get_all_data_unsafe(site_id: str, table_id: str):
    df = spark_repo.read_parquet_optimized(site_id, table_id)
    return df.collect()  # Can cause OutOfMemoryError

# ✅ GOOD: Limiting data size
def get_data_safe(site_id: str, table_id: str, limit: int = 1000):
    df = spark_repo.read_parquet_optimized(site_id, table_id, limit=limit)
    return df.collect()  # Safe with limit
```

#### 3. **Not Using Lazy Initialization**

```python
# ❌ BAD: Initializing everything at startup
class MyService:
    def __init__(self):
        self.spark = SparkConnectionManager.get_spark_session()  # Slow startup
        self.spark_repo = SparkRepository()  # Slow startup
        self.sql_repo = SparkSqlRepository(self.spark)  # Slow startup

# ✅ GOOD: Lazy initialization
class MyService:
    def __init__(self):
        self.spark = None
        self.spark_repo = None
        self.sql_repo = None
    
    def _initialize_if_needed(self):
        if self.spark is None:
            self.spark = SparkConnectionManager.get_spark_session()
            self.spark_repo = SparkRepository()
            self.sql_repo = SparkSqlRepository(self.spark)
```

---

## 🎯 Part 6: Hands-on Exercise

### 🎯 Exercise: Build a Temperature Analytics API

**Goal**: Build an API that analyzes temperature data from a site

**Requirements**:
1. Get temperature data for a date range
2. Calculate daily min/max/average temperatures
3. Identify temperature trends
4. Use the processing hierarchy (PyArrow → SparkSQL → Spark)

**Step-by-Step Solution**:

```python
# 🎯 Step 1: Create the service class
class TemperatureAnalyticsService:
    def __init__(self):
        self.spark = None
        self.spark_repo = None
        self.fast_service = None
    
    def _initialize_components(self):
        if self.spark is None:
            self.spark = SparkConnectionManager.get_spark_session()
            self.spark_repo = SparkRepository()
            self.fast_service = FastMetadataService()
    
    def analyze_temperature(self, site_id: str, table_id: str, from_date: str, to_date: str):
        """
        🎯 Main method that tries different approaches
        """
        self._initialize_components()
        
        # Try PyArrow first (for quick data check)
        try:
            print("🔥 Trying PyArrow for quick analysis...")
            return self._analyze_with_pyarrow(site_id, table_id, from_date, to_date)
        except Exception as e:
            print(f"⚠️ PyArrow failed: {e}")
        
        # Try SparkSQL (for date filtering and aggregation)
        try:
            print("⚡ Trying SparkSQL for analytics...")
            return self._analyze_with_sparksql(site_id, table_id, from_date, to_date)
        except Exception as e:
            print(f"⚠️ SparkSQL failed: {e}")
        
        # Try Spark (for complex analytics)
        try:
            print("🚀 Trying Spark for complex analytics...")
            return self._analyze_with_spark(site_id, table_id, from_date, to_date)
        except Exception as e:
            print(f"❌ All methods failed: {e}")
            return {"error": "All analysis methods failed"}
    
    def _analyze_with_pyarrow(self, site_id: str, table_id: str, from_date: str, to_date: str):
        """
        🔥 PyArrow: Quick temperature overview
        """
        result = self.fast_service.get_fast_column_metadata(
            site_id=site_id,
            table_id=table_id,
            from_date=from_date,
            to_date=to_date,
            max_rows=100
        )
        
        # Find temperature columns
        temp_columns = [col for col in result["columns"] if "temp" in col["name"].lower()]
        
        return {
            "method": "pyarrow_quick_analysis",
            "temperature_columns": [col["name"] for col in temp_columns],
            "sample_data": temp_columns[0]["dataSource"][:10] if temp_columns else [],
            "row_count": result.get("date_filter", {}).get("rows_in_range", 0)
        }
    
    def _analyze_with_sparksql(self, site_id: str, table_id: str, from_date: str, to_date: str):
        """
        ⚡ SparkSQL: Daily temperature statistics
        """
        from infrastructure.orm.repositories.sparkSqlRepository import SparkSqlRepository
        sql_repo = SparkSqlRepository(self.spark)
        
        view_name = sql_repo.create_optimized_temp_view(site_id, table_id)
        
        try:
            # Daily temperature statistics
            sql_query = f"""
                SELECT 
                    DATE(Datetime) as date,
                    MIN(Temperature) as min_temp,
                    MAX(Temperature) as max_temp,
                    AVG(Temperature) as avg_temp,
                    COUNT(Temperature) as readings_count
                FROM {view_name}
                WHERE Datetime >= '{from_date}' 
                AND Datetime <= '{to_date}'
                AND Temperature IS NOT NULL
                GROUP BY DATE(Datetime)
                ORDER BY date
            """
            
            result_df = self.spark.sql(sql_query)
            daily_stats = [row.asDict() for row in result_df.collect()]
            
            return {
                "method": "sparksql_daily_stats",
                "daily_statistics": daily_stats,
                "total_days": len(daily_stats)
            }
            
        finally:
            sql_repo.cleanup_temp_view(view_name)
    
    def _analyze_with_spark(self, site_id: str, table_id: str, from_date: str, to_date: str):
        """
        🚀 Spark: Complex temperature trend analysis
        """
        from pyspark.sql import functions as F
        from pyspark.sql.window import Window
        
        # Read data
        df = self.spark_repo.read_parquet_optimized(
            siteName=site_id,
            tableName=table_id,
            from_date=from_date,
            to_date=to_date
        )
        
        # Daily statistics with trend analysis
        daily_stats = df.groupBy(
            F.date_format("Datetime", "yyyy-MM-dd").alias("date")
        ).agg(
            F.min("Temperature").alias("min_temp"),
            F.max("Temperature").alias("max_temp"),
            F.avg("Temperature").alias("avg_temp"),
            F.count("Temperature").alias("readings_count")
        ).orderBy("date")
        
        # Add trend analysis
        window = Window.orderBy("date")
        trend_analysis = daily_stats.withColumn(
            "temp_trend",
            F.when(F.col("avg_temp") > F.lag("avg_temp").over(window), "increasing")
            .when(F.col("avg_temp") < F.lag("avg_temp").over(window), "decreasing")
            .otherwise("stable")
        ).withColumn(
            "temp_change",
            F.col("avg_temp") - F.lag("avg_temp").over(window)
        )
        
        # Calculate overall statistics
        overall_stats = df.agg(
            F.avg("Temperature").alias("overall_avg"),
            F.min("Temperature").alias("overall_min"),
            F.max("Temperature").alias("overall_max"),
            F.stddev("Temperature").alias("temp_stddev")
        ).collect()[0].asDict()
        
        return {
            "method": "spark_complex_analysis",
            "daily_trends": [row.asDict() for row in trend_analysis.collect()],
            "overall_statistics": overall_stats
        }

# 🎯 Step 2: Create the API view
class TemperatureAnalyticsAPIView(APIView):
    def __init__(self):
        super().__init__()
        self.analytics_service = TemperatureAnalyticsService()
    
    def get(self, request, site_id: str, table_id: str):
        try:
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            
            if not from_date or not to_date:
                return Response({
                    "success": False,
                    "error": "from_date and to_date are required"
                }, status=400)
            
            result = self.analytics_service.analyze_temperature(
                site_id=site_id,
                table_id=table_id,
                from_date=from_date,
                to_date=to_date
            )
            
            return Response({
                "success": True,
                "site_id": site_id,
                "table_id": table_id,
                "date_range": {"from": from_date, "to": to_date},
                "analysis": result
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)
```

---

## 🎯 Part 7: Testing Your APIs

### 🎯 How to Test Your New API

```python
# 🎯 Step 1: Start your Django server
# python manage.py runserver

# 🎯 Step 2: Test with curl
import subprocess

def test_api():
    # Test the temperature analytics API
    url = "http://localhost:8000/api/temperature-analytics/Rabigh3/Rabigh3_Chemicals_ppm/"
    params = "?from_date=2025-01-01&to_date=2025-01-31"
    
    result = subprocess.run([
        "curl", "-X", "GET", 
        f"{url}{params}",
        "-H", "Content-Type: application/json"
    ], capture_output=True, text=True)
    
    print("API Response:")
    print(result.stdout)

# 🎯 Step 3: Test in Python
import requests

def test_api_python():
    url = "http://localhost:8000/api/temperature-analytics/Rabigh3/Rabigh3_Chemicals_ppm/"
    params = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-31"
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
```

---

## 🎯 Part 8: Q&A & Discussion

### 🤔 Common Questions

**Q: When should I use PyArrow vs SparkSQL vs Spark?**

**A**: 
- **PyArrow**: Column metadata, schema info, quick data checks
- **SparkSQL**: Date filtering, simple aggregations, joins
- **Spark**: Complex transformations, large datasets, ML features

**Q: How do I handle memory issues?**

**A**: 
- Use `limit` parameter to restrict data size
- Use lazy initialization to avoid loading everything at startup
- Clean up temporary views and resources

**Q: What if all methods fail?**

**A**: 
- Always have a fallback response
- Log errors for debugging
- Return meaningful error messages to users

**Q: How do I optimize performance?**

**A**: 
- Use the processing hierarchy (fast methods first)
- Limit data size with appropriate parameters
- Use proper indexing and filtering

---

## 🎯 Summary

### 🎯 What We Learned

1. **Technology Selection**: Choose the right tool for the job
2. **Processing Hierarchy**: PyArrow → SparkSQL → Spark
3. **Error Handling**: Always have fallbacks
4. **Resource Management**: Clean up after yourself
5. **Performance**: Use lazy initialization and limits

### 🎯 Next Steps

1. **Practice**: Build your own API using the patterns
2. **Experiment**: Try different technologies for the same task
3. **Optimize**: Measure performance and improve
4. **Share**: Help other developers with your learnings

### 🎯 Key Takeaways

- **Start Simple**: Use PyArrow for basic operations
- **Scale Up**: Use SparkSQL for queries, Spark for complex analytics
- **Handle Errors**: Always have fallback methods
- **Clean Up**: Always cleanup resources
- **Test**: Test your APIs thoroughly

---

## 🎯 Resources

- **Code Examples**: All examples in this guide are ready to use
- **Documentation**: Check the DEVELOPER_GUIDE.md for more details
- **Existing APIs**: Look at the Columns API for real-world examples
- **Team Support**: Ask questions in the team chat

---

**Happy Coding! 🚀**

*Remember: Start with PyArrow, fallback to SparkSQL, use Spark when you need the power!*
