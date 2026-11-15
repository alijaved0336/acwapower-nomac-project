from django.urls import path

from infrastructure.controllers.dash_028.controller import ROQuality, ROQualityRacksTable, ROQualityRacksOperationalStatus

urlpatterns = [
    path('ro_quality_overall', ROQuality.as_view(), name='RO-quality-overall'),
    path('ro_quality_racks_table', ROQualityRacksTable.as_view(), name='RO-quality-racks-table'),
    path('ro_quality_racks_operational_status', ROQualityRacksOperationalStatus.as_view(), name='RO-quality-racks-operational-status'),
]