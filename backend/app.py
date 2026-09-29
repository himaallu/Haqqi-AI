"""Hugging Face Spaces entry point.

Gradio-SDK Spaces run `python app.py` and route traffic to port 7860.
We serve our FastAPI app directly; Gradio itself is not used.
Locally, run `uvicorn haqqi.api.main:app` instead.
"""

import os

import uvicorn

from haqqi.api.main import app

__all__ = ["app"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))  # noqa: S104
