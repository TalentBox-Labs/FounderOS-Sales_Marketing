"""
CLI entry: validation pipeline + optional CrewAI QA + tracker update.

Google Sheet mirror is intentionally separate — run after a green pipeline:
  python -m src.tools.sheet_sync --dry-run
  python -m src.tools.sheet_sync --write
See docs/CMS_OS_Operating_Loop.md and docs/System_Architecture.md section 4.2.
"""

from src.tools.pipeline_runner import run_pipeline


def main():
    print("\nSTARTING WORKCREW CMS OS\n")
    run_pipeline()


if __name__ == "__main__":
    main()