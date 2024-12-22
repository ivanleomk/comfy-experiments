import subprocess

import modal

# Build up the environment
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install("comfy-cli==1.2.7")
    .run_commands("comfy --skip-prompt install --nvidia")
)

# Download custom nodes
image = image.run_commands(
    "comfy node install was-node-suite-comfyui"
).run_commands(  # needs to be empty for Volume mount to work
    "rm -rf /root/comfy/ComfyUI/models"
)

app = modal.App(name="example-comfyui", image=image)

# Set up model storage
vol = modal.Volume.from_name("comfyui-models", create_if_missing=True)


# Interactive UI endpoint
@app.function(
    allow_concurrent_inputs=10,
    concurrency_limit=1,
    container_idle_timeout=30,
    timeout=1800,
    gpu="A100",
    volumes={"/root/comfy/ComfyUI/models": vol},
)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)
