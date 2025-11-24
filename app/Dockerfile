FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

COPY requirements.txt .
RUN . /opt/venv/bin/activate && pip install -r requirements.txt

COPY . .

CMD . /opt/venv/bin/activate && exec python app.py