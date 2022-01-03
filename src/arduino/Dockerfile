FROM vscode:latest

ENV DEBIAN_FRONTEND noninteractive

ARG arduino_version=1.8.16 # Install Arduino Version
RUN curl -LO https://downloads.arduino.cc/arduino-${arduino_version}-linux64.tar.xz \
    && tar xvf arduino-${arduino_version}-linux64.tar.xz \
    && mv arduino-${arduino_version} /opt/ \
    && cd /opt/arduino-${arduino_version}/ \
    && ./install.sh
CMD ["code", "--verbose", "--no-sandbox", "--user-data-dir=/root/.config/Code"]
