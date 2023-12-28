import random
from collections import namedtuple
import torch
import numpy as np
use_cuda = torch.cuda.is_available()
FloatTensor = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor
device = torch.device("cuda" if use_cuda else "cpu")    #使用GPU进行训练

Transition = namedtuple('Transition', ('state', 'action', 'reward', 'next_state', 'done'))

class ReplayMemory(object):

    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
    
    def push(self, batch):
        self.memory.append(batch)
        if len(self.memory) > self.capacity:
            del self.memory[0]    
       
    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def save(self, path):
        memory_dict = {}
        for i in range(len(self.memory)):
            memory_dict[i] = self.memory[i]
        torch.save(memory_dict, path)

    def load(self,path):
        memory_dict = torch.load(path)
        self.memory=[]
        for i in range(len(memory_dict)):
            self.memory.append(memory_dict[i])

    def __len__(self):
        return len(self.memory)

if __name__ == '__main__':
    replay_memory = ReplayMemory(10000)
    replay_memory.push(
                    (FloatTensor(np.array([1.2,2.6,3.9,4.7])), 
                    FloatTensor([[19]]),
                    FloatTensor([-2.4]), 
                    FloatTensor(np.array([3.2,4.6,6.9,9.7])), 
                    FloatTensor([1])))
    
    replay_memory.push(
                    (FloatTensor(np.array([6.2,3.1,7.9,5.7])), 
                    FloatTensor([[6]]),
                    FloatTensor([-7.2]), 
                    FloatTensor(np.array([5.2,1.6,8.9,4.7])), 
                    FloatTensor([0])))
    replay_memory.save('functions/DQN/replay_test.pth')
    test = ReplayMemory(10000)
    test.load('functions/DQN/replay_test.pth')
    print(replay_memory.memory)
    print(test.memory)
