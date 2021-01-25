import json

class DockerConfig:
  def __init__(self, config_path):
    with open(config_path) as io:
      self.config = json.load(io)

    self.env = {}
    if 'Env' in self.config:
      for kv in self.config['Env']:
        key, value = kv.split('=', 1)
        self.env[key] = value

    self.working_dir = self._get_config_scalar('WorkingDir')
    self.user = self._get_config_scalar('User')
    self.entrypoint = self._get_config_scalar('Entrypoint')


  def _get_config_scalar(self, key):
    if (key in self.config) and len(self.config[key]) > 0:
      return self.config[key]
    else:
      return None


  def podman_args(self):
    args = []

    if self.working_dir is not None:
      args += ['-w', self.working_dir]

    if self.user is not None:
      args += ['-u', self.user]

    if self.entrypoint is not None:
      args += ['--entrypoint', self.entrypoint]

    for key, value in self.env.items():
      args += ['-e', f'{key}={value}']

    return args
