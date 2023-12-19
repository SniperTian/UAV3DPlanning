from . import views
from django.urls import path

urlpatterns = [
    path("", views.interface, name="interface"),
    path("get-buildings", views.get_bulidings, name="get_buildings"),
    path("load-shp", views.load_shp, name="load_shp"),
]