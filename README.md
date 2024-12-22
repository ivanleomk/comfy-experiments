# Introduction

This repository contains adapted code that can be used to run the following models on `comfy-ui` using `modal`

1. [`black-forest-labs/FLUX.1-dev`](https://huggingface.co/black-forest-labs/FLUX.1-dev)
2. [`black-forest-labs/FLUX.1-schnell`](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
3. [`Mochi Preview`](https://huggingface.co/Comfy-Org/mochi_preview_repackaged): Note that we're using the repackaged version of the repository that was provided by Comfy-UI
4. [`LTX-Video`](https://huggingface.co/Lightricks/LTX-Video)

These models are all available on Hugging Face and we'll be using `modal` to run them with a `A10G` GPU. There are also two sample endpoints provided that can be used to run `flux-1.5-dev` and the `LTX-Video` model. We've provided the following scripts for use

1. `download.py` : This is a script that will download all the relevant models used in `workflows/*.json` workflow config files.
2. `api.py` : This is a script that will run the `comfy-ui` server and provide two endpoints for use.
3. `ui.py` : This is a script that will run the `comfy-ui` server and provide an interactive UI endpoint for use.
