import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests  # For making HTTP requests to the auth server
from flask_session import Session  # For session management

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure session
app.config["SESSION_PERMANENT"] = False  # adjust based on your needs
app.config["SESSION_TYPE"] = "filesystem"  # or "redis", "mongodb"
app.config["SECRET_KEY"] = os.urandom(24)  # VERY IMPORTANT! Use a strong random key in production. Store in environment variable!
Session(app)

# Define upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load trained model
model = load_model('model.h5')

# Class labels
labels = {0: 'Healthy', 1: 'Powdery', 2: 'Rust'}

# Disease information dictionary
disease_info = {
    "Healthy": {
        "description": "The plant is healthy with no visible disease symptoms.",
        "prevention": "Continue regular maintenance, provide adequate sunlight, and avoid overwatering."
    },
    "Powdery": {
        "description": "Powdery mildew appears as white powdery spots on leaves and stems, caused by fungal infection.",
        "prevention": "Improve air circulation, avoid overhead watering, and use fungicides if necessary."
    },
    "Rust": {
        "description": "Rust disease causes orange or reddish-brown spots on leaves, weakening the plant.",
        "prevention": "Remove infected leaves, apply appropriate fungicides, and keep foliage dry to prevent fungal spread."
    }
}

# Image preprocessing function
def preprocess_image(image_path, target_size=(225, 225)):
    img = load_img(image_path, target_size=target_size)
    img_array = img_to_array(img) / 255.0  # Normalize
    img_array = np.expand_dims(img_array, axis=0)  # Expand dims for model
    return img_array

# Prediction function
def get_prediction(image_path):
    img_array = preprocess_image(image_path)
    predictions = model.predict(img_array)[0]
    predicted_label = labels[np.argmax(predictions)]
    return predicted_label

# Authentication check
def is_logged_in():
    return session.get("logged_in")  # Check if 'logged_in' is in the session

# Route to serve login.html
@app.route('/login')
def login():
    return render_template('login.html')  # Serves your existing login.html

# Protected index route
@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('index.html')  # Serves your existing index.html

# Route to handle login and verify token
@app.route('/verify_token', methods=['POST'])
def verify_token():
    token = request.form.get('token')  # Get the token from the request

    # Verify the token with the Node.js server
    auth_server_url = 'http://localhost:5001/profile'  # Replace with your Node.js server URL
    headers = {'Authorization': f'Bearer {token}'}

    try:
        response = requests.get(auth_server_url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        user_data = response.json()
        session["logged_in"] = True  # Set session variable upon successful verification
        return jsonify({'status': 'success', 'message': 'Token verified', 'user': user_data}) # include user data

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with auth server: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid token or server error'}), 401

# Prediction endpoint
@app.route('/predict', methods=['POST'])
def predict():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        predicted_label = get_prediction(file_path)
        # Get additional disease details
        disease_details = disease_info.get(predicted_label, {})
        return jsonify({
            'prediction': predicted_label,
            'description': disease_details.get('description', 'No description available'),
            'prevention': disease_details.get('prevention', 'No prevention tips available')
        })

# Logout route
@app.route("/logout")
def logout():
    session["logged_in"] = False
    return redirect(url_for("login"))

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000) # Ensure Flask runs on a different port
