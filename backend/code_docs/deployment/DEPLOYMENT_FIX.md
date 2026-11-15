# Azure Deployment Fix Documentation

## Problem Analysis

The deployment was failing with the following issues:

1. **ModuleNotFoundError: No module named 'nomac'** - The gunicorn process couldn't find the Django application module
2. **Complex startup command causing failures** - The Azure App Service was configured with an overly complex bash script that was failing during Java setup
3. **Missing proper PYTHONPATH configuration** - The Python module resolution wasn't working correctly in the Azure environment

## Root Cause

The deployment failure was caused by:

1. **No startup command defined in the pipeline** - The pipeline comment said "No startUpCommand - will use the one from App Service configuration", but the App Service had a complex custom command that was failing
2. **Java environment setup in startup command** - The startup command was trying to set up Java environment variables inline, which was causing bash script failures
3. **Module import path issues** - The `nomac` Django module wasn't being found due to incorrect PYTHONPATH configuration

## Solutions Implemented

### 1. **Simplified Startup Command**
```yaml
startUpCommand: 'gunicorn --bind=0.0.0.0:8000 --workers=1 --threads=4 --worker-class=gthread --timeout=120 --access-logfile=- --error-logfile=- nomac.wsgi:application'
```

**Benefits:**
- Direct, reliable gunicorn command
- No complex bash scripting
- Proper module reference to `nomac.wsgi:application`
- Appropriate worker and thread configuration for Azure App Service

### 2. **Clean Environment Variable Configuration**
Added proper environment variables in the Azure pipeline:

```yaml
JAVA_HOME=/home/site/wwwroot/.java
PATH=/home/site/wwwroot/.java/bin:/opt/python/3.11.13/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SPARK_LOCAL_DIRS=/tmp/spark
PYSPARK_PYTHON=python
PYTHONPATH=/home/site/wwwroot
```

**Benefits:**
- Java environment set up through environment variables instead of startup script
- Proper Python path configuration
- Spark configuration for PySpark functionality
- Clean separation of concerns

### 3. **Deployment Configuration Files**

#### `.deployment` file:
```ini
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

**Purpose:**
- Ensures Oryx builds the application during deployment
- Provides explicit build configuration

#### `startup.sh` (Backup Option):
- Created as an alternative startup script if needed
- Contains proper Java environment setup
- Can be used as reference or fallback

### 4. **Improved Build Process**
Enhanced the deployment package preparation:

```bash
# Remove unnecessary files
rm -rf $(Build.ArtifactStagingDirectory)/app/venv
rm -rf $(Build.ArtifactStagingDirectory)/app/temp_output.log
rm -rf $(Build.ArtifactStagingDirectory)/app/debug_modules.py

# Ensure startup script is executable
chmod +x $(Build.ArtifactStagingDirectory)/app/startup.sh
```

**Benefits:**
- Cleaner deployment package
- Faster deployment times
- Properly configured executable permissions

### 5. **Azure App Service Settings Optimization**

Removed problematic settings and optimized others:

```yaml
# Removed (causing issues):
# PYTHON_ENABLE_GUNICORN_MULTIWORKERS=false
# PIP_NO_CACHE_DIR=1
# PIP_DISABLE_PIP_VERSION_CHECK=1

# Optimized:
WEBSITES_CONTAINER_START_TIME_LIMIT=1800  # Reduced from 3600
```

## Testing and Verification

### To verify the fix works:

1. **Check Azure App Service logs** for successful startup
2. **Verify Java availability** in the application logs
3. **Test Django endpoints** to ensure the application is responding
4. **Monitor Spark functionality** if using PySpark features

### Expected log output:
```
JAVA_HOME=/home/site/wwwroot/.java
Starting gunicorn with proper module resolution...
Application startup complete
```

## Future Considerations

### For Production Deployment:
1. **Monitor startup times** - The simplified approach should be faster
2. **Java memory settings** - May need adjustment based on usage
3. **Worker configuration** - Can be scaled up for production load
4. **Health checks** - Ensure endpoints respond correctly

### Alternative Approaches:
1. **Docker containers** - For more control over the environment
2. **Separate Java service** - If Spark becomes a bottleneck
3. **Azure Functions** - For lighter Spark processing tasks

## Troubleshooting

### If deployment still fails:

1. **Check Azure App Service Configuration**:
   - Ensure no custom startup command is set in the Azure portal
   - Verify environment variables are correctly applied

2. **Alternative Startup Command**:
   ```bash
   bash startup.sh
   ```
   (Uses the provided startup.sh script)

3. **Debug Environment**:
   ```bash
   python -c "import sys; print(sys.path)"
   python -c "import nomac; print('Module found')"
   ```

4. **Java Verification**:
   ```bash
   echo $JAVA_HOME
   $JAVA_HOME/bin/java -version
   ```

## File Changes Summary

### Modified Files:
- `azure-pipelines.yml` - Updated with proper startup command and environment variables
- `startup.sh` - Created as backup startup script
- `.deployment` - Added for explicit build configuration

### No changes needed to:
- Django application code
- `requirements.txt`
- `nomac/settings.py`
- `nomac/wsgi.py`

The deployment should now work reliably without the complex bash scripting that was causing failures.
