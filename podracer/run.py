import argparse
import os
import signal
import subprocess
import sys

from podracer.docker_config import DockerConfig
from podracer.env import unpack_env
from podracer.ostree import ostree_checkout
from podracer.overlay import podracer_overlay
from podracer.signals import forward_signals

FORWARD_SIGNALS = [signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]


class Runner:
  def __init__(self, name, ref, env={}, volumes=[], networks=[], command=[]):
    self.name = name
    self.volumes = volumes
    self.networks = networks
    self.checkout = ostree_checkout(ref)
    self.docker_config = DockerConfig(self.checkout.joinpath('docker-config.json'))
    self.child = None

    if env is not None:
      self.docker_config.env.update(env)

    if len(command) > 0:
      self.docker_config.command = command


  def podman_args(self, rootfs):
    args = [
      '--rm',
      '--name', self.name,
      '--replace',
      '--conmon-pidfile', f"/run/container-{self.name}.pid",
      '--cidfile', f"/run/container-{self.name}.ctr-id",
      '--cgroups=no-conmon'
    ]

    if self.docker_config.working_dir is not None:
      args += ['-w', self.docker_config.working_dir]

    if self.docker_config.user is not None:
      args += ['-u', self.docker_config.user]

    for vol in self.volumes:
      args += ['-v', vol]

    for net in self.networks:
      args += ['--network', net]

    if len(self.docker_config.entrypoint) > 0:
      args += ['--entrypoint', self.docker_config.entrypoint[0]]
      command = self.docker_config.entrypoint[1:] + self.docker_config.command
    else:
      command = self.docker_config.command

    args += ['--rootfs', str(rootfs)] + command

    return args


  def send_signal(self, signum):
    if self.child is None:
      return None
    return self.child.send_signal(signum)


  def run(self):
    with podracer_overlay(self.name, self.checkout.joinpath('rootfs')) as (rundir, rootfs):
      env_file = rundir.joinpath('env')
      with open(env_file, 'w') as io:
        for key, value in self.docker_config.env.items():
          io.write(f"{key}={value}\n")

      with forward_signals(self.send_signal, *FORWARD_SIGNALS):
        self.child = subprocess.Popen(['podman', 'run', '--env-file', str(env_file)] + self.podman_args(rootfs))
        self.child.wait()
        return self.child.returncode


def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser(description='Run a container from an ostree commit')
  parser.add_argument('ref', metavar='OSTREE_REF', nargs=1, help='ostree commit for container')
  parser.add_argument('command', metavar='CMD', nargs='*', help='command to run in container')
  parser.add_argument('-n', '--name', metavar='NAME', help='name to assign to container')
  parser.add_argument('-e', '--env', metavar='KEY=VALUE', action='append', help='add or override a container environment variable')
  parser.add_argument('--env-file', metavar='FILE', action='append', help='read environment variables from a file')
  parser.add_argument('-v', '--volume', metavar='VOLUME', action='append', help='bind mount a volume into the container')
  parser.add_argument('--network', metavar='NETWORK', action='append', help='connect the container to a network')

  args = parser.parse_args(argv)

  if len(args.ref) != 1:
    raise RuntimeError('Something went wrong parsing ref')

  args.ref = args.ref[0]

  if args.name is None:
    args.name = f"{args.ref.replace('/', '-')}-{str(os.getpid())}"

  if args.env is None:
    args.env = {}
  else:
    args.env = unpack_env(args.env)

  if args.env_file is not None:
    file_env = {}
    for env_file in args.env_file:
      with open(env_file) as io:
        file_env.update(unpack_env(io))

    # -e vars override --env-files
    file_env.update(args.env)
    args.env = file_env

  if args.volume is None:
    args.volume = []

  if args.network is None:
    args.network = []

  return Runner(args.name, args.ref, args.env, args.volume, args.network, args.command).run()


if __name__ == "__main__":
  sys.exit(main())
