FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    fritzing \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD [ "fritzing" ]
