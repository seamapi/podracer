import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile

from pathlib import Path
from podracer.capture import capture_output, capture_json
from podracer.export import EXPORT_COMMAND, export_rootfs
from podracer.manifests import filter_manifests
from podracer.ostree import ostree_rev_parse
from podracer.registry import get_manifests, qualify_image
from typing import List, Optional

METADATA_FILENAME = '.podracer.json'


def registry_manifest(image: str, arch: str, variant: str = None) -> dict:
  manifests = get_manifests(image)
  matches = list(filter_manifests(manifests, arch=arch, variant=variant, osname='linux'))

  if len(matches) < 1:
    raise RuntimeError("No matching manifests; are your architecture and variant correct?")
  elif len(matches) > 1:
    raise RuntimeError("Multiple matching manifests; try specifying a variant?")

  return matches[0]


def ostree_digest(ref: str) -> Optional[str]:
  try:
    return capture_json('ostree', 'cat', ref, METADATA_FILENAME, suppress_stderr=True)['digest']
  except subprocess.CalledProcessError:
    return None


def ostree_commit(ref: str, tarball: str, metadata: dict, sign_by: str = None) -> str:
  commit_argv = [
    'ostree', 'commit', '--tar-autocreate-parents',
    f"--branch={ref}",
    f"--tree=tar={tarball}",
    f"--subject=podracer repacked {metadata['source']} at {metadata['imported']}",
    f"--add-metadata-string=com.getseam.podracer.source={metadata['source']}",
    f"--add-metadata-string=com.getseam.podracer.imported={metadata['imported']}",
    f"--add-metadata-string=com.getseam.podracer.digest={metadata['digest']}"
  ]

  if sign_by is not None:
    commit_argv.append(f"--gpg-sign={sign_by}")

  return capture_output(*commit_argv)


def repack(ref: str, image: str, arch: str, variant: str = None, sign_by: str = None) -> None:
  qualified = qualify_image(image)
  metadata = registry_manifest(qualified, arch, variant)
  with_digest = f"{qualified.rsplit(':', 1)[0]}@{metadata['digest']}"

  if ostree_digest(ref) == metadata['digest']:
    sys.stderr.write(f"NOTICE: {ref} already contains {with_digest}\n")
    print(ostree_rev_parse(ref))
    return

  capture_output(EXPORT_COMMAND, 'pull', '--quiet', with_digest)
  inspect = capture_json(EXPORT_COMMAND, 'image', 'inspect', with_digest)

  metadata["source"] = image
  metadata["qualified"] = qualified
  metadata["imported"] = datetime.datetime.now().isoformat()
  metadata["config"] = inspect[0]["Config"]

  tarball = tempfile.NamedTemporaryFile(suffix='.tar', delete=False)
  try:
    export_rootfs(with_digest, tarball, inject={METADATA_FILENAME: json.dumps(metadata, indent=2)})
    commit = ostree_commit(ref, tarball.name, metadata, sign_by)
    sys.stderr.write(f"SUCCESS: {with_digest} imported to {ref}\n")
    print(commit)
  finally:
    os.unlink(tarball.name)


def main(argv: List[str] = sys.argv[1:]) -> int:
  parser = argparse.ArgumentParser(description='Import a container into ostree from a registry')
  parser.add_argument('ref', metavar='BRANCH', help='ostree branch to commit to')
  parser.add_argument('image', metavar='IMAGE', help='image to import')
  parser.add_argument('--repo', metavar='OSTREE', help='ostree repo to import to')
  parser.add_argument('--sign-by', metavar='KEYID', help='sign commit with GPG key')
  parser.add_argument('--arch', metavar='ARCH', help='architecture to import')
  parser.add_argument('--variant', metavar='VARIANT', help='variant to import')
  args = parser.parse_args(argv)

  if args.arch is None:
    if 'PODRACER_ARCH' in os.environ and len(os.environ['PODRACER_ARCH']) > 0:
      args.arch = os.getenv('PODRACER_ARCH')
    else:
      raise RuntimeError('--arch not specified and PODRACER_ARCH not set')

  if args.variant is None:
    if 'PODRACER_VARIANT' in os.environ and len(os.environ['PODRACER_VARIANT']) > 0:
      args.variant = os.getenv('PODRACER_VARIANT')

  if args.repo is not None:
    os.environ['OSTREE_REPO'] = args.repo
  elif 'OSTREE_REPO' in os.environ:
    args.repo = os.environ['OSTREE_REPO']

  try:
    capture_output('ostree', 'refs', suppress_stderr=True)
  except subprocess.CalledProcessError:
    if args.repo is not None:
      subprocess.run(['ostree', f"--repo={args.repo}", 'init', '--mode=archive-z2'])
      sys.stderr.write(f"NOTICE: initializing ostree repo in {args.repo}\n")
    else:
      raise RuntimeError("Couldn't read ostree repo; try setting OSTREE_REPO or passing --repo.")

  repack(args.ref, args.image, args.arch, args.variant, args.sign_by)
  return 0


if __name__ == "__main__":
  sys.exit(main())
