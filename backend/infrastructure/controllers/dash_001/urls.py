from django.urls import path

from infrastructure.controllers.dash_001.dash_001 import (ClusterListView,
                                                          ClusterSitesListView,
                                                          MapDataView,
                                                          PlantListView, DailyDispatchGraphData)

urlpatterns = [
    path("plants/", PlantListView.as_view(), name="plant-list"),
    path("clusters/", ClusterListView.as_view(), name="cluster-list"),
    path("clusters-sites/", ClusterSitesListView.as_view(), name="cluster-sites-list"),
    path("map-data/", MapDataView.as_view(), name="map-data"),
    path("daily-dispatch-data/", DailyDispatchGraphData.as_view(), name="daily-dispatch-data"),
]
