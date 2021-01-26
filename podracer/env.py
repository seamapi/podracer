def unpack_env_array(src):
  env = {}
  for kv in src:
    key, value = kv.split('=', 1)
    env[key] = value
  return env
