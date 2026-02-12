#!/usr/bin/env python3
"""
Batch Image Analysis for CropGuard AI
Analyze multiple images at once for bulk processing.
"""

import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import json
import glob
from datetime import datetime

def load_model_and_classes():
    """Load AI model and disease classes"""
    print("Loading CropGuard AI model...")
    model = load_model('model.h5')

    with open('class_names.json', 'r') as f:
        classes = json.load(f)

    print(f"✅ Model loaded with {len(classes)} disease classes")
    return model, classes

def preprocess_image(image_path):
    """Preprocess image for model prediction"""
    img = cv2.imread(image_path)
    if img is None:
        return None

    img = cv2.resize(img, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    return img

def predict_disease(model, classes, image_path):
    """Predict disease for a single image"""
    try:
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            return {"error": "Could not process image", "success": False}

        # Make prediction
        predictions = model.predict(processed_img, verbose=0)
        predicted_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_idx])

        predicted_class = classes[predicted_idx] if predicted_idx < len(classes) else f"Unknown_{predicted_idx}"

        # Get top 3 predictions
        top_3_indices = np.argsort(predictions[0])[-3:][::-1]
        top_3_predictions = [
            {
                "class": classes[idx] if idx < len(classes) else f"Unknown_{idx}",
                "confidence": round(float(predictions[0][idx]), 4)
            }
            for idx in top_3_indices
        ]

        return {
            "filename": os.path.basename(image_path),
            "prediction": predicted_class,
            "confidence": round(confidence, 4),
            "top_3_predictions": top_3_predictions,
            "success": True
        }

    except Exception as e:
        return {
            "filename": os.path.basename(image_path),
            "error": str(e),
            "success": False
        }

def analyze_images_batch(image_paths, output_file=None):
    """Analyze multiple images in batch"""
    print(f"🔍 Starting batch analysis of {len(image_paths)} images...")
    print("=" * 60)

    # Load model
    try:
        model, classes = load_model_and_classes()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    results = []
    successful = 0
    failed = 0

    # Process each image
    for i, image_path in enumerate(image_paths, 1):
        print(f"📷 Processing {i}/{len(image_paths)}: {os.path.basename(image_path)}")

        result = predict_disease(model, classes, image_path)
        results.append(result)

        if result.get("success"):
            successful += 1
            confidence = result.get("confidence", 0)
            prediction = result.get("prediction", "Unknown")
            print(".1f"        else:
            failed += 1
            error = result.get("error", "Unknown error")
            print(f"  ❌ Failed: {error}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 BATCH ANALYSIS COMPLETE"    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(".1f"
    if successful > 0:
        avg_confidence = sum(r.get("confidence", 0) for r in results if r.get("success")) / successful
        print(".1f"
    # Save results to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_images": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results
                }, f, indent=2)

            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

    return results

def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Batch Image Analysis for CropGuard AI')
    parser.add_argument('--input', '-i', required=True,
                       help='Input directory or file pattern (e.g., "images/*.jpg")')
    parser.add_argument('--output', '-o',
                       help='Output JSON file for results')
    parser.add_argument('--max-images', '-m', type=int,
                       help='Maximum number of images to process')

    args = parser.parse_args()

    # Find image files
    if os.path.isdir(args.input):
        # Directory provided
        image_paths = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
            image_paths.extend(glob.glob(os.path.join(args.input, ext)))
            image_paths.extend(glob.glob(os.path.join(args.input, ext.upper())))
    else:
        # File pattern provided
        image_paths = glob.glob(args.input)

    # Remove duplicates and sort
    image_paths = list(set(image_paths))
    image_paths.sort()

    if not image_paths:
        print("❌ No image files found!")
        return

    print(f"📂 Found {len(image_paths)} image files")

    # Limit number of images if specified
    if args.max_images:
        image_paths = image_paths[:args.max_images]
        print(f"📏 Limited to {len(image_paths)} images")

    # Analyze images
    results = analyze_images_batch(image_paths, args.output)

    if results:
        print(f"\n🎉 Batch analysis completed! Processed {len(results)} images.")

if __name__ == "__main__":
    main()