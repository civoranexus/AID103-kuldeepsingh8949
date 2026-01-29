#!/usr/bin/env python3
"""
Test Script for CropGuard AI System
Comprehensive testing of all system components.
"""

import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import json
import time

def test_model_loading():
    """Test AI model loading"""
    print("🧪 Testing Model Loading...")
    try:
        start_time = time.time()
        model = load_model('model.h5')
        load_time = time.time() - start_time

        print(".2f")
        print(f"   📊 Input shape: {model.input_shape}")
        print(f"   📊 Output shape: {model.output_shape}")
        return model
    except Exception as e:
        print(f"   ❌ Model loading failed: {e}")
        return None

def test_class_loading():
    """Test disease class loading"""
    print("🧪 Testing Class Loading...")
    try:
        with open('class_names.json', 'r') as f:
            classes = json.load(f)

        print(f"   ✅ Loaded {len(classes)} classes")
        print(f"   📋 Sample: {classes[:3]}...")
        return classes
    except Exception as e:
        print(f"   ❌ Class loading failed: {e}")
        return None

def test_image_processing():
    """Test image processing pipeline"""
    print("🧪 Testing Image Processing...")
    try:
        # Create test image
        test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Test resizing
        resized = cv2.resize(test_img, (224, 224))
        assert resized.shape == (224, 224, 3), "Resize failed"

        # Test color conversion
        converted = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        assert converted.shape == (224, 224, 3), "Color conversion failed"

        # Test normalization
        normalized = converted.astype(np.float32) / 255.0
        assert normalized.max() <= 1.0 and normalized.min() >= 0.0, "Normalization failed"

        # Test batch dimension
        batched = np.expand_dims(normalized, axis=0)
        assert batched.shape == (1, 224, 224, 3), "Batch dimension failed"

        print("   ✅ Image processing pipeline working")
        return batched
    except Exception as e:
        print(f"   ❌ Image processing failed: {e}")
        return None

def test_prediction(model, classes, test_image):
    """Test prediction functionality"""
    print("🧪 Testing Prediction...")
    try:
        start_time = time.time()
        predictions = model.predict(test_image, verbose=0)
        predict_time = time.time() - start_time

        print(".2f")
        print(f"   📊 Prediction shape: {predictions.shape}")

        # Test prediction results
        predicted_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_idx])

        predicted_class = classes[predicted_idx] if predicted_idx < len(classes) else f"Unknown_{predicted_idx}"

        print(".2f")
        print(f"   🎯 Predicted: {predicted_class}")

        # Test top 3 predictions
        top_3_indices = np.argsort(predictions[0])[-3:][::-1]
        top_3 = [
            {
                "class": classes[idx] if idx < len(classes) else f"Unknown_{idx}",
                "confidence": float(predictions[0][idx])
            }
            for idx in top_3_indices
        ]

        print("   📋 Top 3 predictions:")
        for i, pred in enumerate(top_3[:3], 1):
            print(".1f")

        return True
    except Exception as e:
        print(f"   ❌ Prediction failed: {e}")
        return False

def test_file_operations():
    """Test file upload and processing"""
    print("🧪 Testing File Operations...")
    try:
        # Check if uploads directory exists
        upload_dir = 'static/uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print("   📁 Created uploads directory")
        else:
            print("   📁 Uploads directory exists")

        # Test write permissions
        test_file = os.path.join(upload_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)

        print("   ✅ File operations working")
        return True
    except Exception as e:
        print(f"   ❌ File operations failed: {e}")
        return False

def run_full_test():
    """Run complete system test"""
    print("🚀 CROP GUARD AI - FULL SYSTEM TEST")
    print("=" * 50)

    # Test components
    model = test_model_loading()
    if not model:
        print("❌ SYSTEM TEST FAILED - Model loading failed")
        return False

    classes = test_class_loading()
    if not classes:
        print("❌ SYSTEM TEST FAILED - Class loading failed")
        return False

    test_image = test_image_processing()
    if test_image is None:
        print("❌ SYSTEM TEST FAILED - Image processing failed")
        return False

    prediction_success = test_prediction(model, classes, test_image)
    if not prediction_success:
        print("❌ SYSTEM TEST FAILED - Prediction failed")
        return False

    file_success = test_file_operations()
    if not file_success:
        print("❌ SYSTEM TEST FAILED - File operations failed")
        return False

    print("\n" + "=" * 50)
    print("🎉 ALL SYSTEM TESTS PASSED!")
    print("✅ CropGuard AI is fully operational")
    print("\n📋 System Status:")
    print(f"   🤖 AI Model: Loaded ({model.input_shape} → {model.output_shape})")
    print(f"   🏷️ Disease Classes: {len(classes)} categories")
    print("   📷 Image Processing: Working")
    print("   🔮 Predictions: Functional")
    print("   💾 File Operations: Ready")
    print("\n🚀 Ready for crop disease detection!")
    print("\n💡 Usage:")
    print("   🌐 Web Interface: python3 App.py")
    print("   📊 Batch Analysis: python3 batch_analyze.py --input images/ --output results.json")
    print("   🔍 Standalone Demo: Open demo.html in browser")
    print("   🩺 System Check: python3 diagnose.py")

    return True

if __name__ == "__main__":
    success = run_full_test()
    exit(0 if success else 1)