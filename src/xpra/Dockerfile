FROM ubuntubase

ENV DEBIAN_FRONTEND noninteractive

VOLUME /tmp/.X11-unix

RUN apt update && apt install -y \
   wget gnupg xvfb x11-xserver-utils \
   python3-pip pulseaudio \
   && pip3 install pyinotify \
   && echo "deb [arch=$(dpkg --print-architecture)] https://xpra.org/ focal main" > /etc/apt/sources.list.d/xpra.list \
   && wget -q https://xpra.org/gpg.asc -O- | apt-key add - \
   && apt update && apt install -y xpra \
   && apt-get clean \
   && rm -rf /var/lib/apt/lists/*

ENV XPRA_PORT=10000 XPRA_DISPLAY=80

COPY entrypoint.sh /tmp/entrypoint.sh
RUN ["chmod", "+x", "/tmp/entrypoint.sh"]
ENTRYPOINT ["/tmp/entrypoint.sh"]
CMD ["client"]
