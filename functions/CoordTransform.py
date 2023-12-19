from osgeo import osr,ogr

def UTM2WGS84(y, x, zoneNumber = 50, isNorthernHemisphere = True):
    sSourceSrs = osr.SpatialReference()
    sSourceSrs.SetUTM(zoneNumber, isNorthernHemisphere)
    sTargetSrs = osr.SpatialReference()
    sTargetSrs.ImportFromEPSG(4326)
    sTransform = osr.CoordinateTransformation(sSourceSrs, sTargetSrs)
    sPoint = ogr.Geometry(ogr.wkbPoint)
    sPoint.AddPoint(x, y)
    sPoint.Transform(sTransform)
    return sPoint.GetY(),sPoint.GetX()

#lat:纬度, lng:经度
def WGS842UTM(lng, lat, zoneNumber = 50, isNorthernHemisphere = True):
    sSourceSrs = osr.SpatialReference()
    sSourceSrs.ImportFromEPSG(4326)
    sTargetSrs = osr.SpatialReference()
    sTargetSrs.SetUTM(zoneNumber, isNorthernHemisphere)
    sTransform = osr.CoordinateTransformation(sSourceSrs, sTargetSrs)
    sPoint = ogr.Geometry(ogr.wkbPoint)
    sPoint.AddPoint(lat, lng)
    sPoint.Transform(sTransform)
    return sPoint.GetY(),sPoint.GetX()

if __name__ == "__main__":
    lng_wgs84,lat_wgs84 = 116.29932,39.98456
    lng_utm,lat_utm = WGS842UTM(lng_wgs84,lat_wgs84)
    print(lng_utm,lat_utm)
    lng_wgs84_,lat_wgs84_ = UTM2WGS84(lng_utm,lat_utm)
    print(lng_wgs84_,lat_wgs84_)
    
    