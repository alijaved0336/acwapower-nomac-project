from django.urls import path

from infrastructure.controllers.dash_032.dash_032 import NormalizedData, StreamFilter

urlpatterns = [
    # add url paths here
    path("normalized-data", NormalizedData.as_view(), name="normalized-data"),
    path("stream-filter", StreamFilter.as_view(), name="=stream-filter"),
]