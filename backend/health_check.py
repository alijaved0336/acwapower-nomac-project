"""
Health check script for Azure deployment
Tests connectivity to ClickHouse and other services
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nomac.settings')
django.setup()

from config.clickhouse_connector import check_clickhouse_health
from django.core.cache import cache


def health_check():
    """Comprehensive health check for all services"""
    health_status = {
        "status": "healthy",
        "services": {},
        "timestamp": None
    }
    
    # Test ClickHouse
    try:
        clickhouse_health = check_clickhouse_health()
        health_status["services"]["clickhouse"] = clickhouse_health
    except Exception as e:
        health_status["services"]["clickhouse"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Test Redis Cache
    try:
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        health_status["services"]["redis"] = {
            "status": "healthy" if cache_result == 'ok' else "unhealthy",
            "response_time_ms": 0  # Could add timing if needed
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Test Django Settings
    try:
        health_status["services"]["django"] = {
            "status": "healthy",
            "debug": settings.DEBUG,
            "allowed_hosts": settings.ALLOWED_HOSTS
        }
    except Exception as e:
        health_status["services"]["django"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


if __name__ == "__main__":
    import json
    from datetime import datetime
    
    health = health_check()
    health["timestamp"] = datetime.utcnow().isoformat()
    
    print(json.dumps(health, indent=2))
    
    # Exit with error code if unhealthy
    if health["status"] != "healthy":
        sys.exit(1)
