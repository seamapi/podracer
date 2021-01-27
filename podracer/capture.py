import subprocess
import json


def capture_output(*argv):
  child = subprocess.run(argv, check=True, stdout=subprocess.PIPE, text=True)
  return child.stdout.strip()


def capture_json(*argv):
  return json.loads(capture_output(*argv))
