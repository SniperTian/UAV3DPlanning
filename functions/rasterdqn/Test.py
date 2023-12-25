import numpy as np
import torch
import matplotlib
import matplotlib.pyplot as plt
import time
from Environment import *
import torch
LEARNING_RATE = 0.00033   #学习率
num_episodes = 80000  #训练周期长度
space_dim = 42 # n_spaces   状态空间维度
action_dim = 27 # n_actions   动作空间维度
threshold = 200 
env = Environment(space_dim,action_dim,LEARNING_RATE)


if __name__ == '__main__':
    check_point_Qlocal=torch.load('Qlocal.pth')
    check_point_Qtarget=torch.load('Qtarget.pth')
    env.q_target.load_state_dict(check_point_Qtarget['model'])
    env.q_local.load_state_dict(check_point_Qlocal['model'])
    env.optim.load_state_dict(check_point_Qlocal['optimizer'])
    epoch=check_point_Qlocal['epoch']
    #真实场景运行
    state = env.reset_test()  #环境重置1
    total_reward = 0
    n_done=0
    count=0
 
    n_test=1  #测试次数
    n_creash=0   #坠毁数目
    for i in range(n_test):
        while(1):
            if env.uavs[0].done:
                #无人机已结束任务，跳过
                break
            action = env.get_action(FloatTensor(np.array([state[0]])) , 0.01)   #根据Q值选取动作
            
            next_state, reward, uav_done, info= env.step(action.item(),0)  #根据选取的动作改变状态，获取收益

            total_reward += reward  #求总收益
            #交互显示
            print(action)
            env.render()
            plt.pause(0.01)  
            if uav_done:
                break
            if info==1:
                success_count=success_count+1

            state[0] = next_state  #状态变更
        print(env.uavs[0].step)
        env.ax.scatter(env.target[0].x, env.target[0].y, env.target[0].z,c='red')
        plt.pause(100) 