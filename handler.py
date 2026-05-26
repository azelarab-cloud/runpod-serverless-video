import runpod
import subprocess
import time
import requests
import json
import urllib.request
import os
import base64

def start_comfyui():
    print("Configuring ComfyUI to read from the Network Volume...")
    
    yaml_content = """
runpod_volume:
  base_path: /workspace/comfy_persist/models

  checkpoints: |
    checkpoints
    vae

  clip: |
    clip
    text_encoders

  text_encoders: |
    clip
    text_encoders

  unet: |
    unet
    diffusion_models

  diffusion_models: |
    unet
    diffusion_models

  vae: |
    vae
    checkpoints

  loras: |
    loras
"""
    # Ensure this writes to the directory ComfyUI expects, typically the ComfyUI root.
    with open("extra_model_paths.yaml", "w") as f:
        f.write(yaml_content)
        
    print("Starting ComfyUI Engine...")
    proc = subprocess.Popen(["python", "main.py", "--listen", "127.0.0.1", "--port", "8188"])
    
    start = time.time()
    while True:
        # Check if the ComfyUI process crashed
        if proc.poll() is not None:
            raise RuntimeError("ComfyUI exited during startup")

        # Timeout after 120 seconds
        if time.time() - start > 120:
            raise TimeoutError("ComfyUI did not become ready within 120s")

        try:
            # Poll the API to check readiness
            r = requests.get("http://127.0.0.1:8188/", timeout=2)
            if r.status_code == 200:
                print("ComfyUI is ready!")
                break
        except requests.exceptions.RequestException:
            time.sleep(1)

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}") as response:
        return json.loads(response.read())

def handler(job):
    job_input = job['input']
    workflow = job_input['workflow']
    input_files = job_input.get('input_files', [])
    
    print("Writing dynamic input files...")
    os.makedirs("input", exist_ok=True)
    for file in input_files:
        filename = file['name']
        file_data = base64.b64decode(file['base64'])
        with open(os.path.join("input", filename), "wb") as f:
            f.write(file_data)
        print(f"Saved input: {filename}")

    print("Received job, queuing workflow...")
    prompt_response = queue_prompt(workflow)
    prompt_id = prompt_response['prompt_id']
    print(f"Prompt queued. ID: {prompt_id}")
    
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            print("Generation complete!")
            outputs = history[prompt_id]['outputs']
            results = []
            
            for node_id in outputs:
                if 'gifs' in outputs[node_id]:
                    for video in outputs[node_id]['gifs']:
                        video_path = os.path.join("output", video['filename'])
                        with open(video_path, "rb") as vid_file:
                            encoded_string = base64.b64encode(vid_file.read()).decode('utf-8')
                            results.append({
                                "filename": video['filename'],
                                "data_base64": encoded_string
                            })
            
            return {"status": "success", "media": results}
        
        time.sleep(3)

start_comfyui()
print("Starting RunPod Serverless Video Worker...")
runpod.serverless.start({"handler": handler})
