import face_recognition as fr
from flask import jsonify, request, Flask
from model import BiSeNet
from io import BytesIO
import torch
import base64

import os
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
import cv2


MODEL_PATH = './models'

app = Flask(__name__)
torch.cuda._initialized = False
# torch.cuda.empty_cache()

model_path = os.path.join(MODEL_PATH, 'face_mask.pth')
n_classes = 19
net = BiSeNet(n_classes=n_classes)
# net.cuda()
net.load_state_dict(torch.load(model_path, torch.device('cpu')))
net.eval()


def hex2rgb(hexcolor):
    '''HEX转RGB

    :param hexcolor: int or str
    :return: Tuple[int, int, int]

    >>> hex2rgb(16777215)
    (255, 255, 255)
    >>> hex2rgb('0xffffff')
    (255, 255, 255)
    '''
    hexcolor = int(hexcolor, base=16) if isinstance(
        hexcolor, str) else hexcolor
    rgb = ((hexcolor >> 16) & 0xff, (hexcolor >> 8) & 0xff, hexcolor & 0xff)
    return rgb

# cv2.imread 读取的图片是BGR格式，需要转换成RGB格式, Image.open 读取的图片是RGB格式
def makeup_image(img, mask, part, color):
    r, g, b = color
    tar_color = np.zeros_like(img)
    tar_color[:, :, 0] = r
    tar_color[:, :, 1] = g
    tar_color[:, :, 2] = b
    tar_hsv = cv2.cvtColor(tar_color, cv2.COLOR_RGB2HSV)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    img_hsv[:, :, 0:2] = tar_hsv[:, :, 0:2]
    changed=cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB)
    changed[mask != part] = img[mask != part]

    return changed

def parse_image(img):
    to_tensor = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])
    with torch.no_grad():
        image = img.resize((512, 512), Image.BILINEAR)
        img = to_tensor(image)
        img = torch.unsqueeze(img, 0)
        # img = img.cuda()
        out = net(img)[0]
        parsing = out.squeeze(0).cpu().numpy().argmax(0)
        vis_parsing_anno = parsing.copy().astype(np.uint8)
        vis_parsing_anno = cv2.resize(
            vis_parsing_anno, None, fx=1, fy=1, interpolation=cv2.INTER_NEAREST)
        return vis_parsing_anno

# get the mask image


@app.route('/ai/face_mask', methods=['POST'])
def get_face_mask():
    if request.method == 'POST':
        img = request.json.get('image')
        if img is None:
            return jsonify({
                'message': 'No image provided'
            }), 400
        image = Image.open(BytesIO(base64.b64decode(img)))
        mask_img = parse_image(image)
        # cv2.imwrite('mask.png',mask_img)

        return jsonify({'mask_img': base64.b64encode(mask_img.tobytes()).decode('utf-8')}), 200

# mask the image


@app.route('/ai/face_mask_image', methods=['POST'])
def merge_image():
    if request.method == 'POST':
        img = request.json.get('image')
        if img is None:
            return jsonify({'message': 'No image provided'}), 400
        part_list = request.json.get('part_list')
        if part_list is None:
            return jsonify({'error': 'part_list is None'}), 400
        orig_image = Image.open(BytesIO(base64.b64decode(img)))
        orig_image.save('orig.png')
        mask_image=orig_image.copy()
        
        mask = parse_image(mask_image)
        orig_image = np.array(orig_image)
        mask=cv2.resize(mask,orig_image.shape[0:2],interpolation=cv2.INTER_NEAREST)
        changed_img=orig_image.copy()
        for part, color in part_list.items():
            changed_img = makeup_image(changed_img, mask, int(part), color)
        # new=Image.fromarray(changed_img)
        # new.save('cc.png')
        # cv2.imwrite('mask.png',mask)
        # cv2.imwrite('changed.png',changed_img)

        return jsonify({'changed_img': base64.b64encode(changed_img.tobytes()).decode('utf-8')}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

