import os
import shutil

if os.getenv('PODRACER_RUNTIME') is not None:
  RUNTIME = os.getenv('PODRACER_RUNTIME')
elif shutil.which('podman') is not None:
  RUNTIME = 'podman'
elif shutil.which('docker') is not None:
  RUNTIME = 'docker'
else:
  raise RuntimeError("Couldn't find container runtime; try setting PODRACER_RUNTIME to the path of podman or docker")
