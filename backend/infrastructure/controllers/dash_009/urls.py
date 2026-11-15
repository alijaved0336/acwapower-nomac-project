from django.urls import path

from infrastructure.controllers.dash_009.controller import PumpCategoryFilter, PumpKPISHeatMap
from infrastructure.controllers.dash_009.widgets_controller import UserHeatmapWidgetView

urlpatterns = [
    path('pump-category', PumpCategoryFilter.as_view(), name='pump-category-filter'),
    path('pump-kpis-heatmap', PumpKPISHeatMap.as_view(), name='pump-kpis-heatmap'),
    path('user-heatmap-widget', UserHeatmapWidgetView.as_view(), name='user-heatmap-widget'),
]