"""
TiaCAD entry point for python -m tiacad_core

Allows running: python -m tiacad_core build examples/plate.yaml
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())
