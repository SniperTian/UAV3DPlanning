import numpy as np
import torch
from Environment import *

class Point3D:
    def __init__(self, x, y, z):
        self._x = x
        self._y = y
        self._z = z

def Navigation(raster_data,startPoint,endPoint):
    LEARNING_RATE = 0.0004
    space_dim = 40
    action_dim = 27
    env = Environment(raster_data,space_dim,action_dim,LEARNING_RATE)
    check_point_Qlocal=torch.load('functions/DQN/Qlocal_8000.pth')
    check_point_Qtarget=torch.load('functions/DQN/Qtarget_8000.pth')
    env.q_target.load_state_dict(check_point_Qtarget['model'])
    env.q_local.load_state_dict(check_point_Qlocal['model'])
    env.optim.load_state_dict(check_point_Qlocal['optimizer'])
    dist = abs(endPoint._x-startPoint._x) + abs(endPoint._y-startPoint._y) + abs(endPoint._z-startPoint._z)
    n_test = 10
    state = env.reset_test(startPoint._x,startPoint._y,startPoint._z,endPoint._x,endPoint._y,endPoint._z)
    success_count = 0
    for i in range(n_test):
        for j in range(env.n_uav):
            while(1):
                if env.uavs[j].done:
                    break
                action = env.get_action(FloatTensor(np.array([state[j]])) , 0.01)
                next_state, reward, uav_done, info= env.step(action.item(),0)
                if info==1:
                    success_count += 1
                    break
                if info==2 or info==5:
                    break
                state[j] = next_state  #状态变更
    print('成功到达目的地的无人机数量%s/%s:'% (str(success_count),str(n_test*env.n_uav)))
    print('起点至终点的曼哈顿距离:',dist)
    
    track = env.uavs[0].track

    print('track length:',len(track))

    to_target = []
    for i in range(len(track)):
        delta = abs(track[i][0]-endPoint._x) + abs(track[i][1]-endPoint._y) + abs(track[i][2]-endPoint._z)
        to_target.append(delta)

    print('min distance to target:',np.min(to_target))
    target_index = np.argmin(to_target) 
    cut_track = track[:target_index+1]
    print('cut_track length:',len(cut_track))
    final_track = []
    same_dict = {}
    i = 0
    while(1):
        flag = False
        for j in range(i+1,len(cut_track)):
            if cut_track[i] == cut_track[j]:
                flag = True
                same_dict[i] = j
        if flag:
            i = same_dict[i]+1
        else:
            i = i+1
        if i == len(cut_track)-1:
            break
    keys = list(same_dict.keys())
    keys.sort()
    left = 0
    right = len(cut_track)
    for i in range(len(keys)):
        right = keys[i]
        final_track += cut_track[left:right+1]
        left = same_dict[right]+1
    if left < len(cut_track):
        final_track += cut_track[left:] 
    print('final_track length:',len(final_track))
    
    total_step = 0
    for i in range(len(final_track)-1):
        dx = abs(final_track[i][0]-final_track[i+1][0])
        dy = abs(final_track[i][1]-final_track[i+1][1])
        dz = abs(final_track[i][2]-final_track[i+1][2])
        if dx > 1 or dy > 1 or dz > 1:
            print('不连续')
        total_step = total_step + dx + dy + dz
    print('total_step:',total_step)       

    res = []
    for i in range(len(final_track)):
        res.append(Point3D(final_track[i][0],final_track[i][1],final_track[i][2]))
    return res

if __name__ == '__main__':
    #map_path = 'functions/DQN/PKU.tif'
    map_path = 'functions/DQN/CBD.tif'
    datasets = gdal.Open(map_path)
    map_data = datasets.ReadAsArray()
    startPoint = Point3D(23,23,4)
    endPoint = Point3D(123,231,17)
    res = Navigation(map_data,startPoint,endPoint)
    print(len(res))
    print(res[0])