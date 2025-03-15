import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import IPython.display as display

# Function to count total files in a folder
def total_files(folder_path):
    return len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])

# Dataset paths
DATASET_DIR = "Dataset"
TRAIN_DIR = os.path.join(DATASET_DIR, "Train/Train")
TEST_DIR = os.path.join(DATASET_DIR, "Test/Test")
VALID_DIR = os.path.join(DATASET_DIR, "Validation/Validation")

CATEGORIES = ["Healthy", "Powdery", "Rust"]

# Print dataset details
for category in CATEGORIES:
    print(f"Number of {category} images in training set: {total_files(os.path.join(TRAIN_DIR, category))}")
    print(f"Number of {category} images in test set: {total_files(os.path.join(TEST_DIR, category))}")
    print(f"Number of {category} images in validation set: {total_files(os.path.join(VALID_DIR, category))}")
    print("========================================================")

# Display sample images
sample_images = [
    os.path.join(TRAIN_DIR, "Healthy/8ce77048e12f3dd4.jpg"),
    os.path.join(TRAIN_DIR, "Rust/80f09587dfc7988e.jpg")
]

for image_path in sample_images:
    with open(image_path, 'rb') as f:
        display.display(display.Image(data=f.read(), width=500))

# Data Augmentation & Preprocessing
train_datagen = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)
test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(TRAIN_DIR, target_size=(225, 225), batch_size=32, class_mode='categorical')
validation_generator = test_datagen.flow_from_directory(VALID_DIR, target_size=(225, 225), batch_size=32, class_mode='categorical')

# Build CNN Model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(225, 225, 3)),
    MaxPooling2D(pool_size=(2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(pool_size=(2, 2)),
    Flatten(),
    Dense(64, activation='relu'),
    Dropout(0.5),
    Dense(3, activation='softmax')
])

model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

# Train Model
history = model.fit(
    train_generator,
    batch_size=16,
    epochs=5,
    validation_data=validation_generator,
    validation_batch_size=16
)

# Plot Training Results
sns.set_theme()
sns.set_context("poster")
plt.figure(figsize=(12, 6))
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

# Save Model
model.save("model.h5")

# Image Prediction Function
def preprocess_image(image_path, target_size=(225, 225)):
    img = load_img(image_path, target_size=target_size)
    x = img_to_array(img) / 255.0
    x = np.expand_dims(x, axis=0)
    return x

# Predict Disease
image_path = os.path.join(TEST_DIR, "Rust/82f49a4a7b9585f1.jpg")
x = preprocess_image(image_path)
predictions = model.predict(x)
labels = {v: k for k, v in train_generator.class_indices.items()}
predicted_label = labels[np.argmax(predictions)]
print(f"Predicted Class: {predicted_label}")