from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename
import json
import threading
import time
import gc
import uuid
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MODEL_PATH = "model.h5"
MAX_WORKERS = 2  # Limit concurrent predictions

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables for model and class names
model = None
class_names = None
prediction_lock = threading.Lock()

def load_model_and_classes():
    """Load model and class names"""
    global model, class_names

    if model is None:
        print("Loading CropGuard model...")
        try:
            model = load_model(MODEL_PATH)
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    if class_names is None:
        try:
            with open('class_names.json', 'r') as f:
                class_names = json.load(f)
            print(f"Loaded {len(class_names)} class names")
        except FileNotFoundError:
            # Fallback class names if file doesn't exist
            class_names = [f"Class_{i}" for i in range(38)]  # PlantVillage has 38 classes
            print("Using default class names")

# Load model and classes on startup
load_model_and_classes()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Preprocess image for model prediction"""
    img = cv2.imread(image_path)
    if img is None:
        return None

    # Resize to match model input
    img = cv2.resize(img, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    return img

def predict_disease(image_path):
    """Make prediction using the loaded model"""
    try:
        # Preprocess image
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            return {"error": "Could not process image"}

        # Make prediction with thread safety
        # Use lock to prevent concurrent predictions (TensorFlow models are not fully thread-safe)
        print(f"Starting prediction for image shape: {processed_img.shape}")
        with prediction_lock:
            try:
                # Use batch_size=1 and reduce memory usage
                predictions = model.predict(processed_img, verbose=0, batch_size=1)
                print(f"Prediction completed, output shape: {predictions.shape}")
            except Exception as pred_error:
                print(f"Model prediction error: {pred_error}")
                raise pred_error

        # Clear processed image from memory
        del processed_img
        gc.collect()

        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])

        # Get class name
        predicted_class = class_names[predicted_class_idx] if predicted_class_idx < len(class_names) else f"Class_{predicted_class_idx}"

        # Get top 3 predictions for more detailed response
        top_3_indices = np.argsort(predictions[0])[-3:][::-1]
        top_3_predictions = [
            {
                "class": class_names[idx] if idx < len(class_names) else f"Class_{idx}",
                "confidence": float(predictions[0][idx])
            }
            for idx in top_3_indices
        ]

        # Clear predictions from memory
        del predictions
        gc.collect()

        return {
            "prediction": predicted_class,
            "confidence": confidence,
            "top_3_predictions": top_3_predictions,
            "success": True
        }

    except Exception as e:
        return {"error": str(e), "success": False}

def cleanup_old_files():
    """Clean up old uploaded files to free disk space"""
    try:
        current_time = time.time()
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            # Delete files older than 1 hour
            if os.path.isfile(filepath) and (current_time - os.path.getmtime(filepath)) > 3600:
                os.remove(filepath)
                print(f"Cleaned up old file: {filename}")
    except Exception as e:
        print(f"Error during cleanup: {e}")
# Flask Routes
@app.route('/')
def home():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/analyze')
def analyze():
    """Serve the analysis page"""
    return render_template('analyze.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle image upload and prediction with thread safety"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part", "success": False})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file", "success": False})

    if file and allowed_file(file.filename):
        try:
            # Generate unique filename with timestamp to prevent conflicts
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
            unique_filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_ext}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)

            # Clean up old files periodically (every 10 requests)
            if hasattr(predict, '_call_count'):
                predict._call_count += 1
            else:
                predict._call_count = 1

            if predict._call_count % 10 == 0:
                cleanup_old_files()

            # Make prediction
            print(f"Processing image: {unique_filename}")
            start_time = time.time()

            result = predict_disease(filepath)

            processing_time = time.time() - start_time
            print(f"✅ Prediction completed in {processing_time:.2f} seconds")

            # Clean up memory
            gc.collect()

            # Add image path to result for display
            if result.get("success"):
                result["image_path"] = f"/static/uploads/{unique_filename}"
                result["processing_time"] = processing_time

            # Clean up the uploaded file after a short delay (to allow display)
            # Schedule cleanup after 5 minutes
            def delayed_cleanup(file_path):
                time.sleep(300)  # 5 minutes
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Cleaned up file: {file_path}")
                except Exception as e:
                    print(f"Error cleaning up file {file_path}: {e}")
            
            cleanup_thread = threading.Thread(target=delayed_cleanup, args=(filepath,), daemon=True)
            cleanup_thread.start()

            return jsonify(result)

        except Exception as e:
            print(f"Prediction error for {unique_filename}: {str(e)}")
            # Clean up file on error
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
            return jsonify({"error": f"Prediction failed: {str(e)}", "success": False})

    return jsonify({"error": "File type not allowed", "success": False})

@app.route('/about')
def about():
    """Serve the about page"""
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "classes_loaded": class_names is not None,
        "num_classes": len(class_names) if class_names else 0
    })

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Clean up any leftover files on startup
    cleanup_old_files()
    print("🚀 Starting CropGuard AI Web Server...")
    print("🌐 Access at: http://localhost:8000")
    print("📊 Model loaded and ready for predictions")
    print("⚡ Threaded mode enabled for better performance")
    app.run(debug=False, host='0.0.0.0', port=8000, threaded=True)
