import subprocess

from pathlib import Path
from podracer.capture import capture_output

CHECKOUTROOT = Path('/var/lib/podracer/ostree')


def ostree_rev_parse(ref):
  return capture_output('ostree', 'rev-parse', ref, suppress_stderr=True)


def ostree_checkout(ref):
  sha = ostree_rev_parse(ref)

  CHECKOUTROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
  checkout = CHECKOUTROOT.joinpath(sha)

  if not checkout.is_dir():
    subprocess.run(['ostree', 'checkout', sha, str(checkout)], check=True)

  return checkout
