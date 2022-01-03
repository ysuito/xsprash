FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive

RUN sed -i.org -e 's|ports.ubuntu.com|jp.archive.ubuntu.com|g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
    pulseaudio \
    breeze \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
