import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile

from pathlib import Path
from podracer.env import unpack_env
from podracer.paths import PODRACER_RUNDIR
from podracer.ostree import ostree_checkout
from podracer.overlay import podracer_overlay
from podracer.poststop import poststop
from podracer.signals import forward_signals

FORWARD_SIGNALS = [signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]


class Runner:
  def __init__(self, rootfs, *command, env = {}, name = None, daemon = False, passthru_args = []):
    if rootfs.startswith('ostree:'):
      ref = rootfs.split(':', 1)[1]
      rootfs = ostree_checkout(ref)

      if name is None:
        name = f"{ref.replace('/', '-')}-{str(os.getpid())}"

    rootfs = Path(rootfs)

    if not rootfs.is_dir():
      raise RuntimeError(f"rootfs {rootfs} is not a directory")

    if name is None:
      name = f"{rootfs.name}-{str(os.getpid())}"

    self.name = name
    self.rootfs = rootfs
    self.daemon = daemon
    self.passthru_args = passthru_args
    self.working_dir = None
    self.user = None
    self.env = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}
    self.entrypoint = []
    self.command = []

    self.load_config()

    if len(command) > 0:
      self.command = list(command)
    elif len(self.command) < 1:
      if os.access(rootfs.joinpath('bin/bash'), os.X_OK):
        self.command = ['/bin/bash']
      elif os.access(rootfs.joinpath('bin/sh'), os.X_OK):
        self.command = ['/bin/sh']

    self.env.update(env)
    self.child = None


  def load_config(self):
    config_path = self.rootfs.joinpath('.podracer.json')

    if not config_path.is_file():
      return

    with open(config_path) as io:
      config = json.load(io)["config"]

    if 'Env' in config:
      self.env = unpack_env(config['Env'])

    if ('WorkingDir' in config) and (len(config['WorkingDir']) > 0):
      self.working_dir = config['WorkingDir']

    if ('User' in config) and (len(config['User']) > 0):
      self.user = config['User']

    if ('Entrypoint' in config) and (config['Entrypoint'] is not None):
      self.entrypoint = config['Entrypoint']

    if ('Cmd' in config) and (config['Cmd'] is not None):
      self.command = config['Cmd']


  def podman_args(self):
    args = ['--rm', '--name', self.name, '--replace']

    if self.daemon:
      args += [
        '--conmon-pidfile', f"/run/container-{self.name}.pid",
        '--cidfile', f"/run/container-{self.name}.ctr-id",
        '--cgroups=no-conmon'
      ]

    if self.working_dir is not None:
      args += ['-w', self.working_dir]

    if self.user is not None:
      args += ['-u', self.user]

    if len(self.entrypoint) > 0:
      args += ['--entrypoint', json.dumps(self.entrypoint)]

    return args + self.passthru_args + ['--rootfs', str(self.rootfs)] + self.command


  def send_signal(self, signum):
    if self.child is None:
      return None
    return self.child.send_signal(signum)


  def run(self, overlay=True, detach=False):
    rundir = Path(tempfile.mkdtemp(dir=PODRACER_RUNDIR))

    try:
      if overlay:
        self.rootfs, hooks = podracer_overlay(rundir, self.rootfs)
        self.passthru_args += ['--hooks-dir', hooks]

      if detach:
        self.passthru_args.append('-d')

      env_file = rundir.joinpath('env')
      with open(env_file, 'w') as io:
        for key, value in self.env.items():
          io.write(f"{key}={value}\n")

      argv = ['podman', 'run', '--env-file', str(env_file)] + self.podman_args()

      with forward_signals(self.send_signal, *FORWARD_SIGNALS):
        self.child = subprocess.Popen(argv)
        self.child.wait()
    finally:
      if rundir.exists() and not detach:
        poststop(rundir)

    return self.child.returncode


def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser(description='Run a container from a rootfs or an ostree commit')
  parser.add_argument('rootfs', metavar='ROOTFS', nargs=1, help='path to rootfs OR "ostree:<OSTREE COMMIT>"')
  parser.add_argument('command', metavar='CMD', nargs='*', help='command to run in container')
  parser.add_argument('-n', '--name', metavar='NAME', help='name to assign to container')
  parser.add_argument('-e', '--env', metavar='KEY=VALUE', action='append', help='add or override a container environment variable')
  parser.add_argument('--env-file', metavar='FILE', action='append', help='read environment variables from a file')
  parser.add_argument('-v', '--volume', metavar='VOLUME', action='append', help='bind mount a volume into the container')
  parser.add_argument('--network', metavar='NETWORK', action='append', help='connect the container to a network')
  parser.add_argument('-t', '--tty', action='store_true', help='allocate a pseudo-TTY for container')
  parser.add_argument('-i', '--interactive', action='store_true', help='keep STDIN open even if not attached')
  args = parser.parse_args(argv)

  if len(args.rootfs) != 1:
    raise RuntimeError('Something went wrong parsing rootfs')

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

  passthru_args = []

  for attr in ['volume', 'network']:
    values = getattr(args, attr)
    if values is not None:
      for value in values:
        passthru_args += [f"--{attr}", value]

  if args.tty:
    passthru_args.append('-t')

  if args.interactive:
    passthru_args.append('-i')

  Runner(args.rootfs[0], *args.command, env=args.env, name=args.name, passthru_args=passthru_args).run()
  return 0


if __name__ == "__main__":
  sys.exit(main())
