from . import views
from django.urls import path

urlpatterns = [
    path("", views.interface, name="interface"),
    path("load-shp", views.load_shp, name="load_shp"),
    path("get-buildings", views.get_buildings, name="get_buildings"),
    path("get-route", views.get_route, name="get_route"),
]