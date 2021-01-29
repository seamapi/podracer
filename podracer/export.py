import argparse
import codecs
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

from io import BytesIO, IOBase
from pathlib import Path

if os.getenv('PODRACER_EXPORT_COMMAND') is not None:
  EXPORT_COMMAND = os.getenv('PODRACER_EXPORT_COMMAND')
elif shutil.which('podman') is not None:
  EXPORT_COMMAND = 'podman'
elif shutil.which('docker') is not None:
  EXPORT_COMMAND = 'docker'
else:
  raise RuntimeError("Couldn't find podman or docker; try setting PODRACER_EXPORT_COMMAND to the path of podman or docker")


class Archive:
  def __init__(self, buffer: IOBase):
    self.buffer = buffer
    self.archive = tarfile.open(mode='r', fileobj=self.buffer)


  def __del__(self):
    self.archive.close()
    self.buffer.close()


class Layer(Archive):
  def __init__(self, archive: tarfile.TarFile, name: str):
    super().__init__(archive.extractfile(name))

    self.name = name
    self.files = set()
    self.mask = set()

    for member in self.archive.getmembers():
      path = Path(member.name)
      if not path.name.startswith('.wh.'):
        self.files.add(member.name)
        continue

      if len(path.parent.name) > 0:
        prefix = str(path.parent) + '/'
      else:
        prefix = ''

      if path.name == '.wh..wh..opq':
        # Discard everything in the same directory
        self.mask.add(prefix)
      else:
        # Just discard one file
        self.mask.add(prefix + path.name[4:])


class Image(Archive):
  def __init__(self, name: str):
    buffer = tempfile.TemporaryFile()
    try:
      subprocess.run([EXPORT_COMMAND, 'save', name], check=True, stdout=buffer, stderr=subprocess.PIPE)
    except:
      buffer.close()
      raise

    buffer.seek(0)
    super().__init__(buffer)

    manifest = json.load(self.archive.extractfile("manifest.json"))
    if len(manifest) != 1:
      raise RuntimeError(f"Expected exactly 1 image in manifest, got {len(manifest)}")

    self.layers = list(map(lambda name: Layer(self.archive, name), manifest[0]["Layers"]))


def parent_paths(filename: str) -> list[str]:
  path = Path(filename)
  while len(path.parent.name) > 0:
    yield str(path.parent) + '/'
    path = path.parent


def is_parent_masked(filename: str, mask: set) -> bool:
  for parent in parent_paths(filename):
    if parent in mask:
      return True
  return False


def make_buffer(content: str) -> BytesIO:
  buffer = BytesIO()
  codecs.getwriter('utf-8')(buffer).write(content)
  buffer.seek(0)
  return buffer


def export_rootfs(image_name: str, output: IOBase, inject: dict[str] = {}) -> None:
  image = Image(image_name)
  mask = set()
  files = {}

  # Build the list of files
  for layer in reversed(image.layers):
    for filename in layer.files:
      if filename in mask:
        continue
      elif filename in files:
        raise RuntimeError(f"{filename} from {layer.name} conflicts with {files[filename].name}")
      elif is_parent_masked(filename, mask):
        continue

      # Take this file from this layer
      files[filename] = layer

    # Grow the mask
    mask.update(layer.mask)
    mask.update(layer.files)

  # Write the exported rootfs
  with tarfile.open(mode='w', fileobj=output) as tarball:
    for filename in sorted(list(files.keys()) + list(inject.keys())):
      if filename in inject:
        # Synthesize the file
        buffer = make_buffer(inject[filename])
        member = tarfile.TarInfo(filename)
        member.size = len(buffer.getvalue())
        tarball.addfile(member, buffer)
      else:
        # Copy the file from its layer
        layer = files[filename]
        member = layer.archive.getmember(filename)
        if member.size > 0:
          tarball.addfile(member, layer.archive.extractfile(filename))
        else:
          tarball.addfile(member)

    tarball.close()
    output.close()


def main(argv: list[str] = sys.argv[1:]) -> int:
  parser = argparse.ArgumentParser(description='Export container rootfs as tarball')
  parser.add_argument('image', metavar='IMAGE', help='image to export')
  parser.add_argument('-o', '--output', metavar='PATH', help='where to write output; defaults to stdout')
  args = parser.parse_args(argv)

  if args.output is None:
    if sys.stdout.isatty():
      raise RuntimeError("Cowardly refusing to write an archive to a terminal; try using -o or redirecting the output")
    output = sys.stdout.buffer
  else:
    output = open(args.output, 'wb')

  export_rootfs(args.image, output)
  return 0


if __name__ == "__main__":
  sys.exit(main())
