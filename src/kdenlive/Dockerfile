FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    kdenlive \
    vlc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD [ "kdenlive" ]
