from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def interface(request):
    return render(request,"routeplan3d/interface.html")

def show_bulidings(request):
    sw_wgs84 = request.POST["sw_wgs84"]
    ne_wgs84 = request.POST["ne_wgs84"]
    building_list = []
    # building
    # {}
    return JsonResponse({
        "success": True,
        "building_list": building_list,
    })