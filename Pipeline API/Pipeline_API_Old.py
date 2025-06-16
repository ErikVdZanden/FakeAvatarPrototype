from flask import Flask, request, jsonify
import requests
import json
import time

COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_FILE = "pipeline_31_05_2025_Erik.json"  # Path to your saved workflow

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Load base workflow from file
        with open(WORKFLOW_FILE, "r") as f:
            workflow = json.load(f)

        request_data = request.json or {}

        # Modify workflow with provided inputs
        for node in workflow.get("prompt", {}).values():
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = request_data.get("seed", node["inputs"].get("seed", 1234))
            if "positive" in node["inputs"]:
                node["inputs"]["positive"] = request_data.get("positive", node["inputs"]["positive"])
            if "negative" in node["inputs"]:
                node["inputs"]["negative"] = request_data.get("negative", node["inputs"]["negative"])

        # Send workflow to ComfyUI
        response = requests.post(f"{COMFY_URL}/prompt", json=workflow)
        if response.status_code != 200:
            return jsonify({"error": "Failed to send to ComfyUI", "details": response.text}), 500

        prompt_response = response.json()

        # Collect output filenames
        output_images = []
        for node_id, outputs in prompt_response.get("outputs", {}).items():
            for image in outputs.get("images", []):
                image_path = image.get("filename", "unknown")
                output_images.append(image_path)

        return jsonify({"status": "success", "images": output_images})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify if the service is running."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)

    # #Test image generation on startup

    # def test_generate_image():
    #     test_payload = {
    #         "seed": 42,
    #         "positive": "A test image of a 10-year old boy with brown hair, smiling",
    #         "negative": ""
    #     }
    #     try:
    #         time.sleep(1)  # Give Flask a moment to start
    #         resp = requests.post("http://127.0.0.1:5001/generate", json=test_payload)
    #         print("Test image generation response:", resp.json())
    #     except Exception as e:
    #         print("Test image generation failed:", e)

    # test_generate_image()
    