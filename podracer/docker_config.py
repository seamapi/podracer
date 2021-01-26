import json

from podracer.env import unpack_env

class DockerConfig:
  def __init__(self, config_path):
    with open(config_path) as io:
      self.config = json.load(io)

    self.env = {}
    if 'Env' in self.config:
      self.env = unpack_env(self.config['Env'])

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
