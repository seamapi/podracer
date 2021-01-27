import argparse
import datetime
import json
import os
import subprocess
import sys
import tarfile
import tempfile

from pathlib import Path
from podracer.container import RUNTIME
from podracer.ostree import ostree_rev_parse
from podracer.capture import capture_output, capture_json


def registry_manifest(image, arch, variant=None):
  manifests = capture_json(RUNTIME, 'manifest', 'inspect', image)

  def match_manifest(manifest):
    if manifest["platform"]["os"] != "linux":
      return False
    elif manifest["platform"]["architecture"] != arch:
      return False

    if variant is not None:
      if not "variant" in manifest["platform"]:
        return False
      elif manifest["platform"]["variant"] != variant:
        return False

    return True

  matches = list(filter(match_manifest, manifests["manifests"]))

  if len(matches) < 1:
    raise RuntimeError("No matching manifests; are your architecture and variant correct?")
  elif len(matches) > 1:
    raise RuntimeError("Multiple matching manifests; try specifying a variant?")

  return matches[0]


def ostree_digest(ref):
  try:
    return capture_json('ostree', 'cat', ref, '.podracer.json')['digest']
  except subprocess.CalledProcessError:
    return None


def create_tarball(image, metadata):
  # Create a tarball to import into ostree
  tarball = tempfile.NamedTemporaryFile(suffix='.tar', delete=False)
  tree = tarfile.open(None, 'w', tarball)

  try:
    # Save the image and open the archive
    archivefile = tempfile.TemporaryFile()
    subprocess.run([RUNTIME, 'save', image], check=True, stdout=archivefile)
    archivefile.seek(0)
    archive = tarfile.open(None, 'r', archivefile)

    # Extract and parse the manifest
    manifest = json.load(archive.extractfile("manifest.json"))
    if len(manifest) != 1:
      raise RuntimeError(f"Expected exactly 1 image in manifest, got {len(manifest)}")

    # For each layer in the manifest
    for name in manifest[0]["Layers"]:
      layer = tarfile.open(None, 'r', archive.extractfile(name))
      # Copy each file in the layer into the tree
      for member in layer.getmembers():
        if member.size > 0:
          tree.addfile(member, layer.extractfile(member))
        else:
          tree.addfile(member)

    # Write the metadata
    with tempfile.TemporaryFile(mode='w+') as tmp:
      json.dump(metadata, tmp, indent=2)
      tmp.seek(0)

      info = tarfile.TarInfo('.podracer.json')
      info.size = os.stat(tmp.fileno()).st_size
      tree.addfile(info, tmp.buffer)

    # Finish writing the archive
    tree.close()
    tarball.close()
  except:
    os.unlink(tarball.name)
    raise

  return tarball


def ostree_commit(ref, tarball, metadata, sign_by=None):
  commit_argv = [
    'ostree', 'commit', '--tar-autocreate-parents',
    f"--branch={ref}",
    f"--tree=tar={tarball.name}",
    f"--subject=podracer repacked {metadata['source']} at {metadata['imported']}",
    f"--add-metadata-string=source={metadata['source']}",
    f"--add-metadata-string=imported={metadata['imported']}",
    f"--add-metadata-string=digest={metadata['digest']}"
  ]

  if sign_by is not None:
    commit_argv.append(f"--gpg-sign={sign_by}")

  return capture_output(*commit_argv)


def repack(ref, image, arch, variant=None, sign_by=None):
  metadata = registry_manifest(image, arch, variant)
  with_digest = f"{image.rsplit(':', 1)[0]}@{metadata['digest']}"


  if ostree_digest(ref) == metadata['digest']:
    sys.stderr.write(f"{ref} already contains {with_digest}\n")
    print(ostree_rev_parse(ref))
    return 0

  subprocess.run([RUNTIME, 'pull', '--quiet', with_digest], check=True)
  inspect = capture_json(RUNTIME, 'image', 'inspect', with_digest)

  metadata["source"] = image
  metadata["imported"] = datetime.datetime.now().isoformat()
  metadata["config"] = inspect[0]["Config"]

  tarball = create_tarball(with_digest, metadata)

  try:
    commit = ostree_commit(ref, tarball, metadata, sign_by)
    sys.stderr.write(f"{with_digest} imported to {ref}\n")
    print(commit)
  finally:
    os.unlink(tarball.name)


def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser(description='Import a container into ostree from a registry')
  parser.add_argument('ref', metavar='BRANCH', help='ostree branch to commit to')
  parser.add_argument('image', metavar='IMAGE', help='image to import')
  parser.add_argument('--arch', metavar='ARCH', help='architecture to import')
  parser.add_argument('--variant', metavar='VARIANT', help='variant to import')
  parser.add_argument('--sign-by', metavar='KEYID', help='sign commit with GPG key')
  args = parser.parse_args(argv)

  if args.arch is None:
    args.arch = os.getenv('PODRACER_ARCH')

  if args.arch is None:
    raise RuntimeError('--arch not specified and PODRACER_ARCH not set')

  if args.variant is None:
    args.variant = os.getenv('PODRACER_VARIANT')

  repack(args.ref, args.image, args.arch, args.variant, args.sign_by)


if __name__ == "__main__":
  sys.exit(main())
