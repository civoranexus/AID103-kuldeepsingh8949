#!/usr/bin/env python3
"""
Test script to simulate concurrent predictions
"""

import requests
import time
import threading
import os
from pathlib import Path

def test_single_prediction(image_path, prediction_id):
    """Test a single prediction"""
    print(f"🧪 Starting prediction {prediction_id} for {image_path.name}")

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            start_time = time.time()

            response = requests.post('http://localhost:8000/predict',
                                   files=files,
                                   timeout=30)

            end_time = time.time()
            duration = end_time - start_time

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ⏱️  Duration: {duration:.2f} seconds")
                    print(f"   📋 Prediction: {result['prediction']}")
                    confidence = result['confidence']
                    print(".1f")
                    return True
                else:
                    print(f"   ❌ Prediction failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False

    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout: Request took too long (>30s)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_concurrent_predictions():
    """Test multiple concurrent predictions"""
    print("🧪 Testing Concurrent Predictions")
    print("=" * 60)

    # Find test images
    uploads_dir = Path("static/uploads")
    if not uploads_dir.exists():
        print("❌ No uploads directory found")
        return

    image_files = list(uploads_dir.glob("*.jpg")) + list(uploads_dir.glob("*.jpeg")) + list(uploads_dir.glob("*.png"))

    if not image_files:
        print("❌ No test images found")
        return

    # Test with first 3 images
    test_images = image_files[:3]
    print(f"📸 Testing with {len(test_images)} images")

    # Test sequential predictions first
    print("\n🔄 Testing Sequential Predictions:")
    sequential_results = []
    for i, image_path in enumerate(test_images, 1):
        success = test_single_prediction(image_path, f"seq-{i}")
        sequential_results.append(success)
        time.sleep(0.5)  # Small delay between requests

    # Test concurrent predictions
    print("\n🔄 Testing Concurrent Predictions:")
    concurrent_results = []
    threads = []

    def run_prediction(image_path, prediction_id):
        success = test_single_prediction(image_path, prediction_id)
        concurrent_results.append(success)

    # Start concurrent threads
    for i, image_path in enumerate(test_images, 1):
        thread = threading.Thread(target=run_prediction, args=(image_path, f"conc-{i}"))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Results summary
    print("\n📊 Results Summary:")
    print(f"Sequential: {sum(sequential_results)}/{len(sequential_results)} successful")
    print(f"Concurrent: {sum(concurrent_results)}/{len(concurrent_results)} successful")

    if all(sequential_results) and all(concurrent_results):
        print("✅ All predictions successful! Multi-threading is working correctly.")
    else:
        print("❌ Some predictions failed. Check the logs above for details.")

    print("=" * 60)

if __name__ == "__main__":
    test_concurrent_predictions()