from django.urls import path
from infrastructure.controllers.dash_033.controller import RackRuntimeListView, RackCIPValidListView, RackCIPGraphView, RackMembraneGraphView, \
                RackMembraneTableView, RackMembranePercentageGraphView, RackCIPFlushingListView, ColumnsListView , RacksListView

urlpatterns = [
    path('dash-033/racks/runtime', RackRuntimeListView.as_view(), name='racks-runtime-list'),
    path('dash-033/racks/cip-validated', RackCIPValidListView.as_view(), name='racks-cip-list'),
    path('dash-033/racks/cip-flushing', RackCIPFlushingListView.as_view(), name='racks-cip-flushing-list'),
    path('dash-033/racks/cip-graph', RackCIPGraphView.as_view(), name='racks-cip-graph-list'),
    path('dash-033/racks/membrane-graph', RackMembraneGraphView.as_view(), name='racks-membrance-graph-list'),
    path('dash-033/racks/membrane-table', RackMembraneTableView.as_view(), name='racks-membrane-table-list'),
    path('dash-033/racks/membrane-percentage-graph', RackMembranePercentageGraphView.as_view(), name='racks-membrane-percentage-graph-list'),
    path("dash-033/columns/<str:site_id>/", ColumnsListView.as_view(),name="dash_r3-columns-list"),
    path("dash-033/racks/<str:site_id>/",RacksListView.as_view(),name="dash_r3-racks-list"),
]