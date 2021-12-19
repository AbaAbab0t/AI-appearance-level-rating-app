import face_recognition as fr
from flask import jsonify, request, current_app, url_for
from . import api
import uuid
from logger import setup_logger
#from model import BiSeNet

import torch

import os
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
import cv2
from skimage.filters import gaussian


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'log'])
IMAGE_PATH = './res'
MODEL_PATH = './model'

api.config['UPLOAD_FOLDER'] = './upload'
api.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def parse_image(src_img='', respth='./res', model='model_final.pth'):
    if not os.path.exists(respth):
        os.makedirs(respth)
    n_classes = 19
    net = BiSeNet(n_classes=n_classes)
    # net.cuda()

    net.load_state_dict(torch.load(os.path.join(
        MODEL_PATH, model), torch.device('cpu')))
    net.eval()

    to_tensor = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])
    with torch.no_grad():

        img = Image.open(src_img)
        image = img.resize((512, 512), Image.BILINEAR)
        img = to_tensor(image)
        img = torch.unsqueeze(img, 0)
        # img = img.cuda()
        out = net(img)[0]
        parsing = out.squeeze(0).cpu().numpy().argmax(0)
        vis_parsing_anno = parsing.copy().astype(np.uint8)
        vis_parsing_anno = cv2.resize(
            vis_parsing_anno, None, fx=1, fy=1, interpolation=cv2.INTER_NEAREST)
        fname, fext = os.path.splitext(os.path.basename(src_img))
        cv2.imwrite(os.path.join(respth, fname +
                    '_parsing'+fext), vis_parsing_anno)


@api.route('/ai/upload/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = (file.filename)
            image = fr.load_image_file(filename)
            face_locations = fr.face_locations(image)
            # 判断是否检测到人脸
            if len(face_locations) <= 0:
                return jsonify({"result": -10})
            fn, ext = os.path.splitext(filename)
            new_filename = str(uuid.uuid4())+ext
            file.save(os.path.join(
                api.config['UPLOAD_FOLDER'], new_filename))
            # file_url = url_for('uploaded_file', filename=new_filename)
            # 图像分割存入mask目录
            parse_image(src_img=new_filename, respth='./mask',
                        model='model_final.pth')
            return jsonify({"image": new_filename})
