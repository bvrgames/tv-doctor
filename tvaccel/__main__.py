"""python3 -m tvaccel accelerate|repeat|restore|info [--host IP] — see cli.py."""
import sys

from .cli import main

sys.exit(main())
