import time,sys
import numpy as np
import numba

# 网页版本
# from .BuildingManager import Rectangle,Point3D
# from .DQN import Navigation

# 测试版本

sys.path.append(".")
from BuildingManager import Rectangle,Point3D
from DQN import Navigation


ImageHeight = 30
# ImageStep = ImageLength*(1-overlap)
ImageStep = 30
GroundGap = 5
VisibleThreshold = 100
MinVisualDis = 10
MaxVisualDis = 50
TurnRadius = 30
TurnEfficientCoef = 0.5

@numba.jit(nopython=True)
def dilationRaster(raster, resolution):
    length, width = raster.shape
    dilation = np.zeros((length, width), dtype=np.float32)
    r = 2*ImageHeight/resolution
    nr = int(r)

    for y in range(length):
        for x in range(width):
            h = raster[y,x]
            for ny in range(max(0,y-nr),min(length,y+nr+1)):
                for nx in range(x+1,min(width,x+nr+1)):
                    dis = r**2-(nx-x)**2-(ny-y)**2
                    if dis < 0:
                        break
                    newh = h+np.sqrt(dis)*resolution
                    if newh > dilation[ny,nx]:
                        dilation[ny,nx] = newh
                    else:
                        break
                for nx in range(x,max(0,x-nr)-1,-1):
                    dis = r**2-(nx-x)**2-(ny-y)**2
                    if dis < 0:
                        break
                    newh = h+np.sqrt(dis)*resolution
                    if newh > dilation[ny,nx]:
                        dilation[ny,nx] = newh
                    else:
                        break
    return dilation

@numba.jit(nopython=True)
def erosionRaster(raster, resolution):
    length, width = raster.shape
    maxHeight = np.max(raster)
    erosion = np.ones((length, width), dtype=np.float32)*maxHeight
    r = ImageHeight/resolution
    nr = int(r)

    for y in range(length):
        for x in range(width):
            h = raster[y,x]
            for ny in range(max(0,y-nr),min(length,y+nr+1)):
                for nx in range(x+1,min(width,x+nr+1)):
                    dis = r**2-(nx-x)**2-(ny-y)**2
                    if dis < 0:
                        break
                    newh = h-np.sqrt(dis)*resolution
                    if newh < erosion[ny,nx]:
                        erosion[ny,nx] = newh
                    else:
                        break
                for nx in range(x,max(0,x-nr)-1,-1):
                    dis = r**2-(nx-x)**2-(ny-y)**2
                    if dis < 0:
                        break
                    newh = h-np.sqrt(dis)*resolution
                    if newh < erosion[ny,nx]:
                        erosion[ny,nx] = newh
                    else:
                        break
    return erosion

# 修改视点，1.保证相邻视点高度差不能太大；2.保证最低和最高拍摄高度
def addRestriction(raster, resolution):
    pass

@numba.jit(nopython=True)
def getViewPoint(raster, resolution):
    sampleGap = int(ImageStep/resolution)
    length, width = raster.shape

    numberX = int((width-1)/sampleGap)+1
    numberY = int((length-1)/sampleGap)+1
    startI = int((width-(numberX-1)*sampleGap-1)/2)
    startJ = int((length-(numberY-1)*sampleGap-1)/2)
    vpList = []
    for i in range(numberX):
        for j in range(numberY):
            xi = startI + sampleGap*i
            yi = startJ + sampleGap*j
            h = raster[yi,xi]

            sx = max(xi - 1, 0)
            ex = min(xi + 1, width - 1)
            v1 = [(ex - sx) * resolution, 0, raster[yi, ex] - raster[yi, sx]]
            sy = max(yi - 1, 0)
            ey = min(yi + 1, length - 1)
            v2 = [0, -(ey - sy) * resolution, raster[sy, xi] - raster[sy, xi]]
            n = np.array([-v2[1] * v1[2], -v1[0] * v2[2], v1[0] * v2[1]]) # n[2] < 0
            n /= np.linalg.norm(n)

            vpList.append([xi,yi,h,n[0],n[1],n[2]])
    return vpList

@numba.jit(nopython=True)
def getGroundPoint(raster, resolution):
    sampleGap = int(GroundGap/resolution)
    length, width = raster.shape

    numberX = int((width - 1) / sampleGap) + 1
    numberY = int((length - 1) / sampleGap) + 1
    startI = int((width - (numberX - 1) * sampleGap - 1) / 2)
    startJ = int((length - (numberY - 1) * sampleGap - 1) / 2)
    vpList = []
    for i in range(numberX):
        for j in range(numberY):
            xi = startI + sampleGap * i
            yi = startJ + sampleGap * j
            h = raster[yi, xi]

            vpList.append([xi, yi, h, 0, 0, 1])
    return vpList

@numba.jit
def polygonSample(xPos, yPos, gap):
    res = []
    num = len(xPos)
    avgx = np.mean(xPos)
    avgy = np.mean(yPos)
    for i in range(num):
        j = (i+1)%num
        dx = xPos[j]-xPos[i]
        dy = yPos[j]-yPos[i]

        nx = -dy
        ny = dx
        if (xPos[i]-avgx)*nx+(yPos[i]-avgy)*ny < 0:
            nx = -nx
            ny = -ny
        l = np.sqrt(dx**2+dy**2)
        nx /= l
        ny /= l

        n = int(np.ceil(l/gap))
        dx /= n
        dy /= n
        curx = xPos[i]
        cury = yPos[i]
        res.append([curx, cury, nx, ny]) # startpoint are included
        for k in range(n-1):
            curx += dx
            cury += dy
            res.append([curx, cury, nx, ny])
    return res

def getSidePoint(area, startX, startY, stepX, stepY):
    sidePoint = []
    for building in area._buildingsList:
        xPos, yPos = building.GetXYCoords()
        h = building._h

        sample = polygonSample(np.array(xPos), np.array(yPos), GroundGap)
        num = int(np.ceil(h/GroundGap))-1 #endPoint not included
        startH = (h - num*GroundGap)/2
        hList = [startH+i*GroundGap for i in range(num+1)]
        for point in sample:
            x = (point[0]-startX)/stepX
            y = (point[1]-startY)/stepY
            for curH in hList:
                sidePoint.append([x, y, curH, point[2], point[3], 0])
    return sidePoint

@numba.jit(nopython=True)
def getInfoGain(viewPoint, groundPoint, raster, resolution):

    InfoGain = np.zeros((viewPoint.shape[0], groundPoint.shape[0]))
    for i in range(viewPoint.shape[0]):
        vp = viewPoint[i][:3]
        # projectx = vp[0]
        # projecty = vp[1]
        # normalx = projectx - vp[2]*vp[3]/vp[5]
        # normaly = projecty - vp[2]*vp[4]/vp[5]
        for j in range(groundPoint.shape[0]):
            gp = groundPoint[j][:3]
            nv = groundPoint[j][3:]
            visible = checkVisible(vp, gp, raster, resolution)
            # visible = False
            # if (gp[0]-vp[0])**2+(gp[1]-vp[1])**2 < 100**2:
            #     visible = True
            if visible:
                vec = gp-vp
                vec[:2] *= resolution
                dis = np.linalg.norm(vec)
                vec /= dis
                angle = np.abs(np.dot(vec, nv))
                dis = max(0, 1-((dis-ImageHeight)/(ImageHeight-MinVisualDis))**2)
                InfoGain[i,j] = dis * angle

    return InfoGain

@numba.jit(nopython=True)
def checkVisible(vp, gp, raster, resolution):
    dx = gp[0] - vp[0]
    dy = gp[1] - vp[1]
    if (dx**2+dy**2)*(resolution**2) > MaxVisualDis**2:
        return False
    number = int(np.ceil(max(abs(dx), abs(dy))))
    xPos = np.linspace(vp[0], gp[0], number)
    yPos = np.linspace(vp[1], gp[1], number)
    zRecord = np.linspace(vp[2], gp[2], number)
    for i in range(number-1):
        x = int(xPos[i]+0.5)
        y = int(yPos[i]+0.5)
        z = zRecord[i]
        if raster[y][x] >= z:
            return False
    return True

@numba.jit(nopython=True)
def selectViewPoint(infoGain):
    choosed = []
    counter = np.zeros(infoGain.shape[1])
    notView = [i for i in range(len(counter))]
    gain = np.sum(infoGain, axis=1)

    while len(notView) > 0:
        vp = np.argmax(gain)
        if gain[vp] < 0.5:
            break
        choosed.append(vp)

        newView = []
        for i in range(infoGain.shape[1]):
            if infoGain[vp][i] > 0:
                if counter[i] == 0:
                    notView.remove(i)
                    newView.append(i)
                counter[i] += 1
        gain -= np.sum(infoGain[:,np.array(newView)], axis=1)

    return choosed

# @numba.jit(nopython=True)
# def selectViewPoint_upgrade(infoGain):
#     sumGain = np.sum(infoGain, axis=0)
#     score = np.exp(infoGain-sumGain)
#     score = np.sum(score, axis=1)
#     threshold = np.mean(score) + 3*np.std(score)
#     index = np.where(score > threshold)[0]
#
#     choosed = list(index)
#     counter = np.zeros(infoGain.shape[1])
#
#     for i in choosed:
#         counter[np.where(infoGain[i] > 0)] += 1
#     notView = np.where(counter == 0)[0]
#     gain = np.sum(infoGain[:,notView], axis=1)
#     notView = [i for i in notView]
#
#     while len(notView) > 0:
#         vp = np.argmax(gain)
#         if gain[vp] < 0.5:
#             break
#         choosed.append(vp)
#
#         newView = []
#         for i in range(infoGain.shape[1]):
#             if infoGain[vp][i] > 0:
#                 if counter[i] == 0:
#                     notView.remove(i)
#                     newView.append(i)
#                 counter[i] += 1
#         gain -= np.sum(infoGain[:, np.array(newView)], axis=1)
#     return choosed

@numba.jit(nopython=True)
def getCost(viewPoint):
    num = len(viewPoint)
    cost = np.zeros((num,num))
    for i in range(num):
        for j in range(i+1,num):
            p1 = viewPoint[i]
            p2 = viewPoint[j]
            distance = np.linalg.norm(p1-p2)
            cost[i][j] = distance
            cost[j][i] = distance
    return cost

@numba.jit(nopython=True)
def getRotationCost(lp, p, rp):
    a = p - lp
    b = rp - p
    angle = np.arccos(np.dot(a, b)/np.linalg.norm(a)/np.linalg.norm(b))
    if angle < 0:
        raise NotImplementedError
    cost = TurnEfficientCoef*TurnRadius*angle
    return cost

@numba.jit(nopython=True)
def greedyPath(vpList, cost, start=-1):
    num = cost.shape[0]
    if start == -1:
        minxy = -1
        for i in range(num):
            xy = vpList[i][0]+vpList[i][1]
            if xy < minxy or minxy == -1:
                minxy = xy
                start = i

    path = [start]
    remain = [i for i in range(num)]
    remain.remove(start)
    while remain:
        minCost = -1
        cur = -1
        for i in remain:
            tempCost = cost[i][path[-1]]
            if len(path) > 1:
                tempCost += getRotationCost(vpList[path[-2]], vpList[path[-1]], vpList[i])
            if tempCost < minCost or minCost == -1:
                cur = i
                minCost = tempCost
        path.append(cur)
        remain.remove(cur)
    path = np.array(path)

    return path

@numba.jit(nopython=True)
def modifyPath(vpList, cost, path):
    num = len(path)
    change = 0
    for gap in range(num-2,0,-1):
        for start in range(1, num - gap):
            end = start + gap
            old_cost = 0
            new_cost = 0
            if start > 0:
                old_cost += cost[path[start - 1]][path[start]]
                new_cost += cost[path[start - 1]][path[end]]
                # if start > 1:
                #     old_cost += getRotationCost(vpList[path[start-2]], vpList[path[start-1]], vpList[path[start]])
                #     new_cost += getRotationCost(vpList[path[start-2]], vpList[path[start-1]], vpList[path[end]])
                # old_cost += getRotationCost(vpList[path[start-1]], vpList[path[start]], vpList[path[start+1]])
                # if gap > 1:
                #     new_cost += getRotationCost(vpList[path[start-1]], vpList[path[end]], vpList[path[start+1]])
                # else:
                #     new_cost += getRotationCost(vpList[path[start-1]], vpList[path[end]], vpList[path[start]])
            if end < num - 1:
                old_cost += cost[path[end]][path[end + 1]]
                new_cost += cost[path[start]][path[end + 1]]
                # if end < num - 2:
                #     old_cost += getRotationCost(vpList[path[end]], vpList[path[end+1]], vpList[path[end+2]])
                #     new_cost += getRotationCost(vpList[path[start]], vpList[path[end+1]], vpList[path[end+2]])
                # old_cost += getRotationCost(vpList[path[end-1]], vpList[path[end]], vpList[path[end+1]])
                # if gap > 1:
                #     new_cost += getRotationCost(vpList[path[end-1]], vpList[path[start]], vpList[path[end+1]])
                # else:
                #     new_cost += getRotationCost(vpList[path[end]], vpList[path[start]], vpList[path[end+1]])
            if new_cost < old_cost:
                change += 1
                path[start:end+1] = np.flip(path[start:end+1])
    return path, change

def show3D(raster, filename):
    import matplotlib.pyplot as plt

    length, width = raster.shape
    x = np.arange(width)
    y = np.arange(length)
    x,y = np.meshgrid(x,y)
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.set_zlim(0, 160)
    ax.plot_surface(x,y,raster,cmap='rainbow')
    plt.savefig(filename)

def showViewPoint(vpList):
    fp = open('raster.raw', 'rb')
    raster = np.fromfile(fp, dtype=np.float32)
    fp.close()
    raster = raster.reshape((1288, 852))

    import matplotlib.pyplot as plt
    length, width = raster.shape
    x = np.arange(width)
    y = np.arange(length)

    x, y = np.meshgrid(x, y)
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    # ax.plot_surface(x, y, raster)

    number = len(vpList)
    for i in range(number):
        vp = vpList[i]
        ax.scatter(vp[0],vp[1],vp[2])
        if vp[5] > 0:
            x = [vp[0],vp[0]-10*vp[3]]
            y = [vp[1],vp[1]-10*vp[4]]
            z = [vp[2],vp[2]-10*vp[5]]
        else:
            x = [vp[0], vp[0] + 10 * vp[3]]
            y = [vp[1], vp[1] + 10 * vp[4]]
            z = [vp[2], vp[2] + 10 * vp[5]]
        ax.plot(x,y,z)
    # plt.show()
    plt.savefig('viewPoint.jpg')

def showPoint(vpList, groundPointList):

    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = plt.axes(projection='3d')

    # number = len(vpList)
    # for i in range(number):
    #     vp = vpList[i]
    #     ax.scatter(vp[0],vp[1],vp[2], color='b')
    #     if vp[5] > 0:
    #         x = [vp[0],vp[0]-10*vp[3]]
    #         y = [vp[1],vp[1]-10*vp[4]]
    #         z = [vp[2],vp[2]-10*vp[5]]
    #     else:
    #         x = [vp[0], vp[0] + 10 * vp[3]]
    #         y = [vp[1], vp[1] + 10 * vp[4]]
    #         z = [vp[2], vp[2] + 10 * vp[5]]
    #     ax.plot(x,y,z,color='b')

    gp = np.array(groundPointList)
    print('drawing')
    ax.plot(gp[:,0],gp[:,1],gp[:,2],color='r',marker='o',ls='')
    # plt.show()
    plt.savefig('sidePoint.jpg')

def showPath(vpList, path, filename):
    num = len(vpList)
    x = np.zeros(num)
    y = np.zeros(num)
    z = np.zeros(num)
    for i in range(num):
        x[i] = vpList[path[i]][0]
        y[i] = vpList[path[i]][1]
        z[i] = vpList[path[i]][2]
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.plot(x, y, z)
    # plt.show()
    plt.savefig(filename)

def testGP(viewPoint, gp, raster, resolution):
    # print('groundPoint:', gp)
    count = 0
    distance = 0
    for i in range(viewPoint.shape[0]):
        vp = viewPoint[i][:3]
        pos = gp[:3]
        nv = gp[3:]
        # if abs(vp[0]-pos[0])<MaxVisualDis and abs(vp[1]-pos[1])<MaxVisualDis:
        #     print(vp)
        visible = checkVisible(vp, pos, raster, resolution)

        if visible:
            count += 1
            # print(i)
            # vec = pos - vp
            # vec[:2] *= resolution
            # dis = np.linalg.norm(vec)
            # vec /= dis
            # angle = np.abs(np.dot(vec, nv))
            # dis = max(0, 1 - ((dis - ImageHeight) / (ImageHeight - MinVisualDis)) ** 2)
            # score = dis * angle
            # if score == 0:
            distance += np.linalg.norm(pos-vp)
                # print(vp, 'dis=',np.linalg.norm(pos-vp))
    if count:
        distance /= count
    return count,distance

def showResult(raster, vpList, filename):
    xpos = vpList[:,0]
    ypos = vpList[:,1]
    zpos = vpList[:,2]
    import matplotlib.pyplot as plt

    length, width = raster.shape
    x = np.arange(width)
    y = np.arange(length)
    x, y = np.meshgrid(x, y)
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    # ax.plot_surface(x, y, raster, cmap='rainbow')
    ax.plot(xpos, ypos, zpos)

    angle = (90,0)
    ax.view_init(elev=angle[0],azim=angle[1])
    ax.set_title(f'elev:{angle[0]}  azim:{angle[1]}')
    plt.savefig(filename)

def AreaPathPlanning(uavRoutePlanner):
    resolution = 1
    uavRoutePlanner._resolution = resolution
    region = uavRoutePlanner._area._targetRegion
    midX = (region._x1 + region._x2) / 2
    midY = (region._y1 + region._y2) / 2
    raster = uavRoutePlanner.GetHeightRaster()
    length, width = raster.shape
    startX = midX - resolution * (width - 1) / 2
    startY = midY + resolution * (length - 1) / 2
    stepX = resolution
    stepY = -resolution

    print('sampling ground', end='')
    sidePoint = getSidePoint(uavRoutePlanner._area, startX, startY, stepX, stepY) #27393
    groundPoint = getGroundPoint(raster, resolution) #44118
    for point in sidePoint:
        groundPoint.append(point)
    groundPoint = np.array(groundPoint)
    print(': %d samples' % (len(groundPoint)))

    print('initializing view point', end='')
    surface = dilationRaster(raster, resolution)
    surface = erosionRaster(surface, resolution)
    # surface = restriction(surface)
    vpList = getViewPoint(surface, resolution)  # 1247
    vpList = np.array(vpList)
    print(': %d points' % (len(vpList)))

    print('calculating benefit')
    infoGain = getInfoGain(vpList, groundPoint, raster, resolution) #(1247,71511)

    print('selecting view point')
    vpIndex = np.array(selectViewPoint(infoGain))
    vpList = vpList[vpIndex, :3]

    print('calculating cost between every two view points')
    cost = getCost(vpList)

    print('planning connection path')
    path = greedyPath(vpList, cost)
    print('optimizing path')
    for i in range(10):
        path, change = modifyPath(vpList, cost, path)
        if change == 0:
            break

    print('generating navigation path')
    vpList = vpList[path].astype(np.int32)
    integratedPath = [Point3D(vpList[0][0], vpList[0][1], vpList[0][2])]
    for i in range(len(path)-1):
        startPoint = Point3D(vpList[i][0], vpList[i][1], vpList[i][2])
        endPoint = Point3D(vpList[i+1][0], vpList[i+1][1], vpList[i+1][2])
        res = Navigation.Navigation(raster, startPoint, endPoint)
        for p in res[1:]:
            integratedPath.append(p)

    # temp = []
    # for p in integratedPath:
    #     temp.append((p._x,p._y,p._z))
    # temp = np.array(temp)
    # showPath(temp, np.arange(temp.shape[0]), 'integratedPath.jpg')
    return integratedPath

if __name__ == '__main__':
    from UAV3DPlanning import UAV3DPlanning

    shpFilePath = "./data/PKnew.shp"
    uavRoutePlanner = UAV3DPlanning(shpFilePath)
    region = Rectangle(440180, 4426238, 441032, 4427526)
    uavRoutePlanner.SetTargetArea(region)
    AreaPathPlanning(uavRoutePlanner)

