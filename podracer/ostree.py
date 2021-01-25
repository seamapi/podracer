import subprocess

def rev_parse(ref):
  parsed = subprocess.run(['ostree', 'rev-parse', ref], check=True, capture_output=True, text=True)
  return parsed.stdout.strip()
