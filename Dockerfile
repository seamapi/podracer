FROM python:3.8-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      apt-transport-https ca-certificates curl gnupg ostree && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian buster stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli

RUN mkdir -p /sysroot/ostree && \
    ln -sf /sysroot/ostree /ostree && \
    ostree init --repo=/sysroot/ostree/repo --mode=bare

COPY podracer/ /usr/src/podracer/podracer/
COPY setup.py /usr/src/podracer/setup.py
COPY setup.cfg /usr/src/podracer/setup.cfg

WORKDIR /usr/src/podracer
RUN python3 setup.py install
