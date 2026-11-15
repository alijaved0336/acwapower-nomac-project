from django.urls import path

from infrastructure.controllers.auth.controller import (AuthRefreshView,
                                                        AuthVerifyView)

urlpatterns = [
    path("verify-user/", AuthVerifyView.as_view(), name="verify_azure_user"),
    path("refresh/", AuthRefreshView.as_view(), name="token_refresh"),
]
