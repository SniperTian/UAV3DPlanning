from django.shortcuts import render
from django.http import JsonResponse

import os, sys
sys.path.append("..")
from functions.UAV3DPlanning import UAV3DPlanning
from functions.BuildingManager import Rectangle
from functions.CoordTransform import UTM2WGS84,WGS842UTM


photoArea = None
#shpFile_path = "data/Beijing_Buildings_DWG-Polygon.shp"
shpFile_path = "data_UTM/PKnew.shp"
photoArea = UAV3DPlanning(shpFile_path)

# Create your views here.
def interface(request):
    return render(request,"routeplan3d/interface.html")

def load_shp(request = None):
    global photoArea
    shpFile_path = "data/Beijing_Buildings_DWG-Polygon.shp"
    photoArea = UAV3DPlanning(shpFile_path)

def get_bulidings(request):
    #load_shp()
    global photoArea
    #print(request.POST)
    areaBounds_wgs84 = request.POST.getlist("area_bounds[]")
    sw_utm = WGS842UTM(
        lng = float(areaBounds_wgs84[0]),
        lat = float(areaBounds_wgs84[1]),
    )
    ne_utm = WGS842UTM(
        lng = float(areaBounds_wgs84[2]),
        lat = float(areaBounds_wgs84[3]),
        )
    #print(sw_utm[0],sw_utm[1],ne_utm[0],ne_utm[1])
    targetRegion = Rectangle(sw_utm[1],sw_utm[0],ne_utm[1],ne_utm[0])
    #targetRegion = Rectangle(440180，4426238，441032，4427526)
    photoArea.SetTargetArea(targetRegion)
    buildingList_utm = photoArea.GetBuildingsInfo()
    buildingList_wgs84 = [{
        "polygonExterior_wgs84":[
            UTM2WGS84(point["Y"],point["X"]) for point in building["polygonInfo"]
            ],
        "height": building["height"],
        } for building in buildingList_utm]
    return JsonResponse({
        "success": True,
        "building_list": buildingList_wgs84,
    })