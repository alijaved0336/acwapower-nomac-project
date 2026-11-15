from django.urls import path

from infrastructure.controllers.dash_029.controller import WeightedROTable, AvgWeightedROTable, ROPowerConsumptionChart

urlpatterns = [
    path('weighted-heatmap', WeightedROTable.as_view(), name='Weighted-RO-heatmap'),
    path('avg-weighted-heatmap', AvgWeightedROTable.as_view(), name='Avg-Weighted-RO-heatmap'),
    path('ro-power-consumption-chart', ROPowerConsumptionChart.as_view(), name='RO-Power-Consumption-Chart'),
]