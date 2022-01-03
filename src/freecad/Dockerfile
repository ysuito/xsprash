FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y software-properties-common &&\
    add-apt-repository ppa:freecad-maintainers/freecad-stable && \
    apt-get update && apt-get install -y freecad \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
CMD [ "freecad" ]
