def unpack_env(src):
  env = {}
  for kv in src:
    key, value = kv.strip().split('=', 1)
    env[key] = value
  return env
