import requests
from PIL import Image, ImageDraw, ImageFont
import os
import json
import base64
import shutil

############################ Configuration #############################
BASE_URL = "http://www.prom.ddnsfree.com:8989"  # Update if needed (do not include trailing slash)
INPUT_FOLDER = "input_image"      # Folder containing images to process
FONT_PATH = "AI_Model/Fonts/THSarabunNew BoldItalic.ttf"  # Update if needed
OUTPUT_FOLDER = "labelme_output"   # Folder to store the output images and JSON annotations



username = "traco"
password = "123123"
key ="EpqptEfhurKGHCPl9iXsHcxqcyEAhZM32zcQf389c8AYyStWihN2JQQJ99BBACYeBjFXJ3w3AAALACOGPpYq"
endpoint = "https://traco.cognitiveservices.azure.com/"
type_doc = 1 # 1 for who has dataset is the partial bills
             # 2 for who has dataset is the Completed bills
########################################################################







type_dict ={1:"prebuilt-receipt", 2:"prebuilt-invoice"}
# Dictionary to store a unique color for each class
class_colors = {}

def get_color_for_class(class_name):
    """Return a fixed color for the given class name."""
    if class_name in class_colors:
        return class_colors[class_name]
    else:
        # A fixed palette of colors (RGB tuples)
        color_palette = [
            (255, 0, 0),     # red
            (0, 255, 0),     # green
            (0, 0, 255),     # blue
            (255, 255, 0),   # yellow
            (255, 0, 255),   # magenta
            (0, 255, 255),   # cyan
            (128, 0, 0),     # maroon
            (0, 128, 0),     # dark green
            (0, 0, 128),     # navy
            (128, 128, 0),   # olive
            (128, 0, 128),   # purple
            (0, 128, 128),   # teal
        ]
        # Cycle through the palette if more classes appear
        assigned_color = color_palette[len(class_colors) % len(color_palette)]
        class_colors[class_name] = assigned_color
        return assigned_color

def generate_labelme_json(image_path, shapes, image_width, image_height):
    """
    Create a LabelMe-style JSON annotation.
    
    The image data is embedded as a base64 string.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
        
    labelme_json = {
        "version": "5.0.1",
        "flags": {},
        "shapes": shapes,
        "imagePath": os.path.basename(image_path),
        "imageData": image_data,
        "imageWidth": image_width,
        "imageHeight": image_height
    }
    return labelme_json

def process_image(image_path, prediction_url, headers, font, datas):
    """
    Process a single image: send it for prediction, draw annotations,
    generate LabelMe JSON, and save outputs.
    """
    print(f"\nProcessing image: {image_path}")
    
    
    data = {
        "key": datas[0],
        "endpoint": datas[1],
        "type_doc": datas[2]
    }
    
    # === Send image for prediction ===
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            resp = requests.post(prediction_url, files=files, data=data, headers=headers)
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return
    
    if resp.status_code != 201:
        print(f"Prediction failed for {image_path}: {resp.text}")
        return
    
    predictions = resp.json().get("results", [])
    print(f"Received {len(predictions)} predictions for {os.path.basename(image_path)}")
    image_info = resp.json().get("image_info", [])
    print(image_info)

    # === Process each prediction ===
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    shapes = []  # To store shapes for LabelMe JSON
    
    
    
    
    
    for analyze_result in predictions:
        # Extract documents from analyze result
        documents = analyze_result.get('documents', [])
        
        for document in documents:
            # Extract fields from document
            fields = document.get('fields', {})
            
            def process_field(field_name, field, parent_name=""):
                # Handle array-type fields (like Items)
                if field.get('type') == 'array':
                    for idx, item in enumerate(field.get('value_array') or []):
                        if 'value_object' in item:
                            # Process array item's object fields
                            for sub_field_name, sub_field in item['value_object'].items():
                                # full_name = f"{field_name}_{idx+1}_{sub_field_name}"
                                full_name = f"{sub_field_name}"
                                process_field(full_name, sub_field)
                    return
                
                # Handle regular fields with bounding regions
                bounding_regions = field.get('bounding_regions') or []
                
                for region in bounding_regions:
                    polygon = region.get('polygon', [])
                    if len(polygon) != 8:
                        continue

                    x_coords = polygon[::2]
                    y_coords = polygon[1::2]
                    
                    x_min = min(x_coords)
                    x_max = max(x_coords)
                    y_min = min(y_coords)
                    y_max = max(y_coords)
                    
                    confidence = field.get('confidence', 0.0)
                    final_field_name = parent_name + field_name

                    # Get class color
                    color = get_color_for_class(final_field_name)

                    # Draw bounding box
                    draw.rectangle([(x_min, y_min), (x_max, y_max)], 
                                 outline=color, width=2)

                    # Draw label
                    label_text = f"{final_field_name}: {confidence:.2f}"
                    draw.text((x_min, y_min - 20), label_text, 
                             font=font, fill=color)

                    # Add to LabelMe shapes
                    shapes.append({
                        "label": final_field_name,
                        "points": [[x_min, y_min], [x_max, y_max]],
                        "group_id": None,
                        "shape_type": "rectangle",
                        "flags": {}
                    })
            
            # Process all top-level fields
            for field_name, field in fields.items():
                process_field(field_name, field)
    
    
    # === Save the image with drawn predictions (preview) ===
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_image_path = os.path.join(OUTPUT_FOLDER, base_name + "_prediction.jpg")
    image.save(output_image_path)
    print(f"Saved preview image with predictions to: {output_image_path}")
    
    # === Generate and save LabelMe JSON annotation ===
    width, height = image.size
    labelme_json = generate_labelme_json(image_path, shapes, width, height)
    json_filename = os.path.join(OUTPUT_FOLDER, base_name + ".json")
    with open(json_filename, "w") as jf:
        json.dump(labelme_json, jf, indent=4)
    print(f"Saved LabelMe annotation JSON to: {json_filename}")

    # === Copy the original image into the output folder ===
    image_copy_path = os.path.join(OUTPUT_FOLDER, os.path.basename(image_path))
    shutil.copy(image_path, image_copy_path)
    print(f"Copied original image to: {image_copy_path}")

def main():
    # === 1. Login and get token ===
    login_url = f"{BASE_URL}/login"
    credentials = {"username": username, "password": password}
    
    print("=== Logging in ===")
    resp = requests.post(login_url, json=credentials)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    access_token = resp.json().get("access_token")
    if not access_token:
        print("Access token not found in response.")
        return
    print("Login successful!\n")
    
    # === 2. Prepare output folder and prediction URL ===
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    prediction_url = f"{BASE_URL}/predictionboxMS"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Load the custom font (or fallback to default)
    try:
        font = ImageFont.truetype(FONT_PATH, size=16)
    except IOError:
        print("Warning: Custom font not found, using default.")
        font = ImageFont.load_default()
    
    # === 3. Process all images in the input folder ===
    if not os.path.exists(INPUT_FOLDER):
        print(f"Input folder '{INPUT_FOLDER}' does not exist.")
        return

    # Only process files with image extensions
    allowed_extensions = (".png", ".jpg", ".jpeg")
    image_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(allowed_extensions)]
    
    if not image_files:
        print(f"No image files found in folder '{INPUT_FOLDER}'.")
        return

    
    datas =[key, endpoint, type_dict[type_doc]]
    for image_file in image_files:
        image_path = os.path.join(INPUT_FOLDER, image_file)
        process_image(image_path, prediction_url, headers, font, datas)

if __name__ == "__main__":
    main()


