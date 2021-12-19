from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Flatten, Activation
from keras.layers.convolutional import Conv2D, MaxPooling2D
import keras
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image
from keras.preprocessing.image import img_to_array
# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
import pickle
import face_recognition as fr
from flask import jsonify, request, current_app, url_for
from . import api
import uuid
from PIL import Image
from io import BytesIO
import base64


# Model saved with Keras model.save()
MODEL_PATH = 'models/face_rank_model.h5'


# Load your trained model
# model=make_network()
# model.load_weights (MODEL_PATH)
model = load_model(MODEL_PATH)
model.summary()
model._make_predict_function()          # Necessary
print('Model loaded. Start serving...')


def model_predict(img_path, model):

    # Preprocessing the image
    image = fr.load_image_file(img_path)
    encs = fr.face_encodings(image)
    # if len(encs) != 1:
    #     print("Find %d faces in %s" % (len(encs), img_path))
    #     continue

    # Be careful how your trained model deals with the input
    # otherwise, it won't make correct prediction!
    # x = preprocess_input(x, mode='caffe')  wozhushidiaole

    preds = model.predict(np.array(encs))
    print(type(preds))
    return preds


@api.route('/ai', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')

# 以form data 上传
# @api.route('/ai/predict', methods=['GET', 'POST'])
# def upload():
#     if request.method == 'POST':
#         # Get the file from post request
#         f = request.files['file']
    name, ext = os.path.splitext(f.filename)
#         # Save the file to ./uploads
#         basepath = os.path.dirname(__file__)
#         file_path = os.path.join(
#             basepath, 'uploads', uuid.uuid4().hex+ext)
#         f.save(file_path)

#         # Make prediction
#         preds = model_predict(file_path, model)
#         # preds=model_predict("C://l/c1.jpg",model)
#         print(preds[0])

#         t = round(preds[0][0]*2, 3)
#         print('t', t)
#         print(type(t))

#         return jsonify({
#             'rank': t
#         })
#     return None

# 以base 64 格式上传


@api.route('/ai/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request

        data = request.form.get('image')
        filename = request.form.get('filename')
        name, ext = os.path.splitext(filename)
        im = Image.open(BytesIO(base64.b64decode(data)))
        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', uuid.uuid4().hex+ext)
        im.save(file_path)

        # Make prediction
        preds = model_predict(file_path, model)
        # preds=model_predict("C://l/c1.jpg",model)
        print(preds[0])

        t = round(preds[0][0]*2, 3)
        print('t', t)
        print(type(t))

        return jsonify({
            'rank': t
        })
    return None
