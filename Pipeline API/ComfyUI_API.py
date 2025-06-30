# Import Required Libraries
import websocket  
import uuid     
import json     
import urllib.request, urllib.parse 
import random 
from PIL import Image  
import io        
from termcolor import colored  
from dotenv import load_dotenv 
import os
import sys

# Step 1: Initialize connection settings and load environment variables 
print(colored("Step 1: Initialize the connection settings and load environment variables.", "cyan"))
print(colored("Loading configuration from the .env file.", "yellow"))
load_dotenv()

# Load ComfyUI server address from .env, or default to localhost
server_address = os.getenv('COMFYUI_SERVER_ADDRESS', 'localhost:8188')
client_id = str(uuid.uuid4())  # Generate a unique client ID for this session

# Print out the current server config
print(colored(f"Server Address: {server_address}", "magenta"))
print(colored(f"Generated Client ID: {client_id}", "magenta"))

# Function: queue_prompt(prompt)
# Sends the image generation prompt to ComfyUI server via HTTP POST
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p, indent=4).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)

    print(colored(f"Step 5: Queuing the prompt for client ID {client_id}.", "cyan"))
    print(colored("Here's the JSON that will be sent:", "yellow"))
    print(colored(json.dumps(p, indent=4), "blue"))

    return json.loads(urllib.request.urlopen(req).read())

# Function: get_image(...)
# Downloads a generated image from ComfyUI server based on filename and folder
def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)

    print(colored(f"Fetching image from the server: {server_address}/view", "cyan"))
    print(colored(f"Filename: {filename}, Subfolder: {subfolder}, Type: {folder_type}", "yellow"))

    with urllib.request.urlopen(f"http://{server_address}/view?{url_values}") as response:
        return response.read()

# Function: get_history(prompt_id)
# Retrieves execution history and metadata for the given prompt ID
def get_history(prompt_id):
    print(colored(f"Fetching history for prompt ID: {prompt_id}.", "cyan"))
    with urllib.request.urlopen(f"http://{server_address}/history/{prompt_id}") as response:
        return json.loads(response.read())

# Function: get_images(ws, prompt)
# Monitors generation progress over WebSocket and retrieves final images
def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    last_reported_percentage = 0

    print(colored("Step 6: Start listening for progress updates via the WebSocket connection.", "cyan"))

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)

            if message['type'] == 'progress':
                data = message['data']
                current_progress = data['value']
                max_progress = data['max']
                percentage = int((current_progress / max_progress) * 100)

                if percentage >= last_reported_percentage + 10:
                    print(colored(f"Progress: {percentage}% in node {data['node']}", "yellow"))
                    last_reported_percentage = percentage

            elif message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    print(colored("Execution complete.", "green"))
                    break  # End of processing
        else:
            continue  # Skip if not JSON (binary previews)

    # After execution, download images from history
    print(colored("Step 7: Fetch the history and download the images after execution completes.", "cyan"))
    history = get_history(prompt_id)[prompt_id]

    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            images_output = []
            for image in node_output['images']:
                print(colored(f"Downloading image: {image['filename']} from the server.", "yellow"))
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images

# Function: get_workflow_path(filename)
# Resolves path to the workflow file whether run from source or a packaged executable
def get_workflow_path(filename="pipeline_workflow.json"):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, filename)

# Function: generate_images(...)
# Main image generation interface
def generate_images(positive_prompt, batch_size, steps=30, resolution=(512, 512)):
    # Step 3: Connect to ComfyUI WebSocket for real-time updates
    ws = websocket.WebSocket()
    ws_url = f"ws://{server_address}/ws?clientId={client_id}"
    print(colored(f"Step 3: Establishing WebSocket connection to {ws_url}", "cyan"))
    ws.connect(ws_url)

    # Step 4: Load and display the generation workflow
    print(colored("Step 4: Loading the image generation workflow from 'pipeline_workflow.json'.", "cyan"))
    print("Attempting to load workflow at:", get_workflow_path())
    with open(get_workflow_path(), "r") as f:
        workflow = json.load(f)

    print(colored("Here's the workflow as it was loaded before customization:", "yellow"))
    print(colored(json.dumps(workflow, indent=4), "blue"))

    # Step 5: Customize the workflow based on input parameters
    print(colored("Step 5: Customizing the workflow with the provided inputs.", "cyan"))
    print(colored(f"Setting positive prompt: {positive_prompt}", "yellow"))
    workflow["107"]["inputs"]["text"] = positive_prompt  # Set prompt text

    print(colored(f"Setting resolution to {resolution[0]}x{resolution[1]}", "yellow"))
    workflow["80"]["inputs"]["width"] = resolution[0]
    workflow["80"]["inputs"]["height"] = resolution[1]

    seed = random.randint(1, 1000000000)
    print(colored(f"Setting random seed for generation: {seed}", "yellow"))
    workflow["25"]["inputs"]["noise_seed"] = seed
    workflow["99"]["inputs"]["noise_seed"] = seed

    print(colored(f"Setting batch size to: {batch_size}", "yellow"))
    workflow["93"]["inputs"]["batch_size"] = batch_size

    # Start generation process and retrieve images
    images = get_images(ws, workflow)

    # Step 8: Close the WebSocket connection
    print(colored(f"Step 8: Closing WebSocket connection to {ws_url}", "cyan"))
    ws.close()

    return images, seed

# Allows running the script manually for testing
if __name__ == "__main__":
    # Step 2: Ask user for a positive prompt
    positive_prompt = input(colored("Enter the positive prompt: ", "cyan"))
    print(colored("Step 2: User inputs the positive for image generation.", "cyan"))

    # Generate images using the provided prompt
    images, seed = generate_images(positive_prompt)
