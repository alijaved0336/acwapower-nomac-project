#!/bin/bash

# Simple startup script for Azure App Service
# This script is provided as an alternative if needed

# Set Java environment
export JAVA_HOME=/home/site/wwwroot/.java
export PATH=$JAVA_HOME/bin:$PATH

# Set Hadoop environment for Azure Blob Storage
export HADOOP_HOME=/home/site/wwwroot/.hadoop
export HADOOP_CONF_DIR=/home/site/wwwroot/.hadoop/conf
export PATH=$HADOOP_HOME/bin:$PATH

# Create necessary directories
mkdir -p /tmp/spark
mkdir -p /home/site/wwwroot/logs
mkdir -p /home/site/wwwroot/.hadoop/conf
mkdir -p /home/site/wwwroot/.hadoop/bin

export SPARK_LOCAL_DIRS=/tmp/spark

# Set Python environment
export PYSPARK_PYTHON=python

# Verify Java is available
if [ -f "$JAVA_HOME/bin/java" ]; then
    echo "Java found at $JAVA_HOME/bin/java"
    $JAVA_HOME/bin/java -version
else
    echo "Warning: Java not found at $JAVA_HOME/bin/java"
fi

# Verify directories were created
echo "Verifying directory structure..."
if [ -d "/home/site/wwwroot/logs" ]; then
    echo "✓ Logs directory created successfully"
else
    echo "✗ Failed to create logs directory"
fi

if [ -d "/home/site/wwwroot/.hadoop" ]; then
    echo "✓ Hadoop directory created successfully"
else
    echo "✗ Failed to create Hadoop directory"
fi

if [ -d "/tmp/spark" ]; then
    echo "✓ Spark temp directory created successfully"
else
    echo "✗ Failed to create Spark temp directory"
fi

# Activate virtual environment if it exists
if [ -d "/home/site/wwwroot/antenv" ]; then
    echo "Activating virtual environment..."
    source /home/site/wwwroot/antenv/bin/activate
else
    echo "No virtual environment found, using system Python"
fi

# Collect static files if they don't exist
echo "Checking for static files..."
cd /home/site/wwwroot
if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles 2>/dev/null)" ]; then
    echo "Static files not found, collecting them..."
    python manage.py collectstatic --noinput
    echo "Static files collection completed"
else
    echo "Static files already exist"
fi

# Start the Django application with gunicorn
echo "Starting Django application..."
exec gunicorn --bind=0.0.0.0:8000 --workers=1 --threads=4 --worker-class=gthread --timeout=120 --access-logfile=- --error-logfile=- nomac.wsgi:application
