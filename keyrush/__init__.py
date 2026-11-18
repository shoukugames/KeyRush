"""Key Rush - a home-row memory and typing game."""
__version__ = "0.1.1"
RELEASE_DATE = "2026-11-08"

# True when running in a web browser (pygbag / WebAssembly).
import sys as _sys
WEB = _sys.platform == "emscripten"
