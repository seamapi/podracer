import json
import subprocess
import sys

from typing import Any


def capture_output(*argv: str, suppress_stderr: bool = False) -> str:
  if suppress_stderr:
    child_stderr = subprocess.PIPE
  else:
    child_stderr = sys.stderr.fileno()

  child = subprocess.run(argv, check=True, stdout=subprocess.PIPE, stderr=child_stderr, text=True)
  return child.stdout.strip()


def capture_json(*argv: str, suppress_stderr: bool = False) -> Any:
  return json.loads(capture_output(*argv, suppress_stderr=suppress_stderr))
