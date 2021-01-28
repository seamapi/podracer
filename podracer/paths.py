import os

from pathlib import Path

PODRACER_RUNDIR = Path(os.environ.get('PODRACER_RUNDIR', '/run/podracer'))
