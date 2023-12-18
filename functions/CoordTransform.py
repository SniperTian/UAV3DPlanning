from osgeo import osr,ogr

def UTM2WGS84(x, y, zoneNumber = 50, isNorthernHemisphere = True):
    sSourceSrs = osr.SpatialReference()
    sSourceSrs.SetUTM(zoneNumber, isNorthernHemisphere)
    sTargetSrs = osr.SpatialReference()
    sTargetSrs.ImportFromEPSG(4326)
    sTransform = osr.CoordinateTransformation(sSourceSrs, sTargetSrs)
    sPoint = ogr.Geometry(ogr.wkbPoint)
    sPoint.AddPoint(x, y)
    sPoint.Transform(sTransform)
    return sPoint.GetX(), sPoint.GetY()

#lat:纬度, lng:经度
def WGS842UTM(lat, lng, zoneNumber = 50, isNorthernHemisphere = True):
    sSourceSrs = osr.SpatialReference()
    sSourceSrs.ImportFromEPSG(4326)
    sTargetSrs = osr.SpatialReference()
    sTargetSrs.SetUTM(zoneNumber, isNorthernHemisphere)
    sTransform = osr.CoordinateTransformation(sSourceSrs, sTargetSrs)
    sPoint = ogr.Geometry(ogr.wkbPoint)
    sPoint.AddPoint(lat, lng)
    sPoint.Transform(sTransform)
    return sPoint.GetX(), sPoint.GetY()