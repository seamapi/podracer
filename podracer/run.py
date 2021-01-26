import argparse
import os
import signal
import subprocess
import sys

from podracer.docker_config import DockerConfig
from podracer.env import unpack_env_array
from podracer.ostree import ostree_checkout
from podracer.overlay import podracer_overlay
from podracer.signals import forward_signals

FORWARD_SIGNALS = [signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]


class Runner:
  def __init__(self, name, ref, env={}, command=[]):
    self.name = name
    self.checkout = ostree_checkout(ref)
    self.docker_config = DockerConfig(self.checkout.joinpath('docker-config.json'))
    self.child = None

    if env is not None:
      self.docker_config.env.update(env)

    if len(command) > 0:
      self.docker_config.command = command


  def podman_args(self, rootfs):
    args = ['--name', self.name]

    if self.docker_config.working_dir is not None:
      args += ['-w', self.docker_config.working_dir]

    if self.docker_config.user is not None:
      args += ['-u', self.docker_config.user]

    for key, value in self.docker_config.env.items():
      args += ['-e', f'{key}={value}']

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
    with podracer_overlay(self.name, self.checkout.joinpath('rootfs')) as rootfs:
      with forward_signals(self.send_signal, *FORWARD_SIGNALS):
        self.child = subprocess.Popen(['podman', 'run'] + self.podman_args(rootfs))
        self.child.wait()
        return self.child.returncode


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

  return Runner(args.name, args.ref, args.env, args.command).run()


if __name__ == "__main__":
  sys.exit(main())
