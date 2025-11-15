FROM python:3.13.5-slim
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv venv \
    && ./venv/bin/pip install --upgrade pip \
    && ./venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["./venv/bin/python", "app.py"]