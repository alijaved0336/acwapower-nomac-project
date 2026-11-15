from django.urls import path

from infrastructure.controllers.dash_071.dash_071 import (
    ChemicalsData,
    Area,
    Chemicals,
    ChemicalsStock,
    ChemicalDataByMetric
)

urlpatterns = [
    # path('chemical-data', ChemicalsData.as_view(), name='ferric-chloride-graphs'),
    path('chemical-data', ChemicalDataByMetric.as_view(), name='chemical-data-by-metric'),
    path('area', Area.as_view(), name='area'),
    path('chemicals', Chemicals.as_view(), name='chemicals'),
    path('chemical-stock', ChemicalsStock.as_view(), name='chemical-stock'),
]