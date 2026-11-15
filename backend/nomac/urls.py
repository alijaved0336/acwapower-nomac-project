"""nomac URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
# Import column data source controllers
from infrastructure.controllers.columnDataSource import (
    ColumnDataSourceController,
    ColumnDataSourceHealthController,
    ColumnDataSourceCacheController
)

# Import column schema controller
from infrastructure.controllers.columnSchema import ColumnSchemaController

# Import ClickHouse controllers
from infrastructure.controllers.clickhouse.controller import (
    ClickHouseTablesController,
    ClickHouseColumnDataController
)

# Import health check controllers
from infrastructure.controllers.health import (
    HealthCheckController,
    LivenessController,
    ReadinessController
)

# Import scheduler monitoring controller
from infrastructure.controllers.scheduler_monitoring import SchedulerMonitoringController


# Schema view for Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="SWRO API",
        default_version="v1",
        description="API for SWRO application",
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check endpoints (must be before authentication middleware)
    path("health/", HealthCheckController.as_view(), name="health-check"),
    path("liveness/", LivenessController.as_view(), name="liveness-probe"),
    path("readiness/", ReadinessController.as_view(), name="readiness-probe"),
    # Scheduler monitoring endpoint
    path("api/scheduler/monitoring/", SchedulerMonitoringController.as_view(), name="scheduler-monitoring"),
    # Swagger endpoints
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Auth endpoints
    path("auth/", include("infrastructure.controllers.auth.urls")),
    # Dash endpoints
    path("api/", include("infrastructure.controllers.dash_001.urls")),
    path('api/', include("infrastructure.controllers.dash_007.urls")),
    path('api/', include("infrastructure.controllers.dash_008.urls")),
    path('api/', include("infrastructure.controllers.dash_033.urls")),
    path('api/', include("infrastructure.controllers.dash_071.urls")),
    path('api/', include("infrastructure.controllers.dash_030.urls")),
    path('api/', include("infrastructure.controllers.dash_074.urls")),
    
    # Analysis endpoints
    path("analysis/", include("infrastructure.controllers.analysis.urls")),
    # path('analysis/<int:id>/', include("infrastructure.controllers.analysis.urls")),
    # Roles endpoints
    path("api/", include("infrastructure.controllers.roles.urls")),
    # User endpoints
    path("api/", include("infrastructure.controllers.user.urls")),
    # Widgets endpoints
    path("widgets/", include("infrastructure.controllers.widgets.urls")),
    # Column Data Source endpoints
    path("columns/data-source/", ColumnDataSourceController.as_view(), name="column-data-source"),
    path("columns/health/", ColumnDataSourceHealthController.as_view(), name="column-data-source-health"),
    path("columns/cache/", ColumnDataSourceCacheController.as_view(), name="column-data-source-cache"),
    # Column Schema endpoints
    path("columns/", ColumnSchemaController.as_view(), name="column-schema"),
    # ClickHouse ADLS endpoints (new - mirrors analysis APIs) - MUST come before generic patterns
    path("clickhouse/", include("infrastructure.controllers.clickhouse_adls.urls")),

    # ClickHouse endpoints (existing) - specific patterns after include
    path("clickhouse/columns/data/", ClickHouseColumnDataController.as_view(), name="clickhouse-column-data"),
    path('api/', include("infrastructure.controllers.dash_071.urls")),
    path('api/', include("infrastructure.controllers.dash_005.urls")),
    path('api/', include("infrastructure.controllers.dash_009.urls")),
    path('api/', include("infrastructure.controllers.dash_028.urls")),
    path('api/', include("infrastructure.controllers.dash_002.urls")),
    path('api/', include("infrastructure.controllers.dash_032.urls")),
    path('api/', include("infrastructure.controllers.dash_029.urls")),
    # ADLS Event Listener (Azure Event Grid webhook)
    path('api/v1/adls-listener/', include("infrastructure.controllers.adls_listener.urls")),
]

# Static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)