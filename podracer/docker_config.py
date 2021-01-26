import json

from podracer.env import unpack_env_array

class DockerConfig:
  def __init__(self, config_path):
    with open(config_path) as io:
      self.config = json.load(io)

    self.env = {}
    if 'Env' in self.config:
      self.env = unpack_env_array(self.config['Env'])

    self.working_dir = self._get_config_scalar('WorkingDir')
    self.user = self._get_config_scalar('User')
    self.entrypoint = self._get_config_list('Entrypoint')
    self.command = self._get_config_list('Cmd')


  def _get_config_scalar(self, key):
    if (key in self.config) and len(self.config[key]) > 0:
      return self.config[key]
    return None


  def _get_config_list(self, key):
    if (key in self.config):
      if isinstance(self.config[key], list):
        return self.config[key]
      else:
        value = self._get_config_scalar(key)
        if value is not None:
          return [value]
    return []


  def podman_args(self, rootfs):
    args = []

    if self.working_dir is not None:
      args += ['-w', self.working_dir]

    if self.user is not None:
      args += ['-u', self.user]

    for key, value in self.env.items():
      args += ['-e', f'{key}={value}']

    if len(self.entrypoint) > 0:
      args += ['--entrypoint', self.entrypoint[0]]
      command = self.entrypoint[1:] + self.command
    else:
      command = self.command

    args += ['--rootfs', str(rootfs)] + command

    return args
