from django.urls import path
from . import views

urlpatterns = [
    path("", views.interface, name="interface"),
    path("show-buildings", views.show_bulidings, name="show_buildings")
]