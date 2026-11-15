from django.urls import path

from infrastructure.controllers.analysis.handlers import (
    AnalysisDeleteView,
    AnalysisListView,
    SitesListView,
    TablesListView,
    RackEndpointsView,

)
from infrastructure.controllers.analysis.handlers.cache_diagnostic_handler import CacheDiagnosticView
from infrastructure.controllers.analysis.handlers.rack_prewarm_handler import RackPrewarmView

urlpatterns = [
    # Analysis CRUD operations
    path("", AnalysisListView.as_view(), name="analysis_list"),
    
    # Directory and table listing operations (now using Spark) - MUST come before generic <str:id>/ pattern
    path("sites/", SitesListView.as_view(), name="sites_list"),
    path("tables/<str:site_id>/", TablesListView.as_view(), name="tables_list"),
    
    # Rack endpoints operations
    path("fetch-racks/", RackEndpointsView.as_view(), name="fetch_racks"),
    
    # Cache diagnostic endpoints
    path("cache-test/", CacheDiagnosticView.as_view(), name="cache_test"),
    path("prewarm-racks/", RackPrewarmView.as_view(), name="prewarm_racks"),
    # Common data operations - MUST come before generic <str:id>/ pattern

    # Column operations removed - using direct /columns/ endpoints instead
    
    # Generic analysis operations - MUST come after specific patterns
    path("<str:id>/", AnalysisDeleteView.as_view(), name="analysis_delete"),

]
