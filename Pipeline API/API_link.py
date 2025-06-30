from flask import Flask, request, jsonify, send_file
from ComfyUI_API import generate_images
import io
import os
from PIL import Image
from flask_cors import CORS
import sys

# Initialize Flask app
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Endpoint: /generate (POST)
# Generates images using ComfyUI_API with a given prompt and batch size
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    batch_size = int(data.get("batch_size", 1))  # default to 1
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    try:
        # Generate images and get seed used
        images_dict, seed = generate_images(prompt, batch_size)
        image_paths = []
        output_dir = get_real_path("static", "outputs")
        os.makedirs(output_dir, exist_ok=True)

        # Save each generated image to local static/outputs folder
        for node_id, image_datas in images_dict.items():
            for idx, image_data in enumerate(image_datas):
                img = Image.open(io.BytesIO(image_data))
                filename = f"{seed}-{idx}.png"
                filepath = os.path.join(output_dir, filename)
                img.save(filepath)
                image_paths.append(f"/static/outputs/{filename}")

        # Return list of image URLs
        return jsonify({"images": image_paths})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint: /saveImage (POST)
# Saves a generated image into a named avatar folder
@app.route("/saveImage", methods=["POST"])
def save_image():
    data = request.json
    name = data.get("name")          # Avatar folder name
    image_url = data.get("img")      # Image URL to save

    if not name or not image_url:
        return jsonify({"error": "Missing name or image URL"}), 400

    # Extract filename and path
    filename = os.path.basename(image_url)
    source_path = get_real_path("static", "outputs", filename)

    # Check if the source image exists
    if not os.path.exists(source_path):
        return jsonify({"error": "Image not found on server"}), 404

    # Create folder for the avatar (if it doesn't exist)
    avatar_folder = get_real_path("static", "saved_avatars", name)
    os.makedirs(avatar_folder, exist_ok=True)

    # Copy the image into the avatar folder
    save_path = os.path.join(avatar_folder, filename)
    with open(source_path, "rb") as f_src, open(save_path, "wb") as f_dst:
        f_dst.write(f_src.read())

    return jsonify({
        "message": f"Avatar '{name}' saved successfully.",
        "saved_path": f"/static/saved_avatars/{name}/{filename}"
    })

# Endpoint: /listAvatars (GET)
# Returns a list of avatar folders and one image (thumbnail) per avatar
@app.route("/listAvatars", methods=["GET"])
def list_avatars():
    base_dir = os.path.join("static", "saved_avatars")
    avatars = []

    # Check if avatar folder exists
    if not os.path.exists(base_dir):
        return jsonify(avatars)

    # List all subfolders (avatars) and pick one image as thumbnail
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    avatars.append({
                        "name": folder,
                        "image": f"/static/saved_avatars/{folder}/{file}"
                    })
                    break

    return jsonify(avatars)

# Endpoint: /getAvatar (GET)
# Returns all images saved under a specific avatar folder
@app.route("/getAvatar", methods=["GET"])
def get_avatar_images():
    avatar_name = request.args.get("name")

    if not avatar_name:
        return jsonify({"error": "Missing avatar name"}), 400

    folder_path = get_real_path("static", "saved_avatars", avatar_name)

    # Check if avatar folder exists
    if not os.path.exists(folder_path):
        return jsonify({"error": "Avatar folder not found"}), 404

    # Gather all image URLs in that folder
    images = []
    for file in os.listdir(folder_path):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            images.append(f"/static/saved_avatars/{avatar_name}/{file}")

    return jsonify({
        "name": avatar_name,
        "images": images
    })

# Helper Function: get_real_path
# Resolves file paths correctly, even when bundled as an executable
def get_real_path(*path_parts):
    if getattr(sys, 'frozen', False):
        # If bundled (e.g., with PyInstaller)
        base_path = os.path.dirname(sys.executable)
    else:
        # Normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, *path_parts)

# Endpoint: / (GET)
# Basic health check to confirm server is running
@app.route("/", methods=["GET"])
def home():
    return "✅ ComfyUI_API is running!"

# Endpoint: /static/outputs/<filename>
# Serves generated image files
@app.route("/static/outputs/<filename>")
def serve_image(filename):
    return send_file(get_real_path("static", "outputs", filename))

# Endpoint: /static/saved_avatars/<avatar_name>/<filename>
# Serves saved avatar image files
@app.route("/static/saved_avatars/<avatar_name>/<filename>")
def serve_saved_avatar(avatar_name, filename):
    return send_file(get_real_path("static", "saved_avatars", avatar_name, filename))

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8189, debug=True)
