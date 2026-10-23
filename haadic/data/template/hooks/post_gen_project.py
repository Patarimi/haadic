"""Hook executed after the project is generated."""

from pathlib import Path

Path("design.py.jinja").rename("design.py")
