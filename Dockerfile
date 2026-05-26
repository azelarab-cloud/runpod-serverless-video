FROM pytorch/pytorch:2.5.0-cuda12.4-cudnn9-runtime

WORKDIR /workspace

# 1. Install system dependencies (required for VideoHelperSuite and image processing)
RUN apt-get update && apt-get install -y git ffmpeg libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# 2. Clone the core ComfyUI repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

WORKDIR /workspace/ComfyUI

# 3. Install core ComfyUI requirements
RUN pip install --no-cache-dir -r requirements.txt

# 4. Install RunPod and all specific Python dependencies for the custom nodes
# (Includes kornia==0.7.1 to prevent the previous LTXVideo node crash)
RUN pip install --no-cache-dir runpod gguf protobuf PyWavelets scikit-image imageio-ffmpeg requests kornia==0.7.1 opencv-python-headless av

# 5. Clone ALL required Custom Nodes directly into the image
WORKDIR /workspace/ComfyUI/custom_nodes

RUN git clone https://github.com/city96/ComfyUI-GGUF.git
RUN git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git
RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
RUN git clone https://github.com/princepainter/Comfyui-PainterAudioLength.git

# 6. Install any remaining requirements from the custom nodes
RUN find . -name "requirements.txt" -exec pip install --no-cache-dir -r {} \;

# 7. Return to the main ComfyUI directory
WORKDIR /workspace/ComfyUI

# 8. Start the RunPod Serverless worker
COPY handler.py .
CMD ["python", "-u", "handler.py"]
