"""
URL configuration for Dashboard 007 - Pump List API and Pump Data API
"""

from django.urls import path
from infrastructure.controllers.dash_007.controller import PumpListView, PumpDataView

urlpatterns = [
    path('dash-007/get-pumps/<str:site_id>/', PumpListView.as_view(), name='dash-007-pump-list'),
    path(
        'dash-007/pump-data/<str:site_id>/<str:Pump_Category>/<str:pump>/<str:Pump_id>/',
        PumpDataView.as_view(),
        name='dash-007-pump-data'
    ),
]
