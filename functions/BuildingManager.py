import shapefile
from shapely.geometry import Polygon
from osgeo import gdal, osr, ogr
import numpy as np
import math

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

    #获取polygon的XY坐标序列(从第1个点到最后1个点)
    def GetXYCoords(self):
        sxx, syy = self._polygon.exterior.coords.xy
        return sxx.tolist()[:-1], syy.tolist()[:-1]

class Area:
    def __init__(self):
        self._buildingsList = []
        self._targetRegion = None
        self._originX = None #平移原点原来的坐标X
        self._originY = None #平移原点原来的坐标Y
        self._newTargetRegion = None #平移原点后新的测图区域
        self._newBuildingsList = [] #平移原点后的建筑序列
    
    def UpdateTargetRegion(self, originalShpFile, originalShapes, originalRecordsNum, targetRegionRect):
        self._targetRegion = targetRegionRect
        self._originX = targetRegionRect._x1
        self._originY = targetRegionRect._y1
        self._newTargetRegion = Rectangle(0, 0, targetRegionRect._x2 - targetRegionRect._x1,
                                          targetRegionRect._y2 - targetRegionRect._y1)
        sIdList = self.FindPolygonsInTargetRegion(originalShapes, originalRecordsNum, targetRegionRect)
        sZList = []
        for i in range(len(sIdList)):
            sZList.append(originalShpFile.record(sIdList[i])[6])
        self._buildingsList = []
        self._newBuildingsList = []
        self.CroppingUsingTargetRegion(originalShapes, sIdList, sZList, targetRegionRect)
        self.TranslateBuildings()

    def FindPolygonsInTargetRegion(self, shpPolygons, recordsNum, targetRegionRect):
        sIdList = []
        sXmin = targetRegionRect._x1
        sXmax = targetRegionRect._x2
        sYmin = targetRegionRect._y1
        sYmax = targetRegionRect._y2
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
                self._buildingsList.append(sBuilding)
            else: #MultiPolygon
                for j in range(len(sIntersection.geoms)):
                    sBuilding = Building(sIntersection.geoms[j], ZList[i])
                    self._buildingsList.append(sBuilding)

    def TranslateBuildings(self):
        for i in range(len(self._buildingsList)):
            sXList, sYList = self._buildingsList[i].GetXYCoords()
            snewXList = [item - self._originX for item in sXList]
            snewYList = [item - self._originY for item in sYList]
            snewPolygon = Polygon(zip(snewXList, snewYList))
            snewBuilding = Building(snewPolygon, self._buildingsList[i]._h)
            self._newBuildingsList.append(snewBuilding)

    def Polygon2Raster(self, resolution):
        if(len(self._buildingsList) == 0):
            raise Exception("No buildings found!")
        #(1)创建矢量图层并保存
        sTempShpFile = shapefile.Writer("./temp/tempPolygon.shp")
        sTempShpFile.field('Elevation', 'F', '19')
        for i in range(len(self._newBuildingsList)):
            sXList, sYList = self._newBuildingsList[i].GetXYCoords()
            sTempList = []
            for j in range(len(sXList)):
                sTempList.append([sXList[j], sYList[j]])
            sTempShpFile.poly([sTempList])
            sTempShpFile.record(self._newBuildingsList[i]._h)
        sTempShpFile.close()
        #(2)创建raster图层
        stxtFile = open("./temp/projection.txt")
        sprojection = stxtFile.read()
        swidth = math.ceil(self._newTargetRegion._x2 / resolution)
        sheight = math.ceil(self._newTargetRegion._y2 / resolution)
        sgeotrans = (0, resolution, 0, self._newTargetRegion._y2, 0, -resolution) #设置仿射矩阵信息
        sTempRaster = gdal.GetDriverByName('GTiff').Create(
            utf8_path = "./temp/tempRaster.tif",  #栅格地址
            xsize = swidth,  #栅格宽
            ysize = sheight,  #栅格高
            bands = 1,  #栅格波段数
            eType = gdal.GDT_Float32  #栅格数据类型
        )
        sTempRaster.SetGeoTransform(sgeotrans) #将参考栅格的仿射变换信息设置为结果栅格仿射变换信息
        sTempRaster.SetProjection(sprojection) #设置投影坐标信息
        sband = sTempRaster.GetRasterBand(1)
        sband.SetNoDataValue(0) #设置背景nodata数值
        sband.FlushCache()
        #(3)矢量转栅格
        sTempShape = ogr.Open("./temp/tempPolygon.shp") #读取shp文件
        sShpLayer = sTempShape.GetLayer() #获取图层文件对象
        # 栅格化函数
        gdal.RasterizeLayer(
            dataset = sTempRaster,  # 输出的栅格数据集
            bands = [1],  # 输出波段
            layer = sShpLayer,  # 输入待转换的矢量图层
            options = [f"ATTRIBUTE={'Elevation'}"]  # 指定字段值为栅格值
        )
        sRasterData = sTempRaster.ReadAsArray(0, 0, swidth, sheight)
        del sTempRaster
        return sRasterData