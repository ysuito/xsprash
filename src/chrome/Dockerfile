FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt install -y curl gpg apt-transport-https wget && \
    sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    apt update && apt install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
CMD ["google-chrome", "--no-sandbox"]
