def unpack_env(src):
  env = {}
  for kv in src:
    key, value = kv.strip().split('=', 1)
    env[key] = value
  return env


def unpack_env_file(path):
  with open(path) as io:
    return unpack_env(io)
