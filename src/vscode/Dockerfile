FROM ubuntubase:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt install -y \
    curl gpg apt-transport-https \
    ca-certificates lsb-release \
    git zip unzip wget \
    && sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
    && echo "deb [arch=$(dpkg --print-architecture)] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list \
    && apt update && apt install -y \
    docker-ce docker-ce-cli containerd.io \
    code google-chrome-stable \
    && apt-get clean \
    && rm microsoft.gpg \
    && rm -rf /var/lib/apt/lists/*

CMD ["code", "--verbose", "--no-sandbox", "--user-data-dir=.config/Code"]
