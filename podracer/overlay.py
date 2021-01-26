import subprocess

from contextlib import contextmanager
from podracer.rundir import podracer_rundir


@contextmanager
def podracer_overlay(name, rootfs):
  with podracer_rundir(name) as rundir:
    upperdir = rundir.joinpath('upperdir')
    upperdir.mkdir(mode=0o755, parents=True, exist_ok=True)

    workdir = rundir.joinpath('workdir')
    workdir.mkdir(mode=0o755, parents=True, exist_ok=True)

    merged = rundir.joinpath('merged')
    merged.mkdir(mode=0o755, parents=True, exist_ok=True)

    mount_options = f'-olowerdir={rootfs},upperdir={upperdir},workdir={workdir}'
    subprocess.run(['mount', '-t', 'overlay', 'overlay', mount_options, str(merged)], check=True)

    try:
      yield merged
    finally:
      subprocess.run(['umount', str(merged)])
