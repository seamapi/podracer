import shutil
import subprocess
import sys

from pathlib import Path
from podracer.docker_config import DockerConfig
from podracer.ostree import rev_parse


def run(ref):
  sha = rev_parse(ref)
  workdir = Path.home().joinpath('.podracer')
  workdir.mkdir(mode=0o700, parents=True, exist_ok=True)

  checkout = workdir.joinpath(sha)
  config_path = checkout.joinpath('docker-config.json')
  rootfs = checkout.joinpath('rootfs')

  if checkout.is_dir() and not (config_path.is_file() and rootfs.is_dir()):
    shutil.rmtree(str(checkout))

  if not checkout.is_dir():
    subprocess.run(['ostree', 'checkout', sha, str(checkout)], check=True)

  print(str(checkout))
  podman_args = DockerConfig(config_path).podman_args()
  print(podman_args)


def main(argv=sys.argv):
  argv = argv[1:]
  if len(argv) != 1:
    raise RuntimeError("This script takes exactly one argument")

  run(argv[0])


if __name__ == "__main__":
  main()
