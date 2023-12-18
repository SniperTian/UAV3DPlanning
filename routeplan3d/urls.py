from django.urls import path
from . import views

urlpatterns = [
    path("", views.interface, name="interface"),
    path("get-buildings", views.get_bulidings, name="get_buildings")
]