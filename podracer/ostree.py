import subprocess

from pathlib import Path

CHECKOUTROOT = Path('/var/lib/podracer/checkouts')


def ostree_rev_parse(ref):
  parsed = subprocess.run(['ostree', 'rev-parse', ref], check=True, capture_output=True, text=True)
  return parsed.stdout.strip()


def ostree_checkout(ref):
  sha = ostree_rev_parse(ref)

  CHECKOUTROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
  checkout = CHECKOUTROOT.joinpath(sha)

  if not checkout.is_dir():
    subprocess.run(['ostree', 'checkout', sha, str(checkout)], check=True)

  return checkout
