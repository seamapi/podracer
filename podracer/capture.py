import json
import subprocess
import sys

def capture_output(*argv, suppress_stderr=False):
  if suppress_stderr:
    child_stderr = subprocess.PIPE
  else:
    child_stderr = sys.stderr

  child = subprocess.run(argv, check=True, stdout=subprocess.PIPE, stderr=child_stderr, text=True)
  return child.stdout.strip()


def capture_json(*argv, suppress_stderr=False):
  return json.loads(capture_output(*argv, suppress_stderr=suppress_stderr))
