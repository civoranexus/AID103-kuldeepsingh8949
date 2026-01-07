import os
import cv2
import numpy as np

def load_images(dataset_path, img_size=(224, 224), max_images_per_class=50):
    images = []
    labels = []
    class_names = os.listdir(dataset_path)

    for label, class_name in enumerate(class_names):
        class_path = os.path.join(dataset_path, class_name)

        if not os.path.isdir(class_path):
            continue

        count = 0
        for img_file in os.listdir(class_path):
            if count >= max_images_per_class:
                break

            img_path = os.path.join(class_path, img_file)
            img = cv2.imread(img_path)

            if img is None:
                continue

            img = cv2.resize(img, img_size)
            img = img / 255.0

            images.append(img)
            labels.append(label)
            count += 1

    return np.array(images), np.array(labels), class_names