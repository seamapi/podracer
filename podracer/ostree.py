import subprocess

from pathlib import Path
from podracer.paths import PODRACER_LIBDIR
from podracer.capture import capture_output


def ostree_rev_parse(ref):
  return capture_output('ostree', 'rev-parse', ref, suppress_stderr=True)


def ostree_checkout(ref):
  sha = ostree_rev_parse(ref)

  checkout_root = PODRACER_LIBDIR.joinpath('ostree')
  checkout_root.mkdir(mode=0o755, parents=True, exist_ok=True)

  checkout = checkout_root.joinpath(sha)
  if not checkout.is_dir():
    subprocess.run(['ostree', 'checkout', sha, str(checkout)], check=True)

  return checkout
