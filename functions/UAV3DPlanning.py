import BuildingManager as BM
import shapefile
import numpy as np
import time
from AreaPlanning import AreaPathPlanning

class UAV3DPlanning:
    def __init__(self, shpFilePath):
        self._shpFile = shapefile.Reader(shpFilePath)
        self._recordsNum = self._shpFile.numRecords
        self._shapes = self._shpFile.shapes()
        self._area = BM.Area()
        self._resolution = 1
    
    def SetTargetArea(self, targetRegionRect):
        self._area.UpdateTargetRegion(self._shpFile, self._shapes, self._recordsNum, targetRegionRect)
    
    def GetBuildingsInfo(self):
        return self._area.ExportBuildingsInfo()
    
    # 获取研究区高程栅格
    def GetHeightRaster(self):
        return self._area.Polygon2Raster(self._resolution)
    
    def RoutePlan_Navigation(self, startPoint, endPoint):
        #pointsList = ..., List中的元素应为point3D对象
        pass
    
    def RoutePlan_UrbanReconstruction(self):
        path = AreaPathPlanning(self)
        pointsList = []
        for vp in path:
            pointsList.append(BM.Point3D(vp[0],vp[1],vp[2]))
        sRegionWidth = self._area._targetRegion.x2 - self._area._targetRegion.x1
        sRegionHeight = self._area._targetRegion.y2 - self._area._targetRegion.y1
        sOffsetX = self._area._originX
        sOffsetY = self._area._originY
        UTMpointsList = []
        for point in pointsList:
            sUTMX = sOffsetX + point._y * self._resolution
            sUTMY = sOffsetY + sRegionHeight - point._x * self._resolution
            UTMpointsList.append(BM.Point3D(sUTMX, sUTMY, point._z))
        return UTMpointsList

if __name__ == "__main__":
    start_time = time.time()
    shpFilePath = "./data/PKnew.shp"
    uavRoutePlan = UAV3DPlanning(shpFilePath)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"加载完毕, 执行时间为：{elapsed_time}秒")
    
    targetRegion1 = BM.Rectangle(440180, 4426238, 441032, 4427526)
    uavRoutePlan.SetTargetArea(targetRegion1)
    print(uavRoutePlan.GetBuildingsInfo())
    # data1 = uavRoutePlan.GetHeightRaster()
    uavRoutePlan.RoutePlan_UrbanReconstruction()
    