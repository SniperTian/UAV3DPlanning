import BuildingManager as BM
import shapefile
import numpy as np
import time

class UAV3DPlanning:
    def __init__(self, shpFilePath):
        self._shpFile = shapefile.Reader(shpFilePath)
        self._recordsNum = self._shpFile.numRecords
        self._shapes = self._shpFile.shapes()
        self._area = BM.Area()
        self._resolution = 2
    
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
        #pointsList = ..., List中的元素应为point3D对象
        pass

if __name__ == "__main__":
    start_time = time.time()
    shpFilePath = "./data/Beijing_Buildings_DWG-Polygon.shp"
    uavRoutePlan = UAV3DPlanning(shpFilePath)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"加载完毕, 执行时间为：{elapsed_time}秒")
    
    targetRegion1 = BM.Rectangle(486796, 4425988, 487679, 4426941)
    uavRoutePlan.SetTargetArea(targetRegion1)
    print(uavRoutePlan.GetBuildingsInfo())
    data1 = uavRoutePlan.GetHeightRaster()
    