FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    inkscape \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD [ "inkscape" ]
