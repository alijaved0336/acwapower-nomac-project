from django.urls import path

from infrastructure.controllers.dash_005.dash_005 import PumpCategoryFilter, Card, PumpKPIS, PumpFilter, ActionsOverview

urlpatterns = [
    path('pump-category', PumpCategoryFilter.as_view(), name='pump-category-filter'),
    path('cards-data', Card.as_view(), name='cards-data'),
    path('pump-kpis', PumpKPIS.as_view(), name='pump-kpis'),
    path('pump-filter', PumpFilter.as_view(), name='pump-filter'),
    path('actions-overview', ActionsOverview.as_view(), name='actions-overview'),

]