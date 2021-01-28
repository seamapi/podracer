import json
import os
import shutil
import subprocess
import sys

from pathlib import Path

# It's important to only import from the stdlib here, because the hook
# instructs podman to run this file directly from the interpreter; you
# can't count on anything but the stdlib to be available to import.


def generate_hook(rundir):
  hook = {
    'cmds': ['.*'],
    'hook': sys.executable,
    'arguments': [str(Path(__file__).absolute()), str(Path(rundir).absolute())],
    'stages': ['poststop']
  }

  return hook


def poststop(rundir):
  rundir = Path(rundir).absolute()
  if not rundir.is_dir():
    return

  for child in rundir.iterdir():
    if os.path.ismount(child):
      subprocess.run(['umount', str(child)], check=True)

  if os.path.ismount(rundir):
    subprocess.run(['umount', str(rundir)], check=True)

  shutil.rmtree(rundir)


def main(argv=sys.argv[1:]):
  if len(argv) != 1:
    raise RuntimeError('This script takes exactly one argument')

  poststop(argv[0])
  return 0


if __name__ == "__main__":
  sys.exit(main())
