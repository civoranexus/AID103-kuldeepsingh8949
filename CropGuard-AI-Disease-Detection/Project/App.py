from flask import Flask, render_template, request, jsonify
import os
import traceback
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MIME_TO_EXT = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif', 'image/webp': 'webp'}
MODEL_PATH = os.path.join(BASE_DIR, "model.h5")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "class_names.json")
MAX_WORKERS = 2

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables for model and class names
model = None
class_names = None
prediction_lock = threading.Lock()

# Company profile
COMPANY_PROFILE = {
    "name": "CropGuard AI",
    "tagline": "AI-powered crop disease detection for modern agriculture.",
    "mission": "We provide cutting-edge artificial intelligence solutions for crop disease detection, helping farmers protect their crops and maximize yields.",
    "logo_path": "/static/images/logo.png",
    "contact": {
        "email": "contact@cropguard.ai",
        "phone": "+91 7350 675192",
        "location": "India",
    },
    "highlights": [
        {
            "title": "AI Technology",
            "description": "Advanced deep learning models for accurate disease detection",
        },
        {
            "title": "Fast Analysis",
            "description": "Get results in seconds with our optimized AI engine",
        },
        {
            "title": "Easy to Use",
            "description": "Simple interface accessible to farmers worldwide",
        },
    ],
}

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
            with open(CLASS_NAMES_PATH, 'r') as f:
                class_names = json.load(f)
            print(f"Loaded {len(class_names)} class names")
        except FileNotFoundError:
            # Fallback class names if file doesn't exist
            class_names = [f"Class_{i}" for i in range(38)]  # PlantVillage has 38 classes
            print("Using default class names")

# Load model and classes on startup
load_model_and_classes()

def allowed_file(filename):
    if not filename or not isinstance(filename, str):
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename, content_type=None):
    """Get valid extension from filename or content-type."""
    if filename and '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            return ext
    # Only trust content-type for known image formats
    if content_type and content_type in MIME_TO_EXT:
        return MIME_TO_EXT[content_type]
    return None  # cannot determine - caller will reject

def preprocess_image(image_path):
    """Preprocess image for model prediction"""
    img = cv2.imread(image_path)
    if img is None:
        # Fallback: try PIL for WebP or other formats OpenCV may not handle
        try:
            from PIL import Image
            pil_img = Image.open(image_path).convert('RGB')
            img = np.array(pil_img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception:
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
        # Check if image file exists and is readable
        if not os.path.exists(image_path):
            return {"error": "Image file not found", "success": False}

        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size == 0:
            return {"error": "Image file is empty", "success": False}

        # Preprocess image
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            return {"error": "Could not process image. Please ensure it's a valid image file.", "success": False}

        # Validate processed image shape
        if processed_img.shape != (1, 224, 224, 3):
            return {"error": "Image processing failed. Please try with a different image.", "success": False}

        # Make prediction with thread safety
        with prediction_lock:
            try:
                predictions = model.predict(processed_img, verbose=0, batch_size=1)
            except Exception as pred_error:
                return {"error": "AI model prediction failed. Please try again.", "success": False}

        # Validate predictions
        if predictions is None or len(predictions) == 0:
            return {"error": "No predictions received from model", "success": False}

        # Clear processed image from memory
        del processed_img
        gc.collect()

        # Get prediction results
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])

        # Validate confidence range
        if confidence < 0 or confidence > 1:
            confidence = max(0, min(1, confidence))  # Clamp to valid range

        # Get class name
        if class_names and predicted_class_idx < len(class_names):
            predicted_class = class_names[predicted_class_idx]
        else:
            predicted_class = f"Unknown_Class_{predicted_class_idx}"

        # Get top 3 predictions for more detailed response
        try:
            top_3_indices = np.argsort(predictions[0])[-3:][::-1]
            top_3_predictions = [
                {
                    "class": class_names[idx] if class_names and idx < len(class_names) else f"Unknown_{idx}",
                    "confidence": float(predictions[0][idx])
                }
                for idx in top_3_indices
            ]
        except Exception as e:
            print(f"Error getting top predictions: {e}")
            top_3_predictions = []

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
        error_str = str(e)

        # Provide specific error messages based on error type
        if "cannot identify image file" in error_str.lower():
            return {"error": "Invalid image format. Please upload a JPG, PNG, or GIF file.", "success": False}
        elif "memory" in error_str.lower():
            return {"error": "Server memory error. Please try again later.", "success": False}
        elif "shape" in error_str.lower():
            return {"error": "Image processing error. Please try with a different image.", "success": False}
        else:
            return {"error": "Prediction failed. Please try again with a different image.", "success": False}

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
    """Home page."""
    return render_template('index.html', company=COMPANY_PROFILE)

@app.route('/analyze')
def analyze():
    """AI Disease Analysis page."""
    return render_template('analyze.html', company=COMPANY_PROFILE)

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html', company=COMPANY_PROFILE)

@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html', company=COMPANY_PROFILE)

@app.route('/api/company-profile')
def company_profile():
    """Return company profile (JSON)."""
    return jsonify(COMPANY_PROFILE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "classes_loaded": class_names is not None,
        "num_classes": len(class_names) if class_names else 0
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Handle image upload and prediction"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part", "success": False})

    file = request.files['file']
    filename = file.filename or ''
    if not filename or filename.strip() == '':
        return jsonify({"error": "No selected file", "success": False})

    # Accept by extension OR by content-type (for WebP, or files with no/missing extension)
    content_type = file.content_type or ''
    file_ext = get_file_extension(filename, content_type)
    if not file_ext or file_ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File type not allowed. Please use JPG, PNG, GIF, or WebP.", "success": False})

    if file:
        filepath = None
        print(f"[PREDICT] Receiving: filename={filename}, content_type={content_type}, ext={file_ext}")
        try:
            # Generate unique filename (file_ext already determined above)
            unique_filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_ext}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Save file
            file.save(filepath)

            # Verify file was saved and is readable
            if not os.path.exists(filepath):
                return jsonify({"error": "Failed to save uploaded file", "success": False})

            # Check if model is loaded
            if model is None:
                return jsonify({"error": "AI model is not loaded. Please try again later.", "success": False})

            if class_names is None:
                return jsonify({"error": "Disease classes are not loaded. Please try again later.", "success": False})

            # Clean up old files periodically
            if hasattr(predict, '_call_count'):
                predict._call_count += 1
            else:
                predict._call_count = 1

            if predict._call_count % 10 == 0:
                cleanup_old_files()

            # Make prediction
            start_time = time.time()
            result = predict_disease(filepath)
            processing_time = time.time() - start_time

            # Log if prediction returned an error
            if not result.get("success"):
                print(f"[PREDICT] predict_disease returned error: {result.get('error', 'Unknown')}")

            # Clean up memory
            gc.collect()

            # Add image path to result for display
            if result.get("success"):
                result["image_path"] = f"/uploads/{unique_filename}"
                result["processing_time"] = round(processing_time, 2)

            # Clean up the uploaded file after a short delay
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
            error_msg = str(e)
            traceback.print_exc()  # Log full traceback for debugging

            # Clean up file on error
            try:
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass

            # Provide user-friendly error messages (include actual error for diagnosis)
            if "Cannot load OpenCV" in error_msg or "cv2" in error_msg.lower():
                return jsonify({"error": "Image processing error. Please try with a different image.", "success": False})
            elif "TensorFlow" in error_msg or "model" in error_msg.lower():
                return jsonify({"error": "AI model error. Please try again later.", "success": False})
            elif "memory" in error_msg.lower():
                return jsonify({"error": "Server memory error. Please try again later.", "success": False})
            else:
                return jsonify({"error": "An unexpected error occurred. Please try again.", "success": False})

    return jsonify({"error": "File type not allowed", "success": False})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images (separate from /static to avoid routing conflicts)"""
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Clean up any leftover files on startup
    cleanup_old_files()
    print("🌐 Access at: http://localhost:8000")
    print("📊 Model loaded and ready for predictions")
    print("⚡ Threaded mode enabled for better performance")
    app.run(debug=False, host='127.0.0.1', port=8000, threaded=True)
    # Bind to localhost and a non-privileged port; allow overrides via env vars.
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5050"))
    app.run(debug=False, host=host, port=port, threaded=True)
