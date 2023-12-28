import numpy as np
import torch
from Environment import *

LEARNING_RATE = 0.0004  #学习率
space_dim = 40 # n_spaces   状态空间维度
action_dim = 27 # n_actions   动作空间维度

map_path = 'functions/DQN/PKU.tif'
datasets = gdal.Open(map_path)
map_data = datasets.ReadAsArray()

env = Environment(map_data,space_dim,action_dim,LEARNING_RATE)

if __name__ == '__main__':

    check_point_Qlocal=torch.load('functions/DQN/Qlocal_8000.pth')
    check_point_Qtarget=torch.load('functions/DQN/Qtarget_8000.pth')
    env.q_target.load_state_dict(check_point_Qtarget['model'])
    env.q_local.load_state_dict(check_point_Qlocal['model'])
    env.optim.load_state_dict(check_point_Qlocal['optimizer'])
    #真实场景运行
    pos = (23,23,4,123,231,17)
    dist = abs(pos[0]-pos[3])+abs(pos[1]-pos[4])+abs(pos[2]-pos[5])
    success_count=0   # 成功数目
    n_test=10  #测试次数
    state = env.reset_test(23,23,4,123,231,17)  #环境重置
    for i in range(n_test):
        for j in range(env.n_uav):
            #uav_track = []
            while(1):
                if env.uavs[j].done:
                    break
                action = env.get_action(FloatTensor(np.array([state[j]])) , 0.01)   #根据Q值选取动作
                next_state, reward, uav_done, info= env.step(action.item(),0)  #根据选取的动作改变状态，获取收益
                if info==1:
                    success_count += 1
                    break
                if info==2 or info==5:
                    break
                state[j] = next_state  #状态变更
    print('成功到达目的地的无人机数量%s/%s:'% (str(success_count),str(n_test*env.n_uav)))
    print('起点至终点的曼哈顿距离:',dist)
    min_track = env.uavs[0].track

    print('min_track length:',len(min_track))

    to_target = []
    for i in range(len(min_track)):
        delta = abs(min_track[i][0]-pos[3]) + abs(min_track[i][1]-pos[4]) + abs(min_track[i][2]-pos[5])
        to_target.append(delta)

    print('min_distance:',np.min(to_target))
    
    target_index = np.argmin(to_target)
    
    print('target_index:',target_index)
        
    final_track = min_track[:target_index+1]
    
    print('final_track length:',len(final_track))
        
    final_final_track = []
    same_dict = {}
    i = 0
    while(1):
        flag = False
        for j in range(i+1,len(final_track)):
            if final_track[i] == final_track[j]:
                flag = True
                same_dict[i] = j
        if flag:
            i = same_dict[i]+1
        else:
            i = i+1
        if i == len(final_track)-1:
            break
    keys = list(same_dict.keys())
    keys.sort()
    left = 0
    right = len(final_track)
    for i in range(len(keys)):
        right = keys[i]
        final_final_track += final_track[left:right+1]
        left = same_dict[right]+1
    if left < len(final_track):
        final_final_track += final_track[left:] 
    print('final_final_track lenght:',len(final_final_track))
    
    total_step = 0
    for i in range(len(final_final_track)-1):
        dx = abs(final_final_track[i][0]-final_final_track[i+1][0])
        dy = abs(final_final_track[i][1]-final_final_track[i+1][1])
        dz = abs(final_final_track[i][2]-final_final_track[i+1][2])
        if dx > 1 or dy > 1 or dz > 1:
            print('不连续')
        total_step = total_step + dx + dy + dz
    print('total_step:',total_step)       
