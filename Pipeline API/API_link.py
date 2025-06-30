from flask import Flask, request, jsonify, send_file
from ComfyUI_API import generate_images
import io
import os
from PIL import Image
from flask_cors import CORS
import sys

app = Flask(__name__)
CORS(app)  # Optional: allows frontend to connect from other ports

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    batch_size = int(data.get("batch_size", 1))  # default to 1
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    try:
        images_dict, seed = generate_images(prompt, batch_size)
        image_paths = []
        output_dir = get_real_path("static", "outputs")
        os.makedirs(output_dir, exist_ok=True)

        for node_id, image_datas in images_dict.items():
            for idx, image_data in enumerate(image_datas):
                img = Image.open(io.BytesIO(image_data))
                filename = f"{seed}-{idx}.png"
                filepath = os.path.join(output_dir, filename)
                img.save(filepath)
                image_paths.append(f"/static/outputs/{filename}")

        return jsonify({"images": image_paths})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/saveImage", methods=["POST"])
def save_image():
    data = request.json
    name = data.get("name")
    image_url = data.get("img")

    if not name or not image_url:
        return jsonify({"error": "Missing name or image URL"}), 400

    # Extract filename from the URL (e.g. 106-1234567890-0.png)
    filename = os.path.basename(image_url)
    source_path = get_real_path("static", "outputs", filename)

    if not os.path.exists(source_path):
        return jsonify({"error": "Image not found on server"}), 404

    # Create a folder named after the avatar
    avatar_folder = get_real_path("static", "saved_avatars", name)
    os.makedirs(avatar_folder, exist_ok=True)

    save_path = os.path.join(avatar_folder, filename)

    with open(source_path, "rb") as f_src, open(save_path, "wb") as f_dst:
        f_dst.write(f_src.read())

    return jsonify({
        "message": f"Avatar '{name}' saved successfully.",
        "saved_path": f"/static/saved_avatars/{name}/{filename}"
    })

@app.route("/listAvatars", methods=["GET"])
def list_avatars():
    base_dir = os.path.join("static", "saved_avatars")
    avatars = []

    if not os.path.exists(base_dir):
        return jsonify(avatars)

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

@app.route("/getAvatar", methods=["GET"])
def get_avatar_images():
    avatar_name = request.args.get("name")

    if not avatar_name:
        return jsonify({"error": "Missing avatar name"}), 400

    folder_path = get_real_path("static", "saved_avatars", avatar_name)

    if not os.path.exists(folder_path):
        return jsonify({"error": "Avatar folder not found"}), 404

    images = []
    for file in os.listdir(folder_path):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            images.append(f"/static/saved_avatars/{avatar_name}/{file}")

    return jsonify({
        "name": avatar_name,
        "images": images
    })

def get_real_path(*path_parts):
    """
    Resolves paths correctly whether run from source or as an executable.
    """
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, *path_parts)

@app.route("/", methods=["GET"])
def home():
    return "✅ ComfyUI_API is running!"

@app.route("/static/outputs/<filename>")
def serve_image(filename):
    return send_file(get_real_path("static", "outputs", filename))

@app.route("/static/saved_avatars/<avatar_name>/<filename>")
def serve_saved_avatar(avatar_name, filename):
    return send_file(get_real_path("static", "saved_avatars", avatar_name, filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8189, debug=True)