import shapefile
from shapely.geometry import Polygon
import time

class Point3D:
    def __init__(self, x, y, z):
        self._x = x
        self._y = y
        self._z = z

#(x1,y1)为左下角点坐标, (x2,y2)为右上角点坐标
class Rectangle:
    def __init__(self, x1, y1, x2, y2):
        if(x1 > x2):
            raise Exception("x1 should be less than or equal to x2")
        if(y1 > y2):
            raise Exception("y1 should be less than or equal to y2")
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2

    def Convert2Polygon(self):
        sPolygon = Polygon([(self._x1, self._y1), (self._x2, self._y1),
                            (self._x2, self._y2), (self._x1, self._y2)])
        return sPolygon

class Building:
    def __init__(self, polygon, height):
        self._polygon = polygon
        self._h = height

class Area:
    def __init__(self, shpFilePath, targetRegionRect):
        self._BuildingsList = []
        shpFile = shapefile.Reader(shpFilePath)
        sRecordsNum = shpFile.numRecords
        sShapes = shpFile.shapes()
        sIdList = self.FindPolygonsInTargetRegion(sShapes, sRecordsNum, targetRegionRect)
        sZList = []
        for i in range(len(sIdList)):
            sZList.append(shpFile.record(sIdList[i])[6])
        self.CroppingUsingTargetRegion(sShapes, sIdList, sZList, targetRegionRect)
        pass

    def FindPolygonsInTargetRegion(self, shpPolygons, recordsNum, targetRegionRect):
        sIdList = []
        sXmin = targetRegion._x1
        sXmax = targetRegion._x2
        sYmin = targetRegion._y1
        sYmax = targetRegion._y2
        for i in range(recordsNum):
            sPoints = shpPolygons[i].points
            sCurrentXmin = sPoints[0][0]
            sCurrentXmax = sPoints[0][0]
            sCurrentYmax = sPoints[0][1]
            sCurrentYmin = sPoints[0][1]
            for j in range(1, len(sPoints)):
                sCurrentX = sPoints[j][0]
                sCurrentY = sPoints[j][1]
                if(sCurrentX < sCurrentXmin):
                    sCurrentXmin = sCurrentX
                elif(sCurrentX > sCurrentXmax):
                    sCurrentXmax = sCurrentX
                if(sCurrentY < sCurrentYmin):
                    sCurrentYmin = sCurrentY
                elif(sCurrentY > sCurrentYmax):
                    sCurrentYmax = sCurrentY
            sInRegion = 1
            if((sCurrentXmin > sXmax) or (sCurrentXmax < sXmin)):
                sInRegion = 0
            elif((sCurrentYmin > sYmax) or (sCurrentYmax < sYmin)):
                sInRegion = 0
            if(sInRegion):
                sIdList.append(i)
        return sIdList

    def CroppingUsingTargetRegion(self, shpPolygons, idList, ZList, targetRegionRect):
        sRegionPolygon = targetRegionRect.Convert2Polygon()
        for i in range(len(idList)):
            sCurrentPolygon = Polygon(shpPolygons[idList[i]].points)
            sIntersection = sRegionPolygon.intersection(sCurrentPolygon)
            if(sIntersection.geom_type == "Polygon"):
                sBuilding = Building(sIntersection, ZList[i])
                self._BuildingsList.append(sBuilding)
            else: #MultiPolygon
                for j in range(len(sIntersection.geoms)):
                    sBuilding = Building(sIntersection.geoms[j], ZList[i])
                    self._BuildingsList.append(sBuilding)

if __name__ == "__main__":
    start_time = time.time()
    
    targetRegion = Rectangle(486796, 4425988, 487679, 4426941)
    shpFilePath = "../data/Beijing_Buildings_DWG-Polygon.shp"
    myArea = Area(shpFilePath, targetRegion)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"执行时间为：{elapsed_time}秒")