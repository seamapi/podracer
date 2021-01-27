FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      apt-transport-https ca-certificates curl gnupg ostree python3 python3-setuptools

RUN echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_20.04/ /" > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list && \
    curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_20.04/Release.key | apt-key add - && \
    apt-get update && \
    apt-get install -y --no-install-recommends podman

COPY containers.conf /etc/containers/containers.conf

RUN mkdir -p /sysroot/ostree && \
    ln -sf /sysroot/ostree /ostree && \
    ostree init --repo=/sysroot/ostree/repo --mode=bare

COPY podracer/ /usr/src/podracer/podracer/
COPY setup.py /usr/src/podracer/setup.py
COPY setup.cfg /usr/src/podracer/setup.cfg

WORKDIR /usr/src/podracer
RUN python3 setup.py install
