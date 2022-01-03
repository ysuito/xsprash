FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    gnumeric \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD [ "gnumeric" ]
