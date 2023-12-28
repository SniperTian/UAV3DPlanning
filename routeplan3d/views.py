from django.shortcuts import render
from django.http import JsonResponse

import os, sys
sys.path.append("..")
from functions.UAV3DPlanning import UAV3DPlanning
from functions.BuildingManager import Rectangle,Point3D
from functions.CoordTransform import UTM2WGS84,WGS842UTM


photoArea = None
#shpFile_path = "data/Beijing_Buildings_DWG-Polygon.shp"
shpFile_path = "data/PKnew.shp"
photoArea = UAV3DPlanning(shpFile_path)

# Create your views here.
def interface(request):
    return render(request,"routeplan3d/interface.html")

def load_shp(request = None):
    global photoArea
    shpFile_path = "data/Beijing_Buildings_DWG-Polygon.shp"
    photoArea = UAV3DPlanning(shpFile_path)

def get_buildings(request):
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
    
def get_route(request):
    global photoArea
    start_wgs84 = request.POST.getlist("start[]")
    end_wgs84 = request.POST.getlist("end[]")
    start_utm = WGS842UTM(
        lng = float(start_wgs84[0]),
        lat = float(start_wgs84[1]),
    )
    end_utm = WGS842UTM(
        lng = float(end_wgs84[0]),
        lat = float(end_wgs84[1]),
    )
    startPointUTM = Point3D(start_utm[1],start_utm[0],0)
    endPointUTM = Point3D(end_utm[1],end_utm[0],0)
    route_utm = photoArea.RoutePlan_Navigation(startPointUTM,endPointUTM)
    route_wgs84 = [{
        "lnglat": UTM2WGS84(point._y,point._x),
        "height": point._z,
    } for point in route_utm]
    return JsonResponse({
        "success": True,
        "route": route_wgs84,
    })
        