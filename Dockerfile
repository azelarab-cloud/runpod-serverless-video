FROM pytorch/pytorch:2.5.0-cuda12.4-cudnn9-runtime

WORKDIR /workspace

# Install system dependencies (git and ffmpeg for video rendering)
RUN apt-get update && apt-get install -y git ffmpeg && rm -rf /var/lib/apt/lists/*

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

WORKDIR /workspace/ComfyUI

# Install core dependencies
RUN pip install -r requirements.txt
RUN pip install runpod gguf protobuf requests kornia==0.7.1 opencv-python-headless av

# Clone Custom Nodes for LTX Video and VideoHelperSuite
WORKDIR /workspace/ComfyUI/custom_nodes
RUN git clone https://github.com/city96/ComfyUI-GGUF.git
RUN git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git
RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
RUN git clone https://github.com/princepainter/Comfyui-PainterAudioLength.git

# Install requirements for the custom nodes
RUN find . -name "requirements.txt" -exec pip install -r {} \;

WORKDIR /workspace/ComfyUI

# Copy the serverless handler
COPY handler.py .

# Start the RunPod worker
CMD ["python", "-u", "handler.py"]
