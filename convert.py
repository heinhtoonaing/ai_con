import os
import shutil

def reorganize_dataset(base_path):
    # Define the original and new paths
    orig_images_path = os.path.join(base_path, "images")
    orig_labels_path = os.path.join(base_path, "labels")
    new_base_path = os.path.join(base_path, "dataset_yolov10")

    # Create new dataset directory
    os.makedirs(new_base_path, exist_ok=True)

    # Only process available dataset types (train, val)
    for dtype in ["train", "val"]:  # Removed "test" since it's missing
        src_images = os.path.join(orig_images_path, dtype)
        src_labels = os.path.join(orig_labels_path, dtype)

        new_images_path = os.path.join(new_base_path, dtype, "images")
        new_labels_path = os.path.join(new_base_path, dtype, "labels")

        # Make directories
        os.makedirs(new_images_path, exist_ok=True)
        os.makedirs(new_labels_path, exist_ok=True)

        # Copy images if the folder exists
        if os.path.exists(src_images):
            for filename in os.listdir(src_images):
                shutil.copy(os.path.join(src_images, filename), new_images_path)
        else:
            print(f"Warning: Source images path '{src_images}' not found.")

        # Copy labels if the folder exists
        if os.path.exists(src_labels):
            for filename in os.listdir(src_labels):
                shutil.copy(os.path.join(src_labels, filename), new_labels_path)
        else:
            print(f"Warning: Source labels path '{src_labels}' not found.")

    print(f"Reorganized dataset available at: {new_base_path}")

# Use raw string or forward slashes to avoid escape sequence issues
reorganize_dataset(r"labelme_output\YOLODataset")
