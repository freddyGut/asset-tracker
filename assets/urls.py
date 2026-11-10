from django.urls import path
from . import views

app_name = "assets"

urlpatterns = [
    # miosito.it/assets/
    path("", views.AssetListView.as_view(), name="asset_list"),
    # miosito.it/assets/new
    path("new/", views.AssetCreateView.as_view(), name="asset_create"),
    # miosito.it/assets/5
    path("<int:pk>/", views.AssetDetailView.as_view(), name="asset_detail"),
    path("<int:pk>/edit", views.AssetUpdateView.as_view(), name="asset_update"),
    path("<int:pk>/delete/", views.AssetDeleteView.as_view(), name="asset_delete"),
]