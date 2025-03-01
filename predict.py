from ultralytics import YOLO

# Load a model
model = YOLO("last.pt")  # Make sure this is the correct model path

# Run inference on a single image
image_path = r"labelme_output\YOLODataset\dataset_yolov10\test\images\a2.jpg"
results = model([image_path])  # Return a list of Results objects

# Process results list
for result in results:
    boxes = result.boxes        # Bounding box outputs
    masks = result.masks        # Segmentation mask outputs
    keypoints = result.keypoints # Pose outputs
    probs = result.probs        # Classification outputs
    obb = result.obb            # Oriented bounding box outputs
    
    if boxes is not None and len(boxes) > 0:
        print(f"Detected {len(boxes)} objects.")
    else:
        print("No objects detected.")

    result.show()               # Display to screen
    result.save(filename="result.jpg")  # Save to disk
