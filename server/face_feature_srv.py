# encoding:utf-8

import dlib
import numpy as np
import base64
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify
from skimage import io

app = Flask(__name__)


def get_descriptors(img):

    # 对文件夹下的每一个人脸进行:
    # 1.人脸检测
    # 2.关键点检测
    # 3.描述子提取

    # 候选人脸描述子list
    # 1.人脸检测
    dets = detector(img, 1)
    d = dets[0]
    descriptors = []
    shape = sp(img, d)

    # 3.描述子提取，128D向量
    face_descriptor = facerec.compute_face_descriptor(img, shape)

    # 转换为numpy array
    v = np.array(face_descriptor)
    descriptors.append(v)

    return v


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


def predict(descriptors, img):
    # 对需识别人脸进行同样处理
    # 提取描述子
    dets = detector(img, 1)

    dist = []
    for k, d in enumerate(dets):
        shape = sp(img, d)
        face_descriptor = facerec.compute_face_descriptor(img, shape)
        d_test = np.array(face_descriptor)

        # 计算欧式距离
        for i in descriptors:
            dist_ = np.linalg.norm(i-d_test)
            dist.append(dist_)
    return dist


def init_ai():
    global detector, sp, facerec
    # 加载正脸检测器
    dlib.DLIB_USE_CUDA=False
    detector = dlib.get_frontal_face_detector()

    # 加载人脸关键点检测器
    sp = dlib.shape_predictor("./models/shape_predictor_68_face_landmarks.dat")

    # 3. 加载人脸识别模型
    facerec = dlib.face_recognition_model_v1(
        "./models/dlib_face_recognition_resnet_model_v1.dat")


@app.route('/ai/face_feature', methods=['POST'])
def get_face_feature():
    image = request.json.get('image')
    im_64=BytesIO(base64.b64decode(image)).getvalue()
    img = Image.open(BytesIO(base64.b64decode(image)))

    desc = get_descriptors(np.array(img))

    features=desc.tolist()
    #features = [str(i) for i in desc]
    return jsonify({'face_feature': features}), 200

init_ai()
if __name__ == '__main__':
    app.run()

