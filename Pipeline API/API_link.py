from flask import Flask, request, jsonify, send_file
from ComfyUI_API import generate_images
import io
import os
from PIL import Image
from flask_cors import CORS

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
        output_dir = "static/outputs"
        os.makedirs(output_dir, exist_ok=True)

        for node_id, image_datas in images_dict.items():
            for idx, image_data in enumerate(image_datas):
                img = Image.open(io.BytesIO(image_data))
                filename = f"{node_id}-{seed}-{idx}.png"
                filepath = os.path.join(output_dir, filename)
                img.save(filepath)
                image_paths.append(f"/static/outputs/{filename}")

        return jsonify({"images": image_paths})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ ComfyUI_API is running!"

@app.route("/static/outputs/<filename>")
def serve_image(filename):
    return send_file(os.path.join("static/outputs", filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8189, debug=True)