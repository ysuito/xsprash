FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive

RUN sed -i.org -e 's|ports.ubuntu.com|jp.archive.ubuntu.com|g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
    tzdata \
    locales \
    fonts-noto-cjk \
    pulseaudio \
    fcitx-mozc \
    dbus-x11 \
    breeze \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s -f /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && dpkg-reconfigure tzdata \
    && locale-gen ja_JP.UTF-8
# If you want to use jp106 keyboard, uncomment following line.
# RUN setxkbmap -model jp106 -layout jp
# If you want to system lang to japanese, uncomment following line.
# ENV LANG ja_JP.UTF-8
