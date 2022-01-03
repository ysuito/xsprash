FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    ubuntu-restricted-extras \
    ffmpeg \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    libpci-dev \
    firefox \
    firefox-geckodriver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
CMD ["firefox"]
