from django.urls import path
from infrastructure.controllers.dash_008.controller import (
    PumpListView,
    OperationalTrendView,
    PerformanceTrendView
)

urlpatterns = [
    # Get Pumps API
    path(
        'dash-008/get-pumps/<str:site_id>/',
        PumpListView.as_view(),
        name='dash_008_get_pumps'
    ),
    
    # Operational Trend API
    path(
        'dash-008/operational-trend/<str:site_id>/<str:pump_type>/',
        OperationalTrendView.as_view(),
        name='dash_008_operational_trend'
    ),
    
    # Performance Trend API
    path(
        'dash-008/performance-trend/<str:site_id>/<str:pump_type>/',
        PerformanceTrendView.as_view(),
        name='dash_008_performance_trend'
    ),
]