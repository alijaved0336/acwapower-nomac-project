from django.urls import path

from infrastructure.controllers.widgets.controller import (
    WidgetDetailView,
    WidgetsView,
    WidgetCopyView,
    WidgetBulkDeleteView,
)

urlpatterns = [
    # Bulk operations (no analysisID dependency)
    path(
        "delete/",
        WidgetBulkDeleteView.as_view(),
        name="widget_bulk_delete",
    ),
    # Widget copy operation (must come before analysisID patterns)
    path(
        "copy/<str:widgetID>/",
        WidgetCopyView.as_view(),
        name="widget_copy",
    ),
    # Analysis-specific operations
    path("<str:analysisID>/", WidgetsView.as_view(), name="widgets_list"),
    path(
        "<str:analysisID>/<str:widgetID>/",
        WidgetDetailView.as_view(),
        name="widget_detail",
    ),
]
