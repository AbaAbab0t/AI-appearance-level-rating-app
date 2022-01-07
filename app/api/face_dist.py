import numpy as np

def calc_dist(a, b):
    '''
    计算欧式距离
    param: a, b 两个向量np.array
    return: 欧式距离
    '''
    # dist = np.sqrt(np.sum(np.square(a - b)))
    return np.linalg.norm(a-b)


def calc_cos(a, b):
    '''
    计算余弦相似度
    param: a, b 两个向量np.array
    return: 相似度
    '''
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 归一化


def sim_dist(a, b):
    return 1/(1+calc_dist(a, b))


def sim_cos(a, b):
    sim = 0.5+0.5*calc_cos(a, b)
    return sim