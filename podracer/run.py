import argparse
import os
import subprocess
import sys

from podracer.docker_config import DockerConfig
from podracer.env import unpack_env_array
from podracer.ostree import ostree_checkout
from podracer.overlay import podracer_overlay


def run(name, ref, env={}, command=[], *extra_args):
  checkout = ostree_checkout(ref)
  docker_config = DockerConfig(checkout.joinpath('docker-config.json'))

  if env is not None:
    docker_config.env.update(env)

  if len(command) > 0:
    docker_config.command = command

  with podracer_overlay(name, checkout.joinpath('rootfs')) as rootfs:
    subprocess.run(['podman', 'run', '--name', name] + docker_config.podman_args(rootfs))


def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser(description='Run a container from an ostree commit')
  parser.add_argument('ref', metavar='OSTREE_REF', nargs=1, help='ostree commit for container')
  parser.add_argument('command', metavar='CMD', nargs='*', help='command to run in container')
  parser.add_argument('-n', '--name', metavar='NAME', help='name to assign to container')
  parser.add_argument('-e', '--env', metavar='KEY=VALUE', action='append', help='add or override container environment variable')

  args = parser.parse_args(argv)

  if len(args.ref) != 1:
    raise RuntimeError('something went wrong parsing ref')

  args.ref = args.ref[0]

  if args.name is None:
    args.name = f"{args.ref.replace('/', '-')}-{str(os.getpid())}"

  if args.env is None:
    args.env = {}
  else:
  args.env = unpack_env_array(args.env)

  run(args.name, args.ref, args.env, args.command)


if __name__ == "__main__":
  main()
