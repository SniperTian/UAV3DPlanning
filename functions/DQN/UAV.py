import math
import random

class UAV():
    def __init__(self, x, y, z, env):
        # 初始化无人机坐标位置
        self.x = x
        self.y = y
        self.z = z

        # 初始化无人机目标的坐标和所处环境
        self.target = [env.target[0][0], env.target[0][1], env.target[0][2]]
        self.environment = env

        #初始化运动情况
        self.direction = 0 # 水平运动方向,8种情况
        self.detect_range = 5 # 无人机探测范围 (格,每格2米)
        self.obstacles_space = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # 无人机邻近栅格内障碍物情况
        self.nearest_distance = 10 # 最近障碍物距离
        #self.obstacle_direction = None # 最近障碍物相对于无人机的方位
        self.crash_probability = 0 # 无人机坠毁概率
        self.done = False # 终止状态
        self.distance_to_target = abs(self.x-self.target[0])+abs(self.y-self.target[1])+abs(self.z-self.target[2]) # 无人机当前距离目标点曼哈顿距离
        self.distance_to_destination = abs(self.x-self.target[0])+abs(self.y-self.target[1])+abs(self.z-self.target[2]) # 无人机初始状态距离终点的曼哈顿距离
        self.step = 0 # 无人机已走步数
        self.track = [(self.x,self.y,self.z)]

    def calculate(self, num):
        # 利用动作值计算运动改变量
        if num == 0:
            return -1
        elif num == 1:
            return 0
        elif num == 2:
            return 1
        else:
            raise NotImplementedError
    
    def state(self):
        dx = self.target[0]-self.x
        dy = self.target[1]-self.y
        dz = self.target[2]-self.z
        state_grid = [self.x,self.y,self.z,dx,dy,dz,self.target[0],self.target[1],self.target[2],self.distance_to_destination,self.step,self.distance_to_target,self.direction,self.crash_probability]
        # 14
        # 更新临近栅格状态
        self.obstacles_space = []
        for i in range(-1,2):
            for j in range(-1,2):
                for k in range(-1,2):
                    if i == 0 and j == 0 and k == 0:
                        continue
                    if self.x+i<0 or self.x+i>=self.environment.width or self.y+j<0 or self.y+j>=self.environment.length or self.z+k<0 or self.z+k>=self.environment.map_height:
                        #  越界
                        self.obstacles_space.append(1) 
                        state_grid.append(1)
                    else:
                        self.obstacles_space.append(self.environment.map[self.x+i,self.y+j,self.z+k])  #添加无人机临近各个栅格状态
                        state_grid.append(self.environment.map[self.x+i,self.y+j,self.z+k])
        return state_grid

    def update(self, action):
        # 更新无人机状态
        dx, dy, dz = [0,0,0]
        temp = action
        # 相关参数
        b = 1 # 撞毁参数
        wc = 0.07 # 爬升参数
        crash = 10 # 撞毁概率惩罚增益倍数
        delta_distance = 0 # 距离终点的距离变化量

        # 计算无人机坐标变更值
        dx = self.calculate(temp%3)
        temp = int(temp/3)
        dy = self.calculate(temp%3)
        temp = int(temp/3)
        dz = self.calculate(temp)

        # 如果无人机静止不动,就给予大量惩罚
        if dx ==0 and dy == 0 and dz == 0:
            return -1000, False, False
        self.x = self.x + dx
        self.y = self.y + dy
        self.z = self.z + dz
        self.track.append((self.x,self.y,self.z))
        delta_distance = self.distance_to_target - (abs(self.x-self.target[0])+abs(self.y-self.target[1])+abs(self.z-self.target[2])) # 正代表接近目标，负代表远离目标
        self.distance_to_target = abs(self.x-self.target[0])+abs(self.y-self.target[1])+abs(self.z-self.target[2]) # 更新距离值
        self.step = self.step + abs(dx) + abs(dy) + abs(dz)

        flag = 1
        if abs(dy) == dy:
            flag = 1
        else:
            flag = -1
        
        if dx*dx + dy*dy != 0:
           self.direction = math.acos(dx/math.sqrt(dx*dx+dy*dy))*flag # 无人机速度方向(弧度)

        # 计算碰撞概率与相应奖励
        for i in range(-2,3):
            for j in range(-2,3):
                if i == 0 and j == 0:
                    continue # 排除无人机所在点
                if self.x+i<0 or self.x+i>=self.environment.width or self.y+j<0 or self.y+j>=self.environment.length or self.z<0 or self.z>=self.environment.map_height:
                        continue # 超出边界,忽略
                if self.environment.map[self.x+i,self.y+j,self.z]==1 and abs(i)+abs(j)<self.nearest_distance:
                    self.nearest_distance=abs(i)+abs(j)
                    flag=1
                    if abs(j)==-j:
                        flag=-1
                    self.obstacle_direction = math.acos(i/(i*i+j*j))*flag  #障碍物相对于无人机方向
        # 计算坠毁概率
        if self.nearest_distance>=4:
            self.crash_probability=0
        else:
            # 根据公式计算撞毁概率,此为原公式中环境风速为0的情况
            self.crash_probability=math.exp(-b*self.nearest_distance)

        # 计算爬升奖励
        r_climb = -wc*(abs(self.z-self.target[2]))

        # 计算目标奖励
        if self.distance_to_target>1:
            r_target=4*(self.distance_to_destination/self.distance_to_target)*delta_distance                #奖励函数3越接近目标，奖励越大
        else:
            r_target=4*(self.distance_to_destination)*delta_distance



        # 计算总奖励
        r = r_climb + r_target - crash * self.crash_probability

        # 终止状态判断
        if self.x<=0 or self.x>=self.environment.width-1 or self.y<=0 or self.y>=self.environment.length-1 or self.z<=0 or self.z>=self.environment.map_height-1 or self.environment.map[self.x,self.y,self.z]==1 or random.random()<self.crash_probability:
            #发生碰撞，产生巨大惩罚
            return r-400,True,2
        if self.distance_to_target <= 5:
            #到达目标点，给予f大量奖励
            r_step = self.step - self.distance_to_destination
            return r+500-r_step,True,1
        if self.step>=self.distance_to_destination+2*self.environment.map_height:
            #步数超过最差步长，给予惩罚
            return r-100,True,5
        return r,False,4