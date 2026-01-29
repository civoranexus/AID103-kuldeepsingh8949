#!/usr/bin/env python3
"""
CropGuard AI Diagnostic Script
This script helps diagnose issues with the image analysis functionality.
"""

import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import json

def run_diagnostics():
    print("🔍 CropGuard AI Diagnostic Tool")
    print("=" * 50)

    # Check 1: File existence
    print("\n📁 Checking file existence...")
    files_to_check = ['model.h5', 'class_names.json', 'App.py']
    for file in files_to_check:
        exists = os.path.exists(file)
        size = os.path.getsize(file) if exists else 0
        print(f"  {file}: {'✅' if exists else '❌'} ({size} bytes)")
        if not exists:
            print(f"  ERROR: {file} not found!")
            return False

    # Check 2: Model loading
    print("\n🤖 Testing model loading...")
    try:
        model = load_model('model.h5')
        print("  ✅ Model loaded successfully")
        print(f"  📊 Input shape: {model.input_shape}")
        print(f"  📊 Output shape: {model.output_shape}")
    except Exception as e:
        print(f"  ❌ Model loading failed: {e}")
        return False

    # Check 3: Class names loading
    print("\n🏷️  Testing class names loading...")
    try:
        with open('class_names.json', 'r') as f:
            classes = json.load(f)
        print(f"  ✅ Classes loaded: {len(classes)} classes")
        print(f"  📋 Sample classes: {classes[:5]}")
    except Exception as e:
        print(f"  ❌ Class loading failed: {e}")
        return False

    # Check 4: OpenCV availability
    print("\n📷 Testing OpenCV...")
    try:
        test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        resized = cv2.resize(test_img, (224, 224))
        converted = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = converted.astype(np.float32) / 255.0
        batched = np.expand_dims(normalized, axis=0)
        print("  ✅ OpenCV preprocessing works")
        print(f"  📐 Final shape: {batched.shape}")
    except Exception as e:
        print(f"  ❌ OpenCV test failed: {e}")
        return False

    # Check 5: Prediction test
    print("\n🔮 Testing prediction pipeline...")
    try:
        # Create dummy image
        dummy_img = np.random.rand(1, 224, 224, 3).astype(np.float32)

        # Make prediction
        predictions = model.predict(dummy_img, verbose=0)
        predicted_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_idx])

        predicted_class = classes[predicted_idx] if predicted_idx < len(classes) else f"Unknown_{predicted_idx}"

        print("  ✅ Prediction successful")
        print(f"  🎯 Predicted: {predicted_class}")
        print(".2f")
    except Exception as e:
        print(f"  ❌ Prediction failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 ALL DIAGNOSTICS PASSED!")
    print("Your CropGuard AI system is working correctly.")
    print("\nIf you're still getting errors in the web interface:")
    print("1. Make sure the Flask server is running: python3 App.py")
    print("2. Check that you're uploading valid image files (JPG, PNG, GIF)")
    print("3. Ensure the images are not corrupted or too large")
    print("4. Try refreshing the browser and clearing cache")

    return True

if __name__ == "__main__":
    success = run_diagnostics()
    exit(0 if success else 1)