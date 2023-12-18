from django.shortcuts import render
from django.http import JsonResponse
from ..functions.BuildingManager import getBuildingList
from ..functions.CoordTransform import UTM2WGS84,WGS842UTM

# Create your views here.
def interface(request):
    return render(request,"routeplan3d/interface.html")

def get_bulidings(request):
    areaBounds_wgs84 = request.POST["area_bounds"]
    sw_utm = WGS842UTM(areaBounds_wgs84[0])
    buildingList_wgs84 = getBuildingList(request.POST["area_bounds"])
    return JsonResponse({
        "success": True,
        "building_list": buildingList_wgs84,
    })