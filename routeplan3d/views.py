from django.shortcuts import render
from django.http import JsonResponse
from ..functions.BuildingManager import getBuildingList

# Create your views here.
def interface(request):
    return render(request,"routeplan3d/interface.html")

def get_bulidings(request):
    buildingList_wgs84 = getBuildingList(request.POST["area_bounds"])
    return JsonResponse({
        "success": True,
        "building_list": buildingList_wgs84,
    })