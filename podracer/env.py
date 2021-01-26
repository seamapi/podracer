def unpack_env_array(src):
  env = {}
  for kv in src:
    key, value = kv.split('=', 1)
    env[key] = value
  return env


def synthesize_env_args(env):
  args = []
  for key, value in env.items():
    args += ['-e', f'{key}={value}']
  return args
