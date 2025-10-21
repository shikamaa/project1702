FROM python:3.13.5

WORKDIR /app

COPY requirements.txt .

RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get update -o Acquire::CompressionTypes::Order::=gz \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) \
        signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*


RUN python3 -m venv venv \
    && ./venv/bin/pip install --upgrade pip \
    && ./venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["./venv/bin/python", "app.py"]

