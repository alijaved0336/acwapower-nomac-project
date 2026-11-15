from django.urls import path

from infrastructure.controllers.dash_074.dash_074 import AlertsTableView, AlertsGraphView, AssetHistoryView

urlpatterns = [
    # add url paths here
    path("alerts-table-data/",AlertsTableView.as_view(), name = "alerts-table-data"),
    path("alerts-graph-data/",AlertsGraphView.as_view(), name = "alerts-graph-data"),
    path("asset-history-data/",AssetHistoryView.as_view(), name = "asset-history-data")
    
]