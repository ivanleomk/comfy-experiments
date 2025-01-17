import json
import subprocess
import uuid
from pathlib import Path
from typing import Dict

import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install("comfy-cli==1.2.7")
    .run_commands("comfy --skip-prompt install --nvidia")
)

image = image.run_commands(
    "comfy node install was-node-suite-comfyui"
).run_commands(  # needs to be empty for Volume mount to work
    "rm -rf /root/comfy/ComfyUI/models"
)

app = modal.App(name="comfyui-api", image=image)

vol = modal.Volume.from_name("comfyui-models", create_if_missing=True)


@app.cls(
    gpu="A10G",
    volumes={"/root/comfy/ComfyUI/models": vol},
    mounts=[
        modal.Mount.from_local_file(
            "workflows/flux.json",
            "/root/flux.json",
        ),
        modal.Mount.from_local_file(
            "workflows/ltx.json",
            "/root/ltx.json",
        ),
    ],
)
class ComfyUI:
    @modal.enter()
    def launch_comfy_background(self):
        cmd = "comfy launch --background"
        subprocess.run(cmd, shell=True, check=True)

    @modal.method()
    def infer(self, workflow_path: str = "/root/flux.json"):
        cmd = f"comfy run --workflow {workflow_path} --wait --timeout 1200"
        subprocess.run(cmd, shell=True, check=True)

        output_dir = "/root/comfy/ComfyUI/output"
        workflow = json.loads(Path(workflow_path).read_text())
        file_prefix = [
            node.get("inputs")
            for node in workflow.values()
            if node.get("class_type") == "SaveImage"
            or node.get("class_type") == "SaveAnimatedWEBP"
        ][0]["filename_prefix"]

        for f in Path(output_dir).iterdir():
            if f.name.startswith(file_prefix):
                return f.read_bytes()

    @modal.web_endpoint(method="POST")
    def api(self, item: Dict):
        from fastapi import Response

        workflow_data = json.loads(Path("/root/flux.json").read_text())
        workflow_data["6"]["inputs"]["text"] = item["prompt"]

        client_id = uuid.uuid4().hex
        workflow_data["9"]["inputs"]["filename_prefix"] = client_id

        new_workflow_file = f"{client_id}.json"
        json.dump(workflow_data, Path(new_workflow_file).open("w"))

        img_bytes = self.infer.local(new_workflow_file)
        return Response(img_bytes, media_type="image/jpeg")

    @modal.web_endpoint(method="POST")
    def video_api(self, item: Dict):
        from fastapi import Response

        workflow_data = json.loads((Path(__file__).parent / "ltx.json").read_text())

        # insert the prompt
        workflow_data["6"]["inputs"]["text"] = item["prompt"]

        # give the output video a unique id per client request
        client_id = uuid.uuid4().hex
        workflow_data["41"]["inputs"]["filename_prefix"] = client_id

        # save this updated workflow to a new file
        new_workflow_file = f"{client_id}.json"
        json.dump(workflow_data, Path(new_workflow_file).open("w"))

        # run inference on the currently running container
        video_bytes = self.infer.local(new_workflow_file)

        return Response(video_bytes, media_type="video/webp")
