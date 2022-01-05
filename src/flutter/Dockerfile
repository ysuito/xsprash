FROM vscode:latest

ENV DEBIAN_FRONTEND noninteractive

ARG studio_version=2020.3.1.25 # Android Studio Version to install
ARG flutter_version=2.5.3 # Flutter Version to install
RUN apt update && apt install -y \
    libglu1-mesa clang cmake ninja-build \
    pkg-config libgtk-3-dev \
    && curl -LO https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${flutter_version}-stable.tar.xz \
    && tar xf ./flutter_linux_${flutter_version}-stable.tar.xz \
    && curl -LO https://redirector.gvt1.com/edgedl/android/studio/ide-zips/${studio_version}/android-studio-${studio_version}-linux.tar.gz \
    && tar xf ./android-studio-${studio_version}-linux.tar.gz \
    && mv flutter /opt/ \
    && mv android-studio /opt/ \
    && ln -s /opt/android-studio/bin/studio.sh /usr/local/bin/android_studio \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN chmod 777 -R /opt/flutter/
ENV PATH /opt/flutter/bin:$PATH
ENV CHROME_EXECUTABLE /usr/bin/google-chrome
CMD ["code", "--verbose", "--no-sandbox", "--user-data-dir=/root/.config/Code"]
