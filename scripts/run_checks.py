"""Compatibility entrypoint for the current revision checks."""
from pathlib import Path
from runpy import run_path
run_path(str(Path(__file__).with_name("check_revision.py")),run_name="__main__")
