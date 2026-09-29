---
title: Haqqi API
emoji: ⚖️
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 6.29.0
python_version: "3.12"
app_file: app.py
pinned: false
---

# Haqqi backend

FastAPI service for Haqqi. The YAML header above is read by Hugging Face Spaces: a free Gradio-SDK Space installs
`requirements.txt` and runs `app.py`, which serves the FastAPI app on port 7860 (Gradio itself is not used).
See `docs/DEPLOY.md` in the main repository.

`requirements.txt` is generated from `uv.lock`; after changing dependencies run
`uv export --no-dev --no-hashes --no-emit-project -o requirements.txt`.
