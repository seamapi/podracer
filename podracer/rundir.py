import fcntl
import os
import shutil

from contextlib import contextmanager
from pathlib import Path

RUNROOT = Path('/run/podracer')


@contextmanager
def podracer_lockfile(name):
  RUNROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
  lockfile = RUNROOT.joinpath(f'{name}.lock')
  lockfd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)

  try:
    fcntl.lockf(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    yield lockfile
  finally:
    os.unlink(lockfile)
    os.close(lockfd)


@contextmanager
def podracer_rundir(name):
  rundir = RUNROOT.joinpath(name)
  with podracer_lockfile(name):
    try:
      rundir.mkdir(mode=0o755, parents=True)
      yield rundir
    finally:
      shutil.rmtree(rundir)
