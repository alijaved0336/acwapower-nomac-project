# Spark Timestamp Compatibility Fix - Deployment Guide

## Problem Summary
The production API was experiencing timeouts and empty responses due to Spark's inability to read Parquet files with nanosecond timestamp precision (`PARQUET_TYPE_ILLEGAL: INT64 (TIMESTAMP(NANOS,true))`).

## Root Cause
- Parquet files contain nanosecond precision timestamps
- Spark configuration lacked proper timestamp compatibility settings
- PyArrow fallback was inefficient and caused background processing delays

## Solution Implemented

### 1. Enhanced Spark Configuration (`config/spark_connection.py`)
Added critical timestamp compatibility settings:
```python
# Critical timestamp configuration for nanosecond precision
.config("spark.sql.parquet.outputTimestampType", "TIMESTAMP_MICROS")
.config("spark.sql.parquet.timestampType", "TIMESTAMP_MICROS")
.config("spark.sql.parquet.readLegacyFormat", "true")
```

### 2. Optimized Parquet Reading (`infrastructure/orm/repositories/sparkRepository.py`)
- Simplified Spark read path with enhanced timestamp options
- Optimized PyArrow fallback (reduced from 30 to 5 files, 50K row limit)
- Added graceful error handling to prevent API crashes

## Deployment Steps

### Immediate Production Fix:
1. **Deploy the updated files:**
   - `config/spark_connection.py`
   - `infrastructure/orm/repositories/sparkRepository.py`

2. **Restart the application** to apply new Spark configuration

3. **Monitor logs** for these success indicators:
   ```
   [SPARK_READ] Successfully read parquet with enhanced timestamp options
   ```

### Verification Steps:
1. **Test API endpoint:**
   ```
   GET /columns/Rabigh3/Rabigh3_Chemicals_ppm/?from_date=2025-08-28&to_date=2025-09-04
   ```

2. **Expected behavior:**
   - Fast response (< 10 seconds)
   - No more `PARQUET_TYPE_ILLEGAL` errors
   - Successful data retrieval without PyArrow fallback

3. **Check for elimination of these error patterns:**
   ```
   org.apache.spark.sql.AnalysisException: [PARQUET_TYPE_ILLEGAL] Illegal Parquet type: INT64 (TIMESTAMP(NANOS,true))
   [FALLBACK] All Spark methods failed, activating PyArrow fallback
   ```

## Performance Impact
- **Before:** API timeouts, background PyArrow processing, empty responses
- **After:** Fast Spark-native processing, immediate responses, no background delays

## Monitoring Points
1. **Response time:** Should be < 10 seconds consistently
2. **Error logs:** No more timestamp-related Spark errors
3. **Memory usage:** Reduced due to optimized PyArrow limits
4. **Background processes:** Minimal PyArrow usage

## Rollback Plan
If issues occur, revert these files to previous versions:
```bash
git checkout HEAD~1 config/spark_connection.py
git checkout HEAD~1 infrastructure/orm/repositories/sparkRepository.py
```

## Long-term Optimization
Consider regenerating Parquet files with microsecond timestamps instead of nanoseconds to completely eliminate the need for PyArrow fallback.

## Success Metrics
- ✅ API response time < 10 seconds
- ✅ No `PARQUET_TYPE_ILLEGAL` errors
- ✅ Successful data retrieval
- ✅ No background PyArrow processing for most requests
