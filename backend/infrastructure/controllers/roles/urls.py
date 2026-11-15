"""
URL configuration for roles endpoints.
"""

from django.urls import path

from .controller import (RoleCreateView, RoleDeleteView, RoleListView,
                         RoleUpdateView)

app_name = "roles"

urlpatterns = [
    path("role/list", RoleListView.as_view(), name="roles-list"),
    path("role/update/<str:role_id>", RoleUpdateView.as_view(), name="role-update"),
    path("role/delete/<str:role_id>", RoleDeleteView.as_view(), name="role-delete"),
    path("role/create", RoleCreateView.as_view(), name="role-create"),
]
