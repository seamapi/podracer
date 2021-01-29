import argparse
import json
import sys
from typing import Iterable

from podracer.registry import get_manifests


def filter_manifests(manifests: list[dict], arch: str = None, osname: str = None, variant: str = None) -> Iterable[dict]:
  for manifest in manifests:
    if arch is not None:
      if manifest['platform']['architecture'] != arch:
        continue

    if osname is not None:
      if manifest['platform']['os'] != osname:
        continue

    if variant is not None:
      if 'variant' not in manifest['platform']:
        continue
      if manifest['platform']['variant'] != variant:
        continue

    yield manifest


def main(argv: list[str] = sys.argv[1:]) -> int:
  parser = argparse.ArgumentParser(description='Inspect registry manifests')
  parser.add_argument('image', metavar='IMAGE', help='image to inspect')
  parser.add_argument('--arch', metavar='ARCH', help='filter by architecture')
  parser.add_argument('--os', metavar='OS', help='filter by OS')
  parser.add_argument('--variant', metavar='VARIANT', help='filter by variant')
  parser.add_argument('--output', metavar='yaml|json|digests', help='output format; "digests" prints one digest per line')
  args = parser.parse_args(argv)

  manifests = list(filter_manifests(get_manifests(args.image), args.arch, args.os, args.variant))

  if len(manifests) < 1:
    sys.stderr.write("No manifests found\n")
    return 1

  if args.output is None or args.output == 'yaml':
    for manifest in manifests:
      print(f"- digest: {manifest['digest']}")
      print(f"  architecture: {manifest['platform']['architecture']}")
      print(f"  os: {manifest['platform']['os']}")
      if 'variant' in manifest['platform']:
        print(f"  variant: {manifest['platform']['variant']}")
  elif args.output == 'json':
    print(json.dumps(manifests, indent=2))
  elif args.output == 'digests':
    for manifest in manifests:
      print(manifest['digest'])
  else:
    raise RuntimeError(f"Unknown output format: {args.output}")

  return 0


if __name__ == "__main__":
  sys.exit(main())
