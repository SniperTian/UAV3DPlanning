from django.shortcuts import render
from django.http import JsonResponse
from ..functions.BuildingManager import getBuildingList

# Create your views here.
def interface(request):
    return render(request,"routeplan3d/interface.html")

def show_bulidings(request):
    buildingList = getBuildingList(request.POST["area_bounds"])
    buildingListJson = []
    for building in buildingList:
        buildingListJson.append({
            "polygon": building._polygon.exterior.coords[:],
            "height": building._h,
        })
    return JsonResponse({
        "success": True,
        "building_list": buildingListJson,
    })