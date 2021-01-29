import json
import os
import shutil
import subprocess
import tempfile

from pathlib import Path
from typing import Tuple
from podracer.poststop import generate_hook

PODRACER_RUNDIR = Path(os.environ.get('PODRACER_RUNDIR', '/run/podracer'))


def podracer_overlay(rundir: Path, rootfs: Path) -> Tuple[Path, Path]:
  upperdir = rundir.joinpath('upperdir')
  upperdir.mkdir(mode=0o755, parents=True, exist_ok=True)

  workdir = rundir.joinpath('workdir')
  workdir.mkdir(mode=0o755, parents=True, exist_ok=True)

  overlay = rundir.joinpath('rootfs')
  overlay.mkdir(mode=0o755, parents=True, exist_ok=True)

  hooks = rundir.joinpath('hooks')
  hooks.mkdir(mode=0o755, parents=True, exist_ok=True)

  with open(hooks.joinpath('cleanup.json'), 'w') as io:
    json.dump(generate_hook(rundir), io)

  mount_options = f'-olowerdir={rootfs},upperdir={upperdir},workdir={workdir}'
  subprocess.run(['mount', '-t', 'overlay', 'overlay', mount_options, str(overlay)], check=True)

  return overlay, hooks
