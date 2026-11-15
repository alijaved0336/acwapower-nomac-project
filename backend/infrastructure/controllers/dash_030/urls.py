from django.urls import path

from infrastructure.controllers.dash_030.dash_030 import (
    ROSummaryMergedView, 
    ConductivitiesPass1View, 
    ConductivitiesPass2View,
    ConductivitiesPass1RawDataView,
    ConductivitiesPass2RawDataView,
    FetchRacksView
)

urlpatterns = [
    path("ro-summary-merged/", ROSummaryMergedView.as_view(), name="ro-summary-merged"),
    path("conductivities-pass1/", ConductivitiesPass1View.as_view(), name="conductivities-pass1"),
    path("conductivities-pass2/", ConductivitiesPass2View.as_view(), name="conductivities-pass2"),
    path("conductivities-pass1-table/", ConductivitiesPass1RawDataView.as_view(), name="conductivities-pass1-raw"),
    path("conductivities-pass2-table/", ConductivitiesPass2RawDataView.as_view(), name="conductivities-pass2-raw"),
    path("dash-030/fetch-racks/", FetchRacksView.as_view(), name="fetch-racks"),
]