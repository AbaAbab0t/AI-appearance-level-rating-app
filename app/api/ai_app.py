from flask.scaffold import F
import requests
import json

from flask import request, jsonify, current_app, g
from werkzeug.wrappers import response
from . import api
from ..models import FaceLandMark,FaceFeature,Recomendation, User
from .. import db,rdb0,rdb1
import os
import uuid
import datetime
from PIL import Image
from io import BytesIO
import base64
import random
import cv2
import numpy as np
from . import face_dist 
from flask_jwt_extended import jwt_required, get_jwt_identity

# 这个路由不再使用
@api.route('/ai/face_mask', methods=['POST'])
def face_mask():
    """
    Face Mask API
    """
    data = request.get_json()
    print(data)
    if data['image'] == '':
        return jsonify({'message': 'No image found'}), 400
    origin_im = Image.open(BytesIO(base64.b64decode(data['image'])))
    # fn, ext = os.path.splitext(data['filename'])
    # new_filename = str(uuid.uuid4())+ext
    # basepath = app.config['UPLOAD_FOLDER'] or os.path.dirname(__file__)
    # file_path = os.path.join(
    #     basepath, 'uploads', uuid.uuid4().hex+ext)
    # origin_im.save(file_path)
    url = current_app.config['AI_FACE_MASK_URL']
    headers = {'api-key': '24.c02ef559f6b1867aeb3a68f00e19ef8d.2592000.1641520412.282335-25303276',
               'Content-Type': 'application/json'}
    payload = {'image': data['image']}
    req = requests.post(url, headers=headers, data=json.dumps(payload))
    if req.status_code != 200:
        return jsonify({'message': 'Error in face mask detection'}), 400
    else:
        mask_image = Image.open(BytesIO(base64.b64decode(req.json()['image'])))
        # TODO combind mask_image and origin_im
        # 这个功能在face_mask_srv 里实现
        # make_image(origin_im, mask_image, req.json()['part_list'])
        return jsonify(req.json()), 200


def get_face_rank(filename):
    # url = app.config['AI_FACE_MARK_URL']
    url_detect = 'https://api-cn.faceplusplus.com/facepp/v3/detect'
    url_analyze = 'https://api-cn.faceplusplus.com/facepp/v3/face/analyze'
    api_key = 'HYP2ZwZzb7jXuflo8_fqk3cV46zRGB6q'
    api_secret = '8eGXvUPWdzG71FwSKvl87IhVIgbYvVUp'
    data = {'api_key': api_key, 'api_secret': api_secret}
    # basepath = current_app.config['UPLOAD_FOLDER'] or os.path.dirname(__file__)
    # filename = Image.open(os.path.join(basepath, 'uploads', filename))
    files = {"image_file": open(filename, "rb")}
    # response = requests.post(url_detect,  data=data,files=files)
    response = requests.post(url_detect,  data=data, files=files)
    if response.status_code != 200:
        return None
    else:
        data = response.json()
        faces_tokens = [face['face_token'] for face in data.get('faces')]
        data = {'api_key': api_key, 'api_secret': api_secret, 'return_attributes': 'gender,age,beauty',
                'face_tokens': ','.join(faces_tokens)}
        response = requests.post(url_analyze, data=data)
        if response.status_code == 200:
            faces = response.json().get('faces')
            if faces:
                attributes = faces[0].get('attributes')
                gender = attributes.get('gender').get('value')
                age = attributes.get('age').get('value')
                if gender == 'Female':
                    beauty = attributes.get('beauty').get('female_score')
                else:
                    beauty = attributes.get('beauty').get('male_score')
                return {'gender': gender, 'age': age, 'beauty': beauty}
        else:
            return None


@ api.route('/ai/face_rank', methods=['POST'])
def face_rank():
    """
    Face MARK API
    """
    data = request.get_json()
    if data.get('image', '') == '':
        return jsonify({'message': 'No image found'}), 400
    ext = data.get('type', 'jpg')
    im = BytesIO(base64.b64decode(data['image'])).getvalue()
    # Save the file to ./uploads
    basepath = current_app.config.get(
        'UPLOAD_FOLDER') or os.path.dirname(__file__)
    file_path = os.path.join(
        basepath, 'uploads', uuid.uuid4().hex+'.'+ext)
    with open(file_path, 'wb') as f:
        f.write(im)
    face_mark = get_face_rank(file_path)
    if face_mark:
        return jsonify({'message': 'Success', 'face_mark': face_mark}), 200
    else:
        return jsonify({'message': 'Error,bad request'}), 400


@ api.route('/ai/test_mask', methods=['POST'])
def test_mask():
    basepath = current_app.config['UPLOAD_FOLDER'] or os.path.dirname(__file__)
    image = Image.open(os.path.join(basepath, 'uploads', 'test_mask.jpg'))

    return jsonify({'message': 'Success', 'image': base64.b64encode(image.tobytes()).decode('utf-8')}), 200


@ api.route('/ai/test_mark', methods=['POST'])
def test_mark():
    # basepath = app.config['UPLOAD_FOLDER'] or os.path.dirname(__file__)
    # image=Image.open(os.path.join(basepath, 'uploads', 'test_mark.jpg'))

    return jsonify({'message': 'Success', 'value': random.randint(2, 9)}), 200


# 人脸关键点检测
def get_face_landmark(im):
    '''
    Get face landmark
    param im: image base64
    return: face landmark
    '''
    url = current_app.config['AI_FACE_LANDMARK_URL'] or 'http://192.168.3.238:8000/predict/face_landmark_localization'
    headers = {'Content-Type': 'application/json'}
    payload = {'images': [im]}
    req = requests.post(url, headers=headers, data=json.dumps(payload))
    if req.status_code != 200:
        return jsonify({'message': 'Error in face landmark detection'}), 400
    else:
        data = req.json()['results'].get('data')
        return jsonify({'data': data}), 200


@api.route('/ai/face_landmark', methods=['POST'])
def face_landmark():
    data = request.get_json()
    if data.get('image', '') == '':
        return jsonify({'message': 'No image found'}), 400
    ext = data.get('type', 'jpg')
    im_base64 = data.get('image')

    image = BytesIO(base64.b64decode(im_base64)).getvalue()
    # Save the file to ./uploads
    basepath = current_app.config.get(
        'UPLOAD_FOLDER') or os.path.dirname(__file__)
    file_path = os.path.join(
        basepath, 'uploads', uuid.uuid4().hex+'.'+ext)
    with open(file_path, 'wb') as f:
        f.write(image)
    face_data = get_face_landmark(im_base64)
    # TODO: Save to database
    rec = FaceLandMark()
    # rec.user_id=g.current_user.id
    rec.face_landmark = face_data
    db.session.add(rec)
    db.commit()

    return jsonify({'message': 'Success'}), 200

# 人脸合成
@api.route('/ai/face_mask_image', methods=['POST'])
def face_mask_image():
    data = request.get_json()
    if data.get('image', '') == '':
        return jsonify({'message': 'No image found'}), 400
    if data.get('part_list', '') == '':
        return jsonify({'message': 'No part list found'}), 400

    url = current_app.config['AI_FACE_MASK_IMAGE_URL'] or 'http://127.0.0.1:8000/ai/face_mask_image'
    headers = {'Content-Type': 'application/json'}

    req = requests.post(url, headers=headers, json=data)
    if req.status_code != 200:
        return jsonify({'message': 'Face changed failed'}), 400
    else:
        data = req.json().get('changed_img')
        # with open('face_mask_image.jpg', 'wb') as f:
        #     f.write(base64.b64decode(data))
        image = Image.fromarray(np.asarray(base64.b64decode(data)))
        # image.save('face_mask_image.jpg')
        return jsonify({'changed_img': data}), 200


# 人脸特征,上传头像时调用，
# TODO: 可以考虑将这个接口放到用户管理模块中
@api.route('/ai/face_feature', methods=['POST'])
@jwt_required()
def face_feature():
    data = request.get_json()
    if data.get('image', '') == '':
        return jsonify({'message': 'No image found'}), 400

    url = current_app.config['AI_FACE_FEATURE_URL'] or 'http://127.0.0.1:5000/ai/face_feature'
    headers = {'Content-Type': 'application/json'}
    user_id=get_jwt_identity()

    req = requests.post(url, headers=headers,json=data)
    if req.status_code != 200:
        return jsonify({'message': 'Error in face feature detection'}), 400
    else:
        data = req.json()
        # Save to database
        features = data.get('face_feature')
        if features:
            rec=db.session.query(FaceFeature).filter_by(user_id=user_id).first()
            if rec:
                db.session.delete(rec)
            # for feature in features:
            #     rec = FaceFeature()
            #     rec.user_id = g.current_user.id
            #     rec.face_feature = feature
            #     db.session.add(rec)
            # db.session.commit()
            rec = FaceFeature()
            rec.face_feature = json.dumps(features)
            rec.user_id = user_id
            db.session.add(rec)
            db.session.commit()

            # save face feature to redis
            rdb0.set(rec.user_id, json.dumps(features))

            # ToDo: 异步处理推荐人列表
            get_face_similarity_redis(user_id)

        return jsonify({'msg': 'Face feature saved'}), 200


# 计算两个人脸的相似度,保存到redis中
def get_face_similarity_redis(user_id):
    src=json.loads(rdb0.get(user_id))
    sims={}
    for key in rdb0.keys():
        if key != str(user_id):
            dst=json.loads(rdb0.get(key))
            sim=face_dist.sim_dist(np.array(src), np.array(dst))
            sims[key]=sim
    if not sims:
        return None
    recommands=sorted(sims.items(), key=lambda x:x[1],reverse=True)[:10]
    recommands=dict(recommands)
    # [{'user_id':sim},{'user_id2':sim2}]
    # 保存推荐人列表到rdb1
    rdb1.set(user_id, json.dumps(recommands))
    # TODO: 遍历推荐人列表的每个人，把user_id 添加到他的推荐列表中
    for id,sim in recommands.items():
        if rdb1.get(id):
            recommand=json.loads(rdb1.get(id))
            recommand[user_id]=sim
            recommand=sorted(recommand.items(), key=lambda x:x[1],reverse=True)[:10]
            recommand=dict(recommand)
            rdb1.set(id, json.dumps(recommand))
        

# 计算两个人脸的相似度,保存到db中
def get_face_similarity_db(user_id):
    src=db.Query(FaceFeature).filter_by(user_id=user_id).first()
    if src is None:
        return None
    src=src.face_feature
    sims={}
    for key in db.Query(FaceFeature).all():
        if key.user_id != user_id:
            dst=key.face_feature
            sim=face_dist.sim_dist(np.array(src), np.array(dst))
            sims[key.user_id]=sim
    recommands=sorted(sims, key=lambda x:x[1],reverse=True)[:10]
    for id,sim in recommands.items():
        rec=db.Query(Recomendation).filter_by(user_id=id).first()
        if rec is None:
            rec=Recomendation()
            rec.user_id=id
            rec.recommands=json.dumps([])
        rec.recommands=json.dumps(recommands)
        db.session.add(rec)
        db.commit()

# 上传头像，调用人脸颜值接口获取颜值，保存到数据库中，调用人脸特征接口获取相似度，保存到数据库中，计算推荐人列表
@api.route('/ai/avatar/<int:id>', methods=['POST'])
# @jwt_required()
def avatar(id):
    data = request.get_json()
    if data.get('image', '') == '':
        return jsonify({'message': 'No image found'}), 400
    ext = data.get('type', 'jpg')
    im = BytesIO(base64.b64decode(data['image'])).getvalue()
    # Save the file to ./uploads
    basepath = current_app.config.get(
        'UPLOAD_FOLDER') or os.path.dirname(__file__)
    filename=str(uuid.uuid4())+'.'+ext
    file_path = os.path.join(
        basepath, 'uploads', filename)
    with open(file_path, 'wb') as f:
        f.write(im)
    face_rank = get_face_rank(file_path)
    if face_rank is None:
        return jsonify({'message': 'No face found'}), 400
    # Save to database
    # user_id=get_jwt_identity()
    user_id = id
    rec = User.query.get_or_404(user_id)
    rec.avatar = filename
    rec.face_rank = face_rank['beauty']
    db.session.add(rec)
    db.session.commit()

    url = current_app.config['AI_FACE_FEATURE_URL'] or 'http://127.0.0.1:5000/ai/face_feature'
    headers = {'Content-Type': 'application/json'}

    req = requests.post(url, headers=headers,json=data)
    if req.status_code != 200:
        return jsonify({'message': 'Error in face feature detection'}), 400
    else:
        data = req.json()
        # Save to database
        features = data.get('face_feature')
        if features:
            rec=db.session.query(FaceFeature).filter_by(user_id=user_id).first()
            if rec:
                db.session.delete(rec)
            # for feature in features:
            #     rec = FaceFeature()
            #     rec.user_id = g.current_user.id
            #     rec.face_feature = feature
            #     db.session.add(rec)
            # db.session.commit()
            rec = FaceFeature()
            rec.face_feature = json.dumps(features)
            rec.user_id = user_id
            db.session.add(rec)
            db.session.commit()

            # save face feature to redis
            rdb0.set(user_id, json.dumps(features))

            # ToDo: 异步处理推荐人列表
            get_face_similarity_redis(user_id)
    return jsonify({'message': 'Success',
                    'rank': face_rank['beauty']}), 200