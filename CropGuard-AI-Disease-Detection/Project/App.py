from flask import Flask, render_template, request
import os
import cv2
from tensorflow.keras.models import load_model
app = Flask(__name__)
MODEL_PATH = "CropGuard-AI-Disease-Detection/Project/model.h5"
model = load_model(MODEL_PATH)
