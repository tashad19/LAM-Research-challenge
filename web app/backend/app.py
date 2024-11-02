from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
import ezdxf
import base64
from scipy.interpolate import splprep, splev
import io
import os

app = Flask(__name__)
CORS(app)  # Enable CORS

def decode_image(image_data):
    nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def detect_contours_sobel(image, threshold_value):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    grad_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=5)
    grad_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=5)
    grad_magnitude = cv2.magnitude(grad_x, grad_y)
    grad_magnitude = cv2.convertScaleAbs(grad_magnitude)
    _, thresh = cv2.threshold(grad_magnitude, threshold_value, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        return max(contours, key=cv2.contourArea)
    return None

def smooth_contour(contour, smoothing_factor, curviness_factor):
    epsilon = smoothing_factor * cv2.arcLength(contour, True)
    simplified_contour = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    
    if len(simplified_contour) < 4:
        return contour
    
    tck, _ = splprep([simplified_contour[:, 0], simplified_contour[:, 1]], s=curviness_factor)
    smooth_points = splev(np.linspace(0, 1, 100), tck)
    smoothed_contour = np.vstack(smooth_points).T
    smoothed_contour = smoothed_contour.reshape(-1, 1, 2).astype(np.int32)
    
    return smoothed_contour

@app.route('/process-image', methods=['POST'])
def process_image():
    data = request.json
    image_data = data.get('image')
    threshold_value = int(data.get('thresholdValue', 245))
    smoothing_factor = float(data.get('smoothingFactor', 0.001))
    curviness_factor = float(data.get('curvinessFactor', 100000))

    image = decode_image(image_data)
    contour = detect_contours_sobel(image, threshold_value)
    if contour is None:
        return jsonify({'error': 'No contour detected'}), 400

    smoothed_contour = smooth_contour(contour, smoothing_factor, curviness_factor)
    # Convert the processed image to base64 for sending back
    preview_img = image.copy()
    cv2.drawContours(preview_img, [smoothed_contour], -1, (0, 255, 0), 2)
    _, buffer = cv2.imencode('.jpg', preview_img)
    preview_image_base64 = base64.b64encode(buffer).decode('utf-8')

    return jsonify({'processedImage': preview_image_base64, 'contour': smoothed_contour.tolist()})

@app.route('/export-dxf', methods=['POST'])
def export_dxf():
    data = request.json
    contour_data = data.get('contour')
    pixels_per_mm = float(data.get('pixelsPerMm', 1))
    scale_factor = float(data.get('scaleFactor', 0.002))

    file_path = 'contour_output.dxf'
    doc = ezdxf.new()
    msp = doc.modelspace()
    
    # Updated line to access contour points correctly
    polyline_points = [(point[0][0] / pixels_per_mm * scale_factor, point[0][1] / pixels_per_mm * scale_factor) for point in contour_data]
    
    msp.add_lwpolyline(polyline_points)
    doc.saveas(file_path)

    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
