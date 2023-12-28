import numpy as np
import random
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import torch
import torch.optim as optim
from  torch.autograd import Variable
#from replay_buffer import ReplayMemory, Transitio
from UAV import *
from model import QNetwork
from osgeo import gdal
from ReplayBuffer import ReplayMemory, Transition

use_cuda = torch.cuda.is_available()
FloatTensor = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor
device = torch.device("cuda" if use_cuda else "cpu")    #使用GPU进行训练

class Environment(object):
    def __init__(self, map, n_states, n_actions, LEARNING_RATE):
        self.map_data = map
        self.width = map.shape[0]
        self.length = map.shape[1]
        self.max_height = int(np.max(map))
        self.map_height = self.max_height + 5
        self.map = np.zeros((self.width,self.length,self.map_height))
        for i in range(self.width):
            for j in range(self.length):
                for k in range(int(self.map_data[i][j])+1):
                    self.map[i,j,k]=1
        self.uavs = []
        self.target = []
        self.n_uav = 14
        

        #神经网络参数
        self.q_local = QNetwork(n_states, n_actions, hidden_dim=16).to(device)   #初始化Q网络
        self.q_target = QNetwork(n_states, n_actions, hidden_dim=16).to(device)   #初始化目标Q网络
        self.mse_loss = torch.nn.MSELoss()     #损失函数：均方误差
        self.optim = optim.Adam(self.q_local.parameters(), lr=LEARNING_RATE)   #设置优化器，使用adam优化器
        self.n_states = n_states     #状态空间数目
        self.n_actions = n_actions    #动作集数目
        self.replay_memory = ReplayMemory(10000)   #初o始化经验池

    def get_action(self, state, eps, check_eps=True):
        global steps_done
        sample = random.random()

        if check_eps==False or sample > eps:
            with torch.no_grad():
                return self.q_local(Variable(state).type(FloatTensor)).data.max(1)[1].view(1, 1)   #根据Q值选择行为
        else:
           return torch.tensor([[random.randrange(self.n_actions)]], device=device)   #随机选取动作

    def learn(self, gamma, BATCH_SIZE):
        if len(self.replay_memory.memory) < BATCH_SIZE:
            return
            
        transitions = self.replay_memory.sample(BATCH_SIZE)  #获取批量经验数据
        
        batch = Transition(*zip(*transitions))
        states = torch.cat(batch.state)
        actions = torch.cat(batch.action)
        rewards = torch.cat(batch.reward)
        next_states = torch.cat(batch.next_state)
        dones = torch.cat(batch.done)
        Q_expected = self.q_local(states).gather(1, actions)     #获得Q估计值
        Q_targets_next = self.q_target(next_states).detach().max(1)[0]   #计算Q目标值估计
        Q_targets = rewards + (gamma * Q_targets_next * (1-dones))   #更新Q目标值
        self.q_local.train(mode=True)        
        self.optim.zero_grad()
        loss = self.mse_loss(Q_expected, Q_targets.unsqueeze(1))  #计算误差
        # backpropagation of loss to NN        
        loss.backward()
        self.optim.step()

    def soft_update(self, local_model, target_model, tau):
        """ tau (float): interpolation parameter"""
        #更新Q网络与Q目标网络
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau*local_param.data + (1.0-tau)*target_param.data)     
            
    def hard_update(self, local, target):
        for target_param, param in zip(target.parameters(), local.parameters()):
            target_param.data.copy_(param.data)
    
    def step(self, action,i):
        reward=0.0
        done=False
        #self.map[self.uavs[i].x,self.uavs[i].y,self.uavs[i].z]=0
        reward,done,info=self.uavs[i].update(action)  #无人机执行行为,info为是否到达目标点
        #self.map[self.uavs[i].x,self.uavs[i].y,self.uavs[i].z]=1
        next_state = self.uavs[i].state()
        return next_state,reward,done,info
    
    def reset(self):
        self.uavs = []
        # 随机生成目标点位置
        x = 0
        y = 0
        z = 0
        while (1):
            x = random.randint(0,self.width-1)
            y = random.randint(0,self.length-1)
            z = random.randint(3,self.max_height)
            if self.map[x,y,z]==0:
                break
        self.target=[(x,y,z)]

        # 随机生成无人机位置
        for i in range(self.n_uav):
            x = 0
            y = 0
            z = 0
            while (1):
                x = random.randint(0,self.width-1)
                y = random.randint(0,self.length-1)
                z = random.randint(3,self.max_height)
                if self.map[x,y,z]==0:
                    break
            self.uavs.append(UAV(x,y,z,self))
        
        # 更新无人机状态
        self.state = np.vstack([uav.state() for (_, uav) in enumerate(self.uavs)])

        return self.state
    
    def reset_test(self,uav_x,uav_y,uav_z,dest_x,dest_y,dest_z):
        self.uavs = []

        if self.map[uav_x,uav_y,uav_z]==1:
            raise Exception("Start point coincides with a building.")
        if self.map[dest_x,dest_y,dest_z]==1:
            raise Exception("Target point coincides with a building.")
        self.target=[(dest_x,dest_y,dest_z)]
        for i in range(self.n_uav):
            self.uavs.append(UAV(uav_x,uav_y,uav_z,self))
        #self.uavs.append(UAV(uav_x,uav_y,uav_z,self))
        # 更新无人机状态
        self.state = np.vstack([uav.state() for (_, uav) in enumerate(self.uavs)])

        return self.state


if __name__ == '__main__':
    map_path = 'functions/DQN/PKU.tif'
    datasets = gdal.Open(map_path)
    map_data = datasets.ReadAsArray()
    env=Environment(map_data,42,27,0.0004)
    state = env.reset()
    print(env.width)
    print(env.length)