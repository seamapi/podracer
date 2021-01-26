import argparse
import shutil
import subprocess
import sys

from pathlib import Path
from podracer.docker_config import DockerConfig
from podracer.env import unpack_env_array
from podracer.ostree import rev_parse


def run(ref, env={}, command=[], *extra_args):
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

  docker_config = DockerConfig(config_path)

  if env is not None:
    docker_config.env.update(env)

  if len(command) > 0:
    docker_config.command = command

  subprocess.run(['podman', 'run'] + docker_config.podman_args(rootfs))


def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser(description='Run a container from an ostree commit')
  parser.add_argument('ref', metavar='OSTREE_REF', nargs=1, help='ostree commit for container')
  parser.add_argument('command', metavar='CMD', nargs='*', help='command to run in container')
  #parser.add_argument('-S', '--systemd', metavar='NAME', help='base name to use for pidfiles, etc under systemd')
  parser.add_argument('-e', '--env', metavar='KEY=VALUE', action='append', help='add or override container environment variable')

  args = parser.parse_args(argv)

  if len(args.ref) != 1:
    raise RuntimeError('something went wrong parsing ref')

  #extra_args = []
  #if args.systemd is not None:

  #print(args.systemd)
  print(args.env)
  run(args.ref[0], unpack_env_array(args.env), args.command)


if __name__ == "__main__":
  main()
