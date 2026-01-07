from load_data import load_images
DATASET_PATH = "/Users/mac/AID103-kuldeepsingh8949/CropGuard-AI-Disease-Detection/plantvillage dataset/color"

X, y, classes = load_images(
    DATASET_PATH,
    max_images_per_class=50
)

print("Images shape:", X.shape)
print("Labels shape:", y.shape)
print("Classes:", classes)

X, y, classes = load_images(
    DATASET_PATH,
    max_images_per_class=50
)

print("Images shape:", X.shape)
print("Labels shape:", y.shape)
print("Classes:", classes)