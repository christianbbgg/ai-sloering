from flask import Flask, render_template, request, send_from_directory, make_response, jsonify
import os
import cv2
import easyocr
import numpy as np
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

reader = easyocr.Reader(['en'])

# Face detection: både frontalt og side
face_cascade_front = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_cascade_side = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

def detect_faces(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces_front = face_cascade_front.detectMultiScale(gray, 1.1, 5)
    faces_side = face_cascade_side.detectMultiScale(gray, 1.1, 5)
    faces = list(faces_front) + list(faces_side)
    return [(x, y, x + w, y + h) for (x, y, w, h) in faces]

def pixelate(img, x1, y1, x2, y2, size=10):
    roi = img[y1:y2, x1:x2]
    if roi.size == 0:
        return img
    h, w = roi.shape[:2]
    temp = cv2.resize(roi, (max(1, w // size), max(1, h // size)), interpolation=cv2.INTER_LINEAR)
    pixelated = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
    img[y1:y2, x1:x2] = pixelated
    return img

def clean_fill(img, x1, y1, x2, y2):
    roi = img[y1:y2, x1:x2]
    avg_color = roi.mean(axis=0).mean(axis=0)
    color = tuple(map(int, avg_color))
    cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
    return img

def letter_blur(img, x1, y1, x2, y2, text, strength=10, tactical=False):
    chars = list(text)
    if not chars or (x2 - x1) <= 0:
        return img
    box_width = (x2 - x1) // len(chars)
    force = 30 if tactical else max(strength * 2, 10)
    for i in range(len(chars)):
        cx1 = x1 + i * box_width
        cx2 = cx1 + box_width
        img = pixelate(img, cx1, y1, cx2, y2, force)
    return img

def apply_method(img, x1, y1, x2, y2, method, text='', strength=10):
    if method == 'pixelate':
        return pixelate(img, x1, y1, x2, y2, strength)
    elif method == 'blur':
        k = strength if strength % 2 == 1 else strength + 1
        img[y1:y2, x1:x2] = cv2.GaussianBlur(img[y1:y2, x1:x2], (k, k), 0)
    elif method == 'hide':
        cv2.rectangle(img, (x1, y1), (x2, y2), (240, 240, 240), -1)
    elif method == 'cleanfill':
        img = clean_fill(img, x1, y1, x2, y2)
    elif method == 'text':
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), -1)
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.7
        thick = 2
        (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
        tx = x1 + ((x2 - x1 - tw) // 2)
        ty = y1 + ((y2 - y1 + th) // 2)
        cv2.putText(img, text, (tx, ty), font, scale, (0, 0, 0), thick, cv2.LINE_AA)
    elif method == 'letterblur':
        img = letter_blur(img, x1, y1, x2, y2, text, strength)
    elif method == 'tactical':
        img = pixelate(img, x1, y1, x2, y2, size=30)
    return img

def detect_text(img, return_text=False):
    results = reader.readtext(img)
    boxes = []
    for (bbox, text, _) in results:
        tl = tuple(map(int, bbox[0]))
        br = tuple(map(int, bbox[2]))
        if return_text:
            boxes.append((tl[0], tl[1], br[0], br[1], text))
        else:
            boxes.append((tl[0], tl[1], br[0], br[1]))
    return boxes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    original_filename = secure_filename(file.filename)
    timestamp = str(int(time.time()))
    filename = f"{timestamp}_{original_filename}"

    method = request.form.get('method')
    strength = int(request.form.get('strength', 10))
    text_value = request.form.get('customText', '')
    detect_faces_flag = request.form.get('detectFaces') == 'on'
    detect_plates_flag = request.form.get('detectPlates') == 'on'

    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    img = cv2.imread(path)

    if img is None:
        return jsonify({'error': 'Billedet kunne ikke indlæses'}), 400

    if detect_plates_flag:
        if method in ['letterblur', 'tactical']:
            boxes = detect_text(img, return_text=True)
            for (x1, y1, x2, y2, found_text) in boxes:
                text = found_text if method == 'letterblur' else ''
                img = apply_method(img, x1, y1, x2, y2, method, text, strength)
        else:
            for (x1, y1, x2, y2) in detect_text(img):
                img = apply_method(img, x1, y1, x2, y2, method, text_value, strength)

    if detect_faces_flag:
        for (x1, y1, x2, y2) in detect_faces(img):
            img = apply_method(img, x1, y1, x2, y2, method, text_value, strength)

    out_path = os.path.join(PROCESSED_FOLDER, filename)
    cv2.imwrite(out_path, img)
    return jsonify({'filename': filename})

@app.route('/processed/<filename>')
def processed(filename):
    resp = make_response(send_from_directory(PROCESSED_FOLDER, filename))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

if __name__ == '__main__':
    print("✅ Flask kører på: http://127.0.0.1:5000")
    app.run(debug=True)
