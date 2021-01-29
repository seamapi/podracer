# podracer

podracer includes a tool to import a container from a registry into an [ostree](https://ostreedev.github.io/ostree/) repository, and wrapper around [podman](https://podman.io/) to launch a container stored in a ostree repository (or just a directory, if you only want a glorified [chroot(1)](https://man7.org/linux/man-pages/man1/chroot.1.html).)

You may want to use this if you want to use an ostree repository for container distribution instead of a registry. The benefits of doing so include:

- Instead of needing to run a container registry, ostree repositories can be served a simple static HTTP server, and work well when put behind a CDN such as Cloudflare.
- Instead of having to transfer an entire layer when only a few files have changed, ostree updates work at the level of individual files.
- ostree only stores one copy of any particular version of a file and creates hard links to it where it is needed; if multiple filesystems with an identical file are stored in the same repository, they will all reference the same copy of the file, saving disk space. Additional savings can be achieved if the host operating system is also managed by ostree, which will allow containers to share files with the host as well as with each other.

## Usage

### `podracer-export`

```text
podracer-export [-h] [-o PATH] IMAGE

Export container rootfs as tarball

positional arguments:
  IMAGE                 image to export

optional arguments:
  -h, --help            show this help message and exit
  -o PATH, --output PATH
                        where to write output; defaults to stdout
```

### `podracer-manifests`

```text
podracer-manifests [-h] [--arch ARCH] [--os OS] [--variant VARIANT] [--output yaml|json|digests] IMAGE

Inspect registry manifests

positional arguments:
  IMAGE                 image to inspect

optional arguments:
  -h, --help            show this help message and exit
  --arch ARCH           filter by architecture
  --os OS               filter by OS
  --variant VARIANT     filter by variant
  --output yaml|json|digests
                        output format; "digests" prints one digest per line
```

### `podracer-repack`

```text
podracer-repack [-h] [--repo OSTREE] [--sign-by KEYID] [--arch ARCH] [--variant VARIANT] BRANCH IMAGE

Import a container into ostree from a registry

positional arguments:
  BRANCH             ostree branch to commit to
  IMAGE              image to import

optional arguments:
  -h, --help         show this help message and exit
  --repo OSTREE      ostree repo to import to
  --sign-by KEYID    sign commit with GPG key
  --arch ARCH        architecture to import
  --variant VARIANT  variant to import
```

### `podracer-run`

```text
podracer-run [-h] [--cidfile PATH] [--cgroups enabled|disabled|no-conmon|split] [--conmon-pidfile PATH] [-d] [--entrypoint ENTRYPOINT] [-e KEY=VALUE] [--env-file FILE] [-i] [-n NAME] [--network NETWORK] [--no-ostree]
              [--replace] [--rm] [-t] [-v VOLUME]
              ROOTFS [CMD ...]

Run a container from a rootfs or an ostree commit

positional arguments:
  ROOTFS                ostree reference of rootfs, or path if --no-ostree given
  CMD                   command to run in container

optional arguments:
  -h, --help            show this help message and exit
  --cidfile PATH        write the container ID to the file
  --cgroups enabled|disabled|no-conmon|split
                        control container cgroup configuration (default "enabled")
  --conmon-pidfile PATH
                        path to the file that will receive the PID of conmon
  -d, --detach          run container in background and print container ID
  --entrypoint ENTRYPOINT
                        overwrite the default ENTRYPOINT of the image
  -e KEY=VALUE, --env KEY=VALUE
                        add or override a container environment variable
  --env-file FILE       read environment variables from a file
  -i, --interactive     keep STDIN open even if not attached
  -n NAME, --name NAME  name to assign to container
  --network NETWORK     connect the container to a network
  --no-ostree           interpret ROOTFS as a path
  --replace             if a container with the same name exists, replace it
  --rm                  remove container after exit
  -t, --tty             allocate a pseudo-TTY for container
  -v VOLUME, --volume VOLUME
                        bind mount a volume into the container
```

## Copyright

Copyright (C) 2021 Halcyon Labs

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/).
