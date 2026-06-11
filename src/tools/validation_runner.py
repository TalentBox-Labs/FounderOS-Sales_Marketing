"""CLI alias for the unified pipeline (same behavior as `python main.py`)."""

from src.tools.pipeline_runner import run_pipeline

if __name__ == "__main__":
    run_pipeline()
