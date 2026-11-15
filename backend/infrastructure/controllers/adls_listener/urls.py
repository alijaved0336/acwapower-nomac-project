from django.urls import path
from .controller import ADLSEventListenerView, ADLSEventHealthView

urlpatterns = [
    path('events/', ADLSEventListenerView.as_view(), name='adls-events'),
    path('health/', ADLSEventHealthView.as_view(), name='adls-listener-health'),
]

