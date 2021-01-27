# podracer

podracer is a wrapper around [podman](https://podman.io/) to launch a container stored in an [ostree](https://ostreedev.github.io/ostree/) repository.

## Usage

```text
podracer-run [-h] [-n NAME] [-e KEY=VALUE] [--env-file FILE] [-v VOLUME]
              OSTREE_REF [CMD [CMD ...]]

Run a container from an ostree commit

positional arguments:
  OSTREE_REF            ostree commit for container
  CMD                   command to run in container

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  name to assign to container
  -e KEY=VALUE, --env KEY=VALUE
                        add or override a container environment variable
  --env-file FILE       read environment variables from a file
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
